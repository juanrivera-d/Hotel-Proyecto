# Pruebas de Carga y Rendimiento (Locust)

Scripts y resultados utilizados para validar las rutas de la API y medir el rendimiento del clúster **Docker Swarm + HAProxy + MySQL** desde un cliente externo en Windows (evitando consumir CPU de las máquinas virtuales).

## 1. Descripción de Archivos

- **`verificar_rutas.py`**: Envía una única petición por endpoint antes de iniciar pruebas de carga para validar códigos HTTP, latencia base, tamaño de respuesta y autenticación JWT (`POST /api/login`). Con el flag `--escribir` valida una inserción controlada en `POST /api/servicios`.
- **`locustfile.py`**: Define las cuatro clases de usuario para aislar cada capa sin mezclar tráfico ligero y pesado (lee host, credenciales y límites desde variables de entorno):
  - `LecturaLigera`: `GET /api/habitaciones` y `GET /api/servicios` (proporción 3:2).
  - `AnaliticaLigera`: `GET /api/analytics/sentimiento-resenas` y `GET /api/analytics/ocupacion-mensual`.
  - `AnaliticaPesada`: `GET /api/analytics/trafico-logs` (~7.78 MB sin paginar).
  - `Escritura`: `POST /api/servicios` con token Bearer JWT y prefijo `LOCUST-`.
- **`resumir.py`**: Procesa los archivos `*_stats.csv` y `*_stats_history.csv` de Locust y los formatea en tablas Markdown.
- **`resultados/`**: Contiene los 40 archivos CSV exportados durante las rondas `E0` a `E3`, el script `graficar.py` y la gráfica comparativa `fig5_locust_final.png`.

## 2. Requisitos y Ejecución

```powershell
# Instalar dependencias en Python 3
python -m pip install locust requests pandas matplotlib

# Paso 1: Configurar host y verificar rutas sin carga
$env:HOTEL_HOST = "[http://192.168.100.3:5080](http://192.168.100.3:5080)"
python verificar_rutas.py

# Paso 2: Ejecutar prueba de carga (ejemplo: LecturaLigera, 20 usuarios, 120 s)
python -m locust -f locustfile.py LecturaLigera --headless -u 20 -r 2 -t 120s --csv resultados\E1b_3replicas

# Paso 3: Generar tablas resumen desde los CSV
python resumir.py resultados\E1b_1replica resultados\E1b_2replicas resultados\E1b_3replicas

# Paso 4: Regenerar la gráfica comparativa (fig5_locust_final.png)
cd resultados
python graficar.py
```

## 3. Estructura de los CSV Generados

Por cada corrida con `--csv`, Locust exporta cuatro archivos:
- `*_stats.csv`: Resumen estadístico por endpoint (solicitudes, fallos, mín, promedio, mediana, P95, P99, máx y Req/s).
- `*_stats_history.csv`: Serie temporal segundo a segundo de usuarios activos, percentiles de latencia y tasa de peticiones/fallos.
- `*_failures.csv`: Registro agrupado de errores HTTP o de conexión (si existieron).
- `*_exceptions.csv`: Trazas de excepciones internas del cliente de carga.

## 4. Inventario de Experimentos (`E0` a `E3`)

1. **`E0_*` (Prueba de humo):** `LecturaLigera` — 1 usuario, 30 s. Validación base de conectividad y latencia (0 % fallos).
2. **`E1a_*` (Lectura continua):** `LecturaLigera` — Ejecución continua de 120 s sobre `/api/habitaciones` y `/api/servicios` (0 % fallos).
3. **`E1b_1replica_*` (Escalado - 1 réplica):** `LecturaLigera` — 20 usuarios, spawn 2/s, 120 s con 1 instancia en Swarm (25.37 req/s, P95 17 ms).
4. **`E1b_2replicas_*` (Escalado - 2 réplicas):** `LecturaLigera` — 20 usuarios, spawn 2/s, 120 s con 2 instancias en Swarm (25.48 req/s, P95 19 ms).
5. **`E1b_3replicas_*` (Escalado - 3 réplicas):** `LecturaLigera` — 20 usuarios, spawn 2/s, 120 s con 3 instancias en Swarm (25.30 req/s, P95 20 ms).
6. **`E2_analitica_ligera_*` (Control analítico):** `AnaliticaLigera` — 5 usuarios, spawn 1/s, 120 s sobre `ocupacion-mensual` y `sentimiento-resenas` (prom. 10 ms).
7. **`E2_analitica_pesada_*` (Consulta masiva):** `AnaliticaPesada` — 5 usuarios, spawn 1/s, 120 s sobre `/api/analytics/trafico-logs` (~7.78 MB sin paginar, prom. 1,197 ms, 1 error HTTP 500).
8. **`E3_piloto_*` (Escritura piloto):** `Escritura` — 1 escritor, tope de 5 `POST /api/servicios` con JWT (5/5 exitosas, P95 67 ms).
9. **`E3_5escritores_*` (Escritura ampliada):** `Escritura` — Tope de 50 `POST /api/servicios` con JWT (48/50 exitosas, P95 180 ms, 2 errores HTTP 500).
10. **`E3_diagnostico_*` (Escritura verificada - 60 s):** `Escritura` — Corrida controlada de 60 s con token JWT válido (`POST /api/servicios`: 37 peticiones, 0 % fallos, P95 130 ms; graficada en el Panel 3 de `fig5_locust_final.png`).