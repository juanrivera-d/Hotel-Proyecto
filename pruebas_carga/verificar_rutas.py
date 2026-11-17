"""
Verifica las rutas reales ANTES de cargar el sistema (1 petición por ruta).
    python verificar_rutas.py              -> solo lecturas y login (si hay credenciales)
    python verificar_rutas.py --escribir   -> además crea 1 servicio de prueba (LOCUST-SMOKE)
Usa las mismas variables de entorno que locustfile.py.
"""
import os
import sys
import time

import requests

HOST = os.getenv("HOTEL_HOST", "http://192.168.100.3:5080")
LOGIN_PATH = os.getenv("HOTEL_LOGIN_PATH", "/api/login")


def probar(metodo, ruta, **kw):
    t0 = time.time()
    try:
        r = requests.request(metodo, HOST + ruta, timeout=120, **kw)
        dt = (time.time() - t0) * 1000
        print(f"  {metodo:5} {ruta:42} HTTP {r.status_code}  {len(r.content):>10,} bytes  {dt:8.0f} ms")
        return r
    except Exception as exc:  # noqa: BLE001
        print(f"  {metodo:5} {ruta:42} ERROR {type(exc).__name__}")
        return None


print(f"Host: {HOST}\n\nLecturas:")
for ruta in ["/api/habitaciones", "/api/servicios", "/api/analytics/sentimiento-resenas",
             "/api/analytics/ocupacion-mensual", "/api/analytics/trafico-logs"]:
    probar("GET", ruta)

doc, pwd = os.getenv("HOTEL_LOGIN_DOCUMENTO"), os.getenv("HOTEL_LOGIN_PASSWORD")
token = None
print("\nLogin (se prueban las dos rutas; solo una debería responder 200):")
if not (doc and pwd):
    print("  (omitido: defina HOTEL_LOGIN_DOCUMENTO y HOTEL_LOGIN_PASSWORD)")
else:
    for ruta in [LOGIN_PATH, "/api/auth/login"]:
        r = probar("POST", ruta, json={"documento": doc, "password": pwd})
        if r is not None and r.ok:
            try:
                d = r.json()
                print(f"     claves de la respuesta: {list(d.keys())}")
                token = d.get("token") or d.get("accessToken") or d.get("jwt")
            except ValueError:
                print("     la respuesta no es JSON")

if "--escribir" in sys.argv:
    print("\nEscritura (1 registro de prueba):")
    h = {"Authorization": f"Bearer {token}"} if token else {}
    print("  " + ("con token" if token else "SIN token"))
    r = probar("POST", "/api/servicios", headers=h, json={
        "nombre": "LOCUST-SMOKE", "descripcion": "Servicio generado para pruebas de carga",
        "precio": 50000, "estado": "Disponible"})
    if r is not None:
        print("  respuesta:", r.text[:200])
    print("  Limpieza: DELETE FROM bd_servicios.servicio WHERE nombre LIKE 'LOCUST-%';")
