Readme.md
@'
# Resultados de Pruebas de Carga con Locust

Esta carpeta contiene las métricas brutas exportadas por **Locust** (ejecutado desde el host Windows contra HAProxy en `http://192.168.100.3:5080`) junto con el script de visualización utilizado para generar la **Figura 5** del informe técnico IEEE.

## 1. Estructura de los archivos CSV
Por cada experimento ejecutado con `--csv`, Locust genera automáticamente cuatro archivos con el mismo prefijo:

* `*_stats.csv`: Resumen estadístico agregado por endpoint (total de solicitudes, fallos, tiempos mínimo, promedio, mediana, P95, P99, máximo y `Requests/s`).
* `*_stats_history.csv`: Serie temporal segundo a segundo con la evolución de usuarios activos, latencia por percentil y tasa de peticiones/fallos durante toda la prueba.
* `*_failures.csv`: Registro agrupado de errores HTTP o de conexión detectados en la corrida (si existieron).
* `*_exceptions.csv`: Trazas de excepciones internas del cliente de carga (vacío cuando no hubo errores de ejecución en Locust).

---

## 2. Inventario de experimentos (`E0` a `E3`)

| Prefijo de archivo | Experimento | Perfil (`locustfile.py`) | Configuración y propósito |
| :--- | :--- | :--- | :--- |
| **`E0_*`** | Prueba de humo | `LecturaLigera` | 1 usuario, 30 s. Validación base de conectividad y latencia (`0 %` fallos). |
| **`E1a_*`** | Lectura continua | `LecturaLigera` | Ejecución continua de 120 s sobre `/api/habitaciones` y `/api/servicios` (`0 %` fallos). |
| **`E1b_1replica_*`** | Escalado (1 réplica) | `LecturaLigera` | 20 usuarios, spawn `2/s`, 120 s con 1 instancia de servicio (`25.37 req/s`, P95 `17 ms`). |
| **`E1b_2replicas_*`** | Escalado (2 réplicas) | `LecturaLigera` | 20 usuarios, spawn `2/s`, 120 s con 2 instancias en Swarm (`25.48 req/s`, P95 `19 ms`). |
| **`E1b_3replicas_*`** | Escalado (3 réplicas) | `LecturaLigera` | 20 usuarios, spawn `2/s`, 120 s con 3 instancias en Swarm (`25.30 req/s`, P95 `20 ms`). |
| **`E2_analitica_ligera_*`** | Control analítico | `AnaliticaLigera` | 5 usuarios, spawn `1/s`, 120 s sobre endpoints pequeños (`ocupacion-mensual` y `sentimiento-resenas`, prom. `10 ms`). |
| **`E2_analitica_pesada_*`** | Consulta masiva | `AnaliticaPesada` | 5 usuarios, spawn `1/s`, 120 s sobre `/api/analytics/trafico-logs` (~7.78 MB por respuesta sin paginar, prom. `1,197 ms`, 1 error HTTP 500). |
| **`E3_piloto_*`** | Escritura piloto | `Escritura` | 1 escritor, tope de 5 `POST /api/servicios` con JWT (`5/5` exitosas, P95 `67 ms`). |
| **`E3_5escritores_*`** | Escritura ampliada | `Escritura` | Tope de 50 `POST /api/servicios` con JWT (`48/50` exitosas, P95 `180 ms`, 2 errores HTTP 500). |
| **`E3_50_diagnostico_*`** | Corrida descartada | `Escritura` | Intento posterior de diagnóstico bloqueado por `100 %` HTTP 401 (token no válido en esa sesión; no se llegó a insertar en MySQL). |

---

## 3. Reproducción de tablas y gráficas

* **Tablas resumen en Markdown:** Desde la carpeta raíz de pruebas (`pruebas_carga/`), ejecutar:
  ```bash
  python resumir.py resultados/E1b_1replica resultados/E1b_2replicas resultados/E1b_3replicas