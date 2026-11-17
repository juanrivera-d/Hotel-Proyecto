

Esta carpeta contiene los scripts utilizados para validar las rutas de la API
y medir el rendimiento del cluster Docker Swarm + HAProxy + MySQL desde un
cliente externo en Windows (evitando consumir CPU de las maquinas virtuales).

1. DESCRIPCION DE ARCHIVOS
--------------------------
- verificar_rutas.py
  Envia una unica peticion por endpoint antes de iniciar pruebas de carga para
  verificar codigos HTTP, latencia base, tamano de respuesta y funcionamiento
  de autenticacion JWT (POST /api/login). Con el flag --escribir valida una
  insercion controlada en POST /api/servicios.

- locustfile.py
  Define las cuatro clases de usuario utilizadas para aislar cada capa de la
  arquitectura sin mezclar trafico ligero y pesado:
    * LecturaLigera: GET /api/habitaciones y GET /api/servicios (proporcion 3:2).
    * AnaliticaPesada: GET /api/analytics/trafico-logs (~7.78 MB sin paginar).
    * AnaliticaLigera: GET /api/analytics/sentimiento-resenas y ocupacion-mensual.
    * Escritura: POST /api/servicios con token Bearer JWT y prefijo LOCUST-.
  Toda la configuracion (host, credenciales, limites y pausas) se lee mediante
  variables de entorno para no almacenar secretos en el codigo fuente.

- resumir.py
  Procesa los archivos *_stats.csv y *_stats_history.csv generados por Locust
  y los formatea en tablas Markdown listas para documentacion tecnica.

- resultados/
  Contiene los 40 archivos CSV exportados durante las rondas E0, E1a, E1b, E2 y E3,
  el script graficar.py, la imagen fig5_locust_final.png y su inventario detallado
  (resultados/IMPORTANTE.txt).

2. REQUISITOS Y EJECUCION (DESDE LA CARPETA pruebas_carga/)
-----------------------------------------------------------
Requisitos en Python 3:
  pip install locust requests pandas matplotlib

Paso 1 - Configurar host y verificar rutas (sin carga):
  $env:HOTEL_HOST = "http://192.168.100.3:5080"
  python verificar_rutas.py

Paso 2 - Ejecutar una prueba de carga (ejemplo: LecturaLigera, 20 usuarios, 120 s):
  python -m locust -f locustfile.py LecturaLigera --headless -u 20 -r 2 -t 120s --csv resultados\E1b_3replicas

Paso 3 - Generar tablas resumen desde los CSV:
  python resumir.py resultados\E1b_1replica resultados\E1b_2replicas resultados\E1b_3replicas

Paso 4 - Regenerar la grafica comparativa del informe:
  cd resultados
  python graficar.py