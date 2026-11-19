import math
import os
import random
import threading
import uuid

import gevent
import requests
from locust import HttpUser, LoadTestShape, between, events, task


def _f(name, default):
    return float(os.getenv(name, default))


def _i(name, default):
    return int(os.getenv(name, default))


def _wait(prefix, dmin, dmax):
    return between(_f(prefix + "_WAIT_MIN", dmin), _f(prefix + "_WAIT_MAX", dmax))


DEFAULT_HOST = "http://192.168.100.3:5080"
LOGIN_PATH = os.getenv("HOTEL_LOGIN_PATH", "/api/login")
RUN_ID = os.getenv("HOTEL_RUN_ID") or uuid.uuid4().hex[:6]
INCLUIR_SERVICIOS = os.getenv("HOTEL_LECTURA_SERVICIOS", "1") != "0"
WRITE_USUARIOS = os.getenv("HOTEL_WRITE_USUARIOS", "0") == "1"
TEST_PASSWORD = os.getenv("HOTEL_TEST_PASSWORD")  # nunca se escribe en el código
TIMEOUT_LIGERO = 60
TIMEOUT_PESADO = 120  # igual al "timeout server" de HAProxy

TOKEN = None  # JWT compartido; se obtiene una sola vez al iniciar la prueba (si hay credenciales)


class _Contador:
    """Cuenta registros creados y respeta el tope global (todos los usuarios comparten el proceso)."""

    def __init__(self, limite):
        self.limite, self.n, self.omitidos = limite, 0, 0
        self._lock = threading.Lock()

    def tomar(self):
        with self._lock:
            if self.n >= self.limite:
                self.omitidos += 1
                return None
            self.n += 1
            return self.n


ESCRITURAS = _Contador(_i("HOTEL_MAX_WRITES", 2000))


def _motivo(resp):
    """Texto del fallo: excepción de red (RemoteDisconnected, ConnectionReset...) o código HTTP."""
    err = getattr(resp, "error", None)
    if err is not None:
        return type(err).__name__
    return f"HTTP {resp.status_code}"


def _get(user, path, timeout, min_bytes=2):
    with user.client.get(path, name=f"GET {path}", timeout=timeout, catch_response=True) as r:
        if r.status_code != 200:
            r.failure(_motivo(r))
        elif len(r.content) < min_bytes:
            r.failure("cuerpo vacío")
        else:
            r.success()


def _post(user, path, body, name, ok=(200, 201)):
    headers = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}
    with user.client.post(path, json=body, headers=headers, name=name, timeout=TIMEOUT_LIGERO,
                          catch_response=True) as r:
        if r.status_code in ok:
            r.success()
        else:
            r.failure(_motivo(r))



class LecturaLigera(HttpUser):
    """Lecturas ligeras. Pesos 3:2 entre habitaciones y servicios (o solo habitaciones)."""
    host = os.getenv("HOTEL_HOST", DEFAULT_HOST)
    wait_time = _wait("HOTEL_LIGERA", 0.5, 1.0)

    def habitaciones(self):
        _get(self, "/api/habitaciones", TIMEOUT_LIGERO)

    def servicios(self):
        _get(self, "/api/servicios", TIMEOUT_LIGERO)

    tasks = {habitaciones: 3, servicios: 2} if INCLUIR_SERVICIOS else {habitaciones: 1}


class AnaliticaPesada(HttpUser):
    """46,094 filas en un solo JSON (~4 MB) sin paginar. Úsese con POCOS usuarios."""
    host = os.getenv("HOTEL_HOST", DEFAULT_HOST)
    wait_time = _wait("HOTEL_PESADA", 1, 2)

    @task
    def trafico_logs(self):
        _get(self, "/api/analytics/trafico-logs", TIMEOUT_PESADO, min_bytes=1000)


class AnaliticaLigera(HttpUser):
    """Control: mismo microservicio de analítica, pero respuestas pequeñas (20 y 109 filas)."""
    host = os.getenv("HOTEL_HOST", DEFAULT_HOST)
    wait_time = _wait("HOTEL", 1, 2)

    @task
    def sentimiento(self):
        _get(self, "/api/analytics/sentimiento-resenas", TIMEOUT_LIGERO)

    @task
    def ocupacion(self):
        _get(self, "/api/analytics/ocupacion-mensual", TIMEOUT_LIGERO)


class Escritura(HttpUser):
    """
    Escrituras controladas. Cada registro lleva la marca LOCUST-<RUN_ID> para poder borrarlo.
    No crea reservas ni pagos (dependen de disponibilidad e integridad del negocio).
    """
    host = os.getenv("HOTEL_HOST", DEFAULT_HOST)
    wait_time = _wait("HOTEL", 1, 2)
    fixed_count = _i("HOTEL_WRITERS", 0)  # si es > 0, se crean exactamente N escritores

    @task(4)
    def crear_servicio(self):
        n = ESCRITURAS.tomar()
        if n is None:
            gevent.sleep(1)  # tope alcanzado: no se escribe más
            return
        body = {
            "nombre": f"LOCUST-{RUN_ID}-{n:06d}",
            "descripcion": "Servicio generado para pruebas de carga",
            "precio": random.choice([20000, 35000, 50000, 80000, 120000]),
            "estado": "Disponible",
        }
        _post(self, "/api/servicios", body, "POST /api/servicios")

    if WRITE_USUARIOS and TEST_PASSWORD:
        @task(1)
        def registrar_usuario(self):
            n = ESCRITURAS.tomar()
            if n is None:
                gevent.sleep(1)
                return
            documento = f"LC{RUN_ID}{n:08d}"  # <= 20 caracteres (varchar(20))
            body = {
                "documento": documento,
                "nombreCompleto": "Usuario Prueba Locust",
                "email": f"{documento.lower()}@example.test",
                "telefono": "3000000000",
                "password": TEST_PASSWORD,
            }
            _post(self, "/api/usuarios", body, "POST /api/usuarios")


if os.getenv("HOTEL_SHAPE", "").lower() == "step":

    class StepShape(LoadTestShape):
        """+STEP_USERS usuarios cada STEP_TIME segundos hasta MAX_USERS; el último escalón dura STEP_TIME."""
        step_users = _i("HOTEL_STEP_USERS", 10)
        step_time = _i("HOTEL_STEP_TIME", 60)
        max_users = _i("HOTEL_MAX_USERS", 100)
        spawn_rate = _f("HOTEL_STEP_SPAWN", 5)

        def tick(self):
            total_steps = math.ceil(self.max_users / self.step_users)
            t = self.get_run_time()
            if t >= total_steps * self.step_time:
                return None
            escalon = int(t // self.step_time)
            return min((escalon + 1) * self.step_users, self.max_users), self.spawn_rate


@events.test_start.add_listener
def _al_iniciar(environment, **kwargs):
    global TOKEN
    host = environment.host or os.getenv("HOTEL_HOST", DEFAULT_HOST)  # --host de la CLI tiene prioridad
    print(f"[hotel] RUN_ID={RUN_ID} host={host} servicios_en_lectura={INCLUIR_SERVICIOS}")
    doc, pwd = os.getenv("HOTEL_LOGIN_DOCUMENTO"), os.getenv("HOTEL_LOGIN_PASSWORD")
    if not (doc and pwd):
        print("[hotel] Sin credenciales de login: los POST se enviarán SIN token.")
        return
    try:
        r = requests.post(host + LOGIN_PATH, json={"documento": doc, "password": pwd}, timeout=30)
        data = r.json() if r.ok else {}
        inner = data.get("data") if isinstance(data.get("data"), dict) else {}
        TOKEN = data.get("token") or data.get("accessToken") or data.get("jwt") or inner.get("token")
        print(f"[hotel] Login {LOGIN_PATH}: HTTP {r.status_code}, token {'obtenido' if TOKEN else 'NO encontrado'}")
    except Exception as exc:  # noqa: BLE001
        print(f"[hotel] Login falló: {type(exc).__name__}")


@events.test_stop.add_listener
def _al_terminar(environment, **kwargs):
    if ESCRITURAS.n or ESCRITURAS.omitidos:
        print(f"[hotel] Intentos de creación: {ESCRITURAS.n} (omitidos por el tope: {ESCRITURAS.omitidos})")
        print("[hotel] LIMPIEZA en MySQL:")
        print("   DELETE FROM bd_servicios.servicio WHERE nombre LIKE 'LOCUST-%';")
        print("   DELETE FROM bd_usuarios.usuario  WHERE documento LIKE 'LC%' AND email LIKE '%@example.test';")
