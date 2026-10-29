#!/usr/bin/env python3
"""
Generador de dataset masivo para Hotel Leyton (fase Big Data / Spark).

Genera CSV (UTF-8) que CONTINUAN tu dump actual (IDs, catalogos y reglas de
negocio coherentes):

  usuarios.csv, habitaciones.csv, reservas.csv, reserva_servicio.csv,
  pagos.csv, resenas.csv, logs.csv

Uso:
  python3 generar_dataset_hotel.py                     # escala completa
  python3 generar_dataset_hotel.py --escala 0.02       # prueba rapida
  python3 generar_dataset_hotel.py --semilla 7 --salida ./csv
  python3 generar_dataset_hotel.py --anio-inicio 2015 --logs-ruido 5000000

Solo usa la libreria estandar de Python 3.8+.
NULL se escribe como \\N (compatible con MySQL LOAD DATA y Spark nullValue).
"""
import argparse
import csv
import math
import os
import random
import unicodedata
from collections import Counter
from datetime import date, datetime, time, timedelta

# --------------------------------------------------------------------------
# Constantes que salen de tu dump (generado el 2026-10-27 02:16:41)
# --------------------------------------------------------------------------
HOY = date(2026, 10, 27)
AHORA = datetime(2026, 10, 27, 2, 16, 41)
FIN_RESERVAS = date(2027, 1, 31)     # reservas futuras hasta aqui

# Mismo hash bcrypt de tus usuarios 1 y 2 -> todos se loguean con esa clave
HASH_PASSWORD = "$2b$10$yuT4cuPXJC3iAOcGn8htW.wmwBlRqn2kpx5RyGIzn2s3xqhDJOyIa"

ID_USUARIO0, ID_RESERVA0, ID_PAGO0, ID_HAB0 = 5, 138, 20, 21
DOCUMENTOS_EXISTENTES = {"100101", "1080050144", "1231", "12365"}
CLIENTES_EXISTENTES = [2, 3, 4]

HABITACIONES_BASE = [
    (1, "101", "Sencilla", 2, 120000, "Vista al jardín interno bonito, cama individual"),
    (2, "102", "Sencilla", 1, 120000, "Vista a la calle principal, escritorio de trabajo"),
    (3, "103", "Sencilla", 1, 120000, "Habitación estándar cama individual"),
    (4, "104", "Sencilla", 1, 120000, "Cama individual, TV por cable"),
    (5, "105", "Sencilla", 1, 120000, "En reparación de aire acondicionado"),
    (6, "201", "Doble", 2, 220000, "Dos camas individuales, balcón privado"),
    (7, "202", "Doble", 2, 220000, "Cama King size, baño privado amplio"),
    (8, "203", "Doble", 2, 220000, "Dos camas semi-dobles"),
    (9, "204", "Doble", 2, 220000, "Cama matrimonial, vista a la piscina"),
    (10, "205", "Doble", 2, 220000, "Vista a la ciudad, escritorio doble"),
    (11, "206", "Doble", 2, 220000, "Dos camas individuales, frigobar"),
    (12, "207", "Doble", 2, 220000, "Pintura y mantenimiento general"),
    (13, "301", "Suite", 4, 450000, "Suite familiar con 2 habitaciones separadas y sala"),
    (14, "302", "Suite", 4, 450000, "Suite nupcial con Jacuzzi y balcón"),
    (15, "303", "Suite", 4, 450000, "Suite ejecutiva con sala de reuniones y minibar"),
    (16, "304", "Suite", 4, 450000, "Vista panorámica, 2 camas Queen size"),
    (17, "305", "Suite", 4, 450000, "Suite de lujo con terraza privada"),
    (18, "401", "Penthouse", 8, 700000, "Piso completo, Jacuzzi, terraza y cocina equipada"),
    (19, "402", "Penthouse", 8, 700000, "Penthouse con vista 360, zona de BBQ y bar"),
    (20, "403", "Penthouse", 8, 700000, "Penthouse VIP con acceso a elevador privado"),
]
PRECIO_TIPO = {"Sencilla": 120000, "Doble": 220000, "Suite": 450000, "Penthouse": 700000}
DESCS = {
    "Sencilla": ["Cama individual, TV por cable", "Vista a la calle, escritorio de trabajo",
                 "Habitación estándar con baño privado", "Vista al jardín interno, cama individual"],
    "Doble": ["Dos camas individuales, balcón privado", "Cama King size, baño privado amplio",
              "Cama matrimonial, vista a la piscina", "Vista a la ciudad, escritorio doble",
              "Dos camas semi-dobles, frigobar"],
    "Suite": ["Suite familiar con 2 habitaciones y sala", "Suite nupcial con Jacuzzi y balcón",
              "Suite ejecutiva con sala de reuniones y minibar", "Vista panorámica, 2 camas Queen size",
              "Suite de lujo con terraza privada"],
    "Penthouse": ["Piso completo, Jacuzzi, terraza y cocina equipada",
                  "Penthouse con vista 360, zona de BBQ y bar",
                  "Penthouse VIP con acceso a elevador privado"],
}
SERVICIOS = {1: ("Spa", 120000), 2: ("Desayuno", 35000), 3: ("Transporte", 80000)}

# Reservas NO canceladas que ya existen (para no solapar): hab -> [(entrada, salida)]
D = date
BLOQUEOS = {
    1: [(D(2026, 11, 1), D(2026, 11, 5)), (D(2026, 2, 12), D(2026, 2, 13)), (D(2026, 2, 14), D(2026, 2, 15)),
        (D(2026, 2, 22), D(2026, 2, 23)), (D(2026, 2, 25), D(2026, 2, 26)), (D(2026, 2, 26), D(2026, 2, 27)),
        (D(2026, 9, 30), D(2026, 10, 1)), (D(2026, 9, 17), D(2026, 9, 18)), (D(2026, 10, 7), D(2026, 10, 8))],
    2: [(D(2026, 10, 5), D(2026, 10, 6)), (D(2026, 10, 18), D(2026, 10, 19))],
    3: [(D(2026, 10, 1), D(2026, 10, 2))],
    6: [(D(2026, 11, 9), D(2026, 11, 11))],
}

# Inflacion de tarifas por año (precioTotal historico != precio actual)
FACTOR_PRECIO = {2017: 0.62, 2018: 0.66, 2019: 0.69, 2020: 0.72, 2021: 0.76, 2022: 0.80, 2023: 0.87, 2024: 0.93, 2025: 0.97, 2026: 1.0, 2027: 1.04}

NOCHES, NOCHES_W = [1, 2, 3, 4, 5, 7], [30, 30, 20, 10, 5, 5]
METODOS, METODOS_W = ["Tarjeta", "Efectivo", "Transferencia"], [50, 25, 25]

NOMBRES = ["Santiago", "Carlos", "Javier", "Johan", "Andrés", "Juan", "Camilo", "Felipe", "Sebastián", "Daniel",
           "Mateo", "Nicolás", "Diego", "Alejandro", "Julián", "David", "Esteban", "Miguel", "Luis", "Jorge",
           "María", "Camila", "Valentina", "Daniela", "Laura", "Sofía", "Paula", "Natalia", "Juliana", "Andrea",
           "Carolina", "Isabella", "Mariana", "Luisa", "Catalina", "Sara", "Manuela", "Lina", "Diana", "Angélica"]
APELLIDOS = ["Mendoza", "Eraso", "Bedoya", "Vivas", "Ortega", "Gómez", "Rodríguez", "Martínez", "López", "García",
             "Hernández", "Díaz", "Pérez", "Sánchez", "Ramírez", "Torres", "Flórez", "Castro", "Vargas", "Rojas",
             "Moreno", "Jiménez", "Álvarez", "Romero", "Gutiérrez", "Ruiz", "Cárdenas", "Ospina", "Quintero", "Muñoz",
             "Cruz", "Salazar", "Valencia", "Arias", "Montoya", "Zapata", "Henao", "Restrepo", "Giraldo", "Londoño"]
DOMINIOS = ["gmail.com", "hotmail.com", "outlook.com", "yahoo.com", "correo.com"]
USER_AGENTS = ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0", "Mozilla/5.0 (Macintosh; Intel Mac OS X) Safari/605.1",
               "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4) Safari/604.1", "Mozilla/5.0 (Linux; Android 14) Chrome/124.0 Mobile",
               "Mozilla/5.0 (Windows NT 10.0) Firefox/125.0", "Mozilla/5.0 (Windows NT 10.0) Edg/124.0"]
HW = [1, 1, 1, 1, 1, 2, 3, 5, 7, 8, 9, 9, 8, 8, 8, 9, 10, 11, 12, 12, 11, 8, 4, 2]  # peso por hora

# ------------------------------ RESEÑAS -----------------------------------
ASPECTOS = {
    "limpieza": (["La habitación estaba impecable y muy limpia.", "Todo estaba muy limpio y ordenado.",
                  "La limpieza fue excelente durante toda la estadía."],
                 ["Encontramos la habitación con polvo y las toallas sin cambiar.", "La limpieza dejó mucho que desear.",
                  "El baño no estaba bien limpio al llegar."]),
    "personal": (["El personal fue amable y atento en todo momento.", "La atención de recepción fue excelente.",
                  "El equipo siempre estuvo dispuesto a ayudarnos."],
                 ["La atención en recepción fue lenta y poco amable.", "El personal tardó mucho en resolver un problema simple.",
                  "Nadie respondió cuando pedimos ayuda."]),
    "ubicacion": (["La ubicación es muy cómoda y cerca de todo.", "Está bien ubicado, con restaurantes y comercio cerca."],
                  ["La ubicación no es la mejor, toca moverse en taxi.", "La zona es algo ruidosa por la noche."]),
    "cama": (["La cama era comodísima y dormimos de maravilla.", "El colchón y las almohadas son de muy buena calidad."],
             ["La cama estaba incómoda y el colchón muy viejo.", "No pudimos dormir bien por el colchón."]),
    "ruido": (["Muy tranquilo, se descansa perfecto."],
              ["Había mucho ruido y fue difícil descansar.", "Se escuchaba todo de las habitaciones vecinas."]),
    "wifi": (["El wifi funcionó rápido, ideal para trabajar."], ["El wifi era lento y se caía constantemente."]),
    "aire": (["El aire acondicionado funciona muy bien."],
             ["El aire acondicionado no enfriaba bien.", "El aire acondicionado hacía un ruido molesto."]),
    "bano": (["El baño es amplio y con buena presión de agua."],
             ["El agua caliente tardaba mucho y la presión era baja."]),
    "precio": (["Buena relación calidad-precio.", "El precio es justo por lo que ofrece."],
               ["Me pareció caro para lo que ofrece.", "No vale lo que cobran por noche."]),
    "jacuzzi": (["El jacuzzi fue lo mejor, súper relajante."], ["El jacuzzi estaba sucio y no calentaba bien."]),
    "piscina": (["La vista a la piscina es hermosa."], ["La zona de la piscina estaba muy concurrida y ruidosa."]),
    "balcon": (["El balcón es lo máximo para tomar un café en la mañana."], ["El balcón estaba descuidado."]),
    "bbq": (["La zona de BBQ es perfecta para reunirse en familia."], ["La zona de BBQ no tenía los implementos completos."]),
    "vista": (["La vista es espectacular."], ["La vista no era como en las fotos."]),
    "spa": (["El spa fue una experiencia increíble, los masajes muy buenos."],
            ["El spa estuvo desorganizado y esperamos mucho para los masajes."]),
    "desayuno": (["El desayuno buffet fue variado y delicioso."], ["El desayuno era escaso y se acababa temprano."]),
    "transporte": (["El traslado al aeropuerto fue puntual y cómodo."], ["El transporte al aeropuerto llegó tarde."]),
    "mantenimiento": ([], ["Había obras de mantenimiento y olía a pintura."]),
}
BASE = ["limpieza", "personal", "ubicacion", "cama", "ruido", "wifi", "aire", "bano", "precio"]
EXTRAS_DESC = [("jacuzzi", "jacuzzi"), ("piscina", "piscina"), ("balc", "balcon"), ("terraza", "balcon"),
               ("bbq", "bbq"), ("vista", "vista")]
EXTRAS_SERV = {1: "spa", 2: "desayuno", 3: "transporte"}
FORZADOS = {5: "aire", 12: "mantenimiento"}   # habitaciones "en reparacion" del dump
MEDIA_TIPO = {"Sencilla": 3.8, "Doble": 4.1, "Suite": 4.4, "Penthouse": 4.6}
P_POS = {5: 1.0, 4: 0.8, 3: 0.5, 2: 0.2, 1: 0.0}
ABRE = {"pos": ["Excelente experiencia.", "Todo salió perfecto.", "Volveremos sin duda.", "Superó nuestras expectativas."],
        "neu": ["Estuvo bien, aunque con detalles por mejorar.", "Experiencia aceptable.", "Cumple, pero sin sorpresas."],
        "neg": ["Muy decepcionante.", "No lo recomiendo.", "Esperaba mucho más.", "Mala experiencia."]}
CIERRA = {5: ["Totalmente recomendado.", "Lo recomiendo a todos."], 4: ["Lo recomiendo."],
          3: ["Podrían mejorar algunos detalles."], 2: ["Espero que mejoren."], 1: ["No volvería.", "Pésima experiencia en general."]}
TITULOS = {5: ["Inmejorable", "Una estadía perfecta", "Superó las expectativas", "Totalmente recomendado"],
           4: ["Muy buena estadía", "Recomendado", "Buena experiencia"],
           3: ["Cumple sin más", "Aceptable", "Regular"],
           2: ["Podría ser mejor", "Poco satisfecho", "Decepcionante"],
           1: ["Pésima experiencia", "No volvería", "Muy malo"]}

# ------------------------------ RUIDO DE LOGS -----------------------------
RUIDO = [  # peso, servicio, metodo, endpoint, status, mensaje
    (0.28, "habitaciones", "GET", "/api/habitaciones", 200, "Listado de habitaciones"),
    (0.12, "habitaciones", "GET", "/api/habitaciones/{h}", 200, "Detalle de habitación"),
    (0.12, "servicios", "GET", "/api/servicios", 200, "Listado de servicios"),
    (0.16, "usuarios", "POST", "/api/auth/login", 200, "Login exitoso"),
    (0.05, "usuarios", "POST", "/api/auth/login", 401, "Credenciales inválidas"),
    (0.10, "reservas", "GET", "/api/reservas/usuario/{u}", 200, "Consulta de reservas del usuario"),
    (0.08, "resenas", "GET", "/api/resenas/habitacion/{h}", 200, "Consulta de reseñas"),
    (0.04, "pagos", "GET", "/api/pagos/reserva/{r}", 200, "Consulta de pagos de la reserva"),
    (0.02, "reservas", "GET", "/api/reservas/{r}", 404, "Reserva no encontrada"),
    (0.015, "reservas", "POST", "/api/reservas", 500, "Error interno del servidor"),
    (0.015, "pagos", "POST", "/api/pagos", 500, "Error interno del servidor"),
]


def slug(s):
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if c.isalpha())


def media_hueco(d):
    """Dias medios libres entre estadias (menor = mas ocupacion)."""
    m = 0.8 if d.month in (12, 1, 6, 7) else 1.2 if d.month in (4, 10) else 1.6
    if date(2020, 3, 20) <= d <= date(2020, 9, 1):   # caida tipo COVID: anomalia util para Spark
        m *= 6
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--escala", type=float, default=1.0, help="multiplica usuarios/habitaciones extra/logs; 0.02 = prueba rapida")
    ap.add_argument("--habitaciones-extra", type=int, default=0, help="habitaciones inventadas ademas de las 20 reales (default 0)")
    ap.add_argument("--usuarios", type=int, default=3000, help="clientes nuevos")
    ap.add_argument("--logs-ruido", type=int, default=2_000_000, help="logs de navegacion/errores ademas de los ligados a eventos")
    ap.add_argument("--anio-inicio", type=int, default=2018, help="año de inicio del historico (mas años = mas reservas)")
    ap.add_argument("--semilla", type=int, default=42)
    ap.add_argument("--salida", default="./salida_csv")
    a = ap.parse_args()

    rng = random.Random(a.semilla)
    os.makedirs(a.salida, exist_ok=True)
    n_usuarios = max(int(a.usuarios * a.escala), 10)
    hab_extra = max(int(a.habitaciones_extra * a.escala), 0)
    n_ruido = int(a.logs_ruido * a.escala)
    inicio = date(a.anio_inicio, 1, 1)

    def abrir(nombre, cab):
        f = open(os.path.join(a.salida, nombre), "w", newline="", encoding="utf-8")
        w = csv.writer(f, lineterminator="\n")
        w.writerow(cab)
        return f, w

    # ------------------------- USUARIOS -----------------------------------
    f_us, w_us = abrir("usuarios.csv", ["idUsuario", "documento", "nombreCompleto", "email", "telefono", "password", "estado", "rol"])
    docs = set(DOCUMENTOS_EXISTENTES)
    clientes = list(CLIENTES_EXISTENTES)
    for i in range(n_usuarios):
        uid = ID_USUARIO0 + i
        while True:
            doc = str(rng.randint(10_000_000, 1_999_999_999))
            if doc not in docs:
                docs.add(doc)
                break
        nom, a1, a2 = rng.choice(NOMBRES), rng.choice(APELLIDOS), rng.choice(APELLIDOS)
        email = f"{slug(nom)}.{slug(a1)}{uid}@{rng.choice(DOMINIOS)}"
        tel = f"3{rng.choice([0, 1, 2, 5])}{rng.randint(0, 9)}{rng.randint(0, 9999999):07d}"
        estado = "Activo" if rng.random() < 0.96 else "Inactivo"
        w_us.writerow([uid, doc, f"{nom} {a1} {a2}", email, tel, HASH_PASSWORD, estado, "Cliente"])
        clientes.append(uid)
    f_us.close()
    rng.shuffle(clientes)

    # ------------------------- HABITACIONES -------------------------------
    habs = list(HABITACIONES_BASE)
    f_h, w_h = abrir("habitaciones.csv", ["idHabitacion", "numeroHabitacion", "tipo", "capacidad", "precioNoche", "descripcion"])
    n, piso = 0, 5
    while n < hab_extra:
        for pos in range(1, 21):
            if n >= hab_extra:
                break
            tipo = "Sencilla" if pos <= 6 else "Doble" if pos <= 14 else "Suite" if pos <= 18 else "Penthouse"
            cap = {"Sencilla": 2 if rng.random() < 0.3 else 1, "Doble": 2, "Suite": 4, "Penthouse": 8}[tipo]
            h = (ID_HAB0 + n, f"{piso}{pos:02d}", tipo, cap, PRECIO_TIPO[tipo], rng.choice(DESCS[tipo]))
            habs.append(h)
            w_h.writerow(h)
            n += 1
        piso += 1
    f_h.close()
    hab_por_id = {h[0]: h for h in habs}

    # ------------------------- ESTADIAS SIN SOLAPE ------------------------
    recs = []
    for h in habs:
        bl = BLOQUEOS.get(h[0], [])
        d = inicio + timedelta(days=rng.randint(0, 5))
        while d < FIN_RESERVAS:
            sal = d + timedelta(days=rng.choices(NOCHES, NOCHES_W)[0])
            if not any(d < b[1] and b[0] < sal for b in bl):
                if d >= HOY:
                    estado = rng.choices(["Confirmada", "Abonada", "Pendiente", "Cancelada"], [50, 22, 18, 10])[0]
                else:
                    estado = rng.choices(["Confirmada", "Cancelada"], [86, 14])[0]
                lead = min(int(rng.expovariate(1 / 20)) + 1, 150)
                crea = datetime.combine(d, time(0, 0)) - timedelta(days=lead) + timedelta(seconds=rng.randint(8 * 3600, 22 * 3600))
                if crea > AHORA:
                    crea = AHORA - timedelta(seconds=rng.randint(60, 30 * 86400))
                recs.append((crea, h[0], d, sal, estado))
            d = sal + timedelta(days=int(rng.expovariate(1 / media_hueco(sal))))
    recs.sort(key=lambda r: r[0])
    max_rid = ID_RESERVA0 + len(recs) - 1

    # ------------------------- ARCHIVOS DE SALIDA --------------------------
    f_r, w_r = abrir("reservas.csv", ["idReserva", "idUsuario", "idHabitacion", "fechaEntrada", "fechaSalida", "precioTotal", "estado", "fechaCreacion"])
    f_rs, w_rs = abrir("reserva_servicio.csv", ["idReserva", "idServicio", "cantidad", "precioUnitario"])
    f_p, w_p = abrir("pagos.csv", ["idPago", "monto", "fechaPago", "metodoPago", "estado", "idReserva"])
    f_rv, w_rv = abrir("resenas.csv", ["idResena", "idReserva", "idUsuario", "idHabitacion", "calificacion", "titulo", "comentario", "fechaResena"])
    f_l, w_l = abrir("logs.csv", ["idLog", "fechaHora", "servicio", "metodo", "endpoint", "statusCode", "latenciaMs", "nivel", "idUsuario", "ip", "userAgent", "mensaje"])

    cnt = Counter()
    ids = {"pago": ID_PAGO0, "resena": 1, "log": 1}
    ingresos = 0.0
    desajustes = 0

    def rnd(desde, hasta):
        return desde + timedelta(seconds=rng.randint(0, max(int((hasta - desde).total_seconds()), 0)))

    def log(ts, servicio, metodo, endpoint, uid, status, msg):
        if ts >= AHORA - timedelta(seconds=1):   # ningun evento puede ser posterior al momento del dump
            ts = AHORA - timedelta(seconds=rng.randint(1, 3600))
        ts = ts.replace(microsecond=rng.randint(0, 999) * 1000)
        med = {"GET": 40, "POST": 140, "PUT": 100}[metodo]
        lat = int(rng.lognormvariate(math.log(med), 0.6)) * (8 if status >= 500 else 1)
        nivel = "INFO" if status < 400 else "WARN" if status < 500 else "ERROR"
        ip = f"{rng.choice([181, 186, 190, 200, 201])}.{rng.randint(0, 255)}.{rng.randint(0, 255)}.{rng.randint(1, 254)}"
        w_l.writerow([ids["log"], ts.strftime("%Y-%m-%d %H:%M:%S.") + f"{ts.microsecond // 1000:03d}", servicio, metodo,
                      endpoint, status, lat, nivel, "\\N" if uid is None else uid, ip, rng.choice(USER_AGENTS), msg])
        ids["log"] += 1
        cnt["logs"] += 1

    def generar_resena(h, serv_ids):
        media = MEDIA_TIPO[h[2]] - (1.2 if h[0] in FORZADOS else 0)
        cal = max(1, min(5, round(rng.gauss(media, 0.95))))
        extras = [k for pal, k in EXTRAS_DESC if pal in h[5].lower()] + [EXTRAS_SERV[s] for s in serv_ids]
        pool = BASE + extras * 2
        rng.shuffle(pool)
        elegidos = []
        for p in pool:
            if p not in elegidos:
                elegidos.append(p)
            if len(elegidos) >= rng.randint(2, 4):
                break
        forzado = FORZADOS.get(h[0]) if cal <= 3 else None
        if forzado and forzado not in elegidos:
            elegidos[0] = forzado
        frases = []
        for asp in elegidos:
            pos, neg = ASPECTOS[asp]
            usar_pos = bool(pos) and asp != forzado and rng.random() < P_POS[cal]
            frases.append(rng.choice(pos if usar_pos else neg))
        abre = ABRE["pos" if cal >= 4 else "neu" if cal == 3 else "neg"]
        texto = " ".join([rng.choice(abre)] + frases + [rng.choice(CIERRA[cal])])
        return cal, rng.choice(TITULOS[cal]), texto

    # ------------------------- RESERVAS + DERIVADOS ------------------------
    for i, (crea, hid, ent, sal, estado) in enumerate(recs):
        rid = ID_RESERVA0 + i
        h = hab_por_id[hid]
        uid = clientes[int(len(clientes) * rng.random() ** 1.7)]
        noches = (sal - ent).days
        pn = round(h[4] * FACTOR_PRECIO.get(ent.year, 1.04) / 1000) * 1000

        servs = []   # (idServicio, cantidad, precio)
        if rng.random() < 0.15:
            servs.append((1, 1, SERVICIOS[1][1]))
        if rng.random() < 0.30:
            servs.append((2, rng.randint(1, noches * min(h[3], 2)), SERVICIOS[2][1]))
        if rng.random() < 0.10:
            servs.append((3, rng.randint(1, 2), SERVICIOS[3][1]))
        total = noches * pn + sum(c * p for _, c, p in servs)

        w_r.writerow([rid, uid, hid, ent.isoformat(), sal.isoformat(), f"{total:.2f}", estado, crea.strftime("%Y-%m-%d %H:%M:%S")])
        for s, c, p in servs:
            w_rs.writerow([rid, s, c, f"{p:.2f}"])
        cnt["reservas"] += 1
        cnt["estado_" + estado] += 1
        cnt["reserva_servicio"] += len(servs)

        # ---- logs previos a la reserva
        t_login = crea - timedelta(minutes=rng.randint(20, 60))
        log(t_login, "usuarios", "POST", "/api/auth/login", uid, 200, "Login exitoso")
        for _ in range(rng.randint(1, 3)):
            log(crea - timedelta(minutes=rng.randint(1, 19)), "habitaciones", "GET",
                f"/api/habitaciones/disponibles?fechaEntrada={ent}&fechaSalida={sal}", uid, 200, "Búsqueda de disponibilidad")
        log(crea, "reservas", "POST", "/api/reservas", uid, 201, f"Reserva {rid} creada (habitación {h[1]})")

        # ---- pagos
        limite = min(AHORA, datetime.combine(ent, time(14, 0)))
        if limite <= crea:
            limite = crea + timedelta(minutes=5)
        metodo = rng.choices(METODOS, METODOS_W)[0]
        pagos = []
        if estado == "Confirmada":
            t0 = crea
            if metodo == "Tarjeta" and rng.random() < 0.05:
                rej = rnd(crea, min(limite, crea + timedelta(minutes=30)))
                pagos.append((total, rej, "Tarjeta", "Rechazado"))
                t0 = min(rej + timedelta(minutes=5), limite)
            if rng.random() < 0.72:
                pagos.append((total, rnd(t0, min(limite, t0 + timedelta(days=3))), metodo, "Exitoso"))
            else:
                abono = round(total * rng.uniform(0.3, 0.5) / 1000) * 1000
                f1 = rnd(t0, min(limite, t0 + timedelta(days=2)))
                f2 = rnd(f1, limite)
                pagos.append((abono, f1, metodo, "Exitoso"))
                pagos.append((total - abono, f2, rng.choices(METODOS, METODOS_W)[0], "Exitoso"))
        elif estado == "Abonada":
            pagos.append((round(total * rng.uniform(0.3, 0.6) / 1000) * 1000, rnd(crea, min(limite, crea + timedelta(days=2))), metodo, "Exitoso"))
        elif estado == "Cancelada" and rng.random() < 0.4:
            est = "Reembolsado" if rng.random() < 0.7 else "Exitoso"
            pagos.append((round(total * rng.uniform(0.3, 1.0) / 1000) * 1000, rnd(crea, min(limite, crea + timedelta(days=2))), metodo, est))

        pagado_ok = 0
        for monto, fecha, met, est in pagos:
            w_p.writerow([ids["pago"], f"{monto:.2f}", fecha.strftime("%Y-%m-%d %H:%M:%S"), met, est, rid])
            ids["pago"] += 1
            cnt["pagos"] += 1
            if est == "Exitoso":
                pagado_ok += monto
            if est == "Rechazado":
                log(fecha, "pagos", "POST", "/api/pagos", uid, 402, f"Pago rechazado reserva {rid}")
            else:
                log(fecha, "pagos", "POST", "/api/pagos", uid, 201, f"Pago {est.lower()} reserva {rid}")
        if estado == "Confirmada":
            ingresos += pagado_ok
            if pagado_ok != total:
                desajustes += 1

        # ---- cancelacion
        if estado == "Cancelada":
            lim_c = min(AHORA, datetime.combine(ent, time(0, 0)))
            if lim_c <= crea:
                lim_c = crea + timedelta(hours=1)
            log(rnd(crea + timedelta(minutes=30), max(lim_c, crea + timedelta(minutes=31))), "reservas", "PUT",
                f"/api/reservas/{rid}/cancelar", uid, 200, f"Reserva {rid} cancelada")

        # ---- reseña (solo estadias Confirmadas ya terminadas)
        if estado == "Confirmada" and sal < HOY and rng.random() < 0.45:
            cal, titulo, texto = generar_resena(h, [s for s, _, _ in servs])
            frs = min(AHORA, datetime.combine(sal, time(12, 0)) + timedelta(seconds=rng.randint(3600, 14 * 86400)))
            w_rv.writerow([ids["resena"], rid, uid, hid, cal, titulo, texto, frs.strftime("%Y-%m-%d %H:%M:%S")])
            ids["resena"] += 1
            cnt["resenas"] += 1
            cnt[f"cal_{cal}"] += 1
            log(frs, "resenas", "POST", "/api/resenas", uid, 201, f"Reseña creada reserva {rid}")

    # ------------------------- LOGS DE RUIDO -------------------------------
    pesos = [r[0] for r in RUIDO]
    dias = (HOY - inicio).days
    for _ in range(n_ruido):
        _, srv, met, ep, st, msg = rng.choices(RUIDO, pesos)[0]
        d = inicio + timedelta(days=rng.randint(0, dias))
        ts = datetime.combine(d, time(rng.choices(range(24), HW)[0], rng.randint(0, 59), rng.randint(0, 59)))
        if ts > AHORA:
            ts -= timedelta(days=1)
        uid = rng.choice(clientes) if (rng.random() < 0.55 and st != 401) else None
        ep = ep.format(h=rng.choice(habs)[0], u=rng.choice(clientes), r=rng.randint(ID_RESERVA0, max_rid))
        log(ts, srv, met, ep, uid, st, msg)

    for f in (f_r, f_rs, f_p, f_rv, f_l):
        f.close()

    # ------------------------- RESUMEN -------------------------------------
    print(f"\nCSV generados en: {os.path.abspath(a.salida)}")
    print(f"  usuarios nuevos      : {n_usuarios:>9,}")
    print(f"  habitaciones nuevas  : {hab_extra:>9,}  (total catálogo: {len(habs)})")
    print(f"  reservas             : {cnt['reservas']:>9,}")
    print(f"  reserva_servicio     : {cnt['reserva_servicio']:>9,}")
    print(f"  pagos                : {cnt['pagos']:>9,}")
    print(f"  reseñas              : {cnt['resenas']:>9,}")
    print(f"  logs                 : {cnt['logs']:>9,}")
    print("  estados reserva      :", {k[7:]: v for k, v in cnt.items() if k.startswith("estado_")})
    cals = {c: cnt[f"cal_{c}"] for c in range(1, 6)}
    media = sum(c * v for c, v in cals.items()) / max(sum(cals.values()), 1)
    print(f"  calificaciones       : {cals}  (media {media:.2f})")
    print(f"  ingresos confirmadas : ${ingresos:,.0f} COP | reservas Confirmadas con pago != total: {desajustes}")


if __name__ == "__main__":
    main()
