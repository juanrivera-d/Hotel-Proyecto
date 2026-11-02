# Sistema de Gestión Hotelera & Analítica Big Data (Docker Swarm + Apache Spark)

Este proyecto implementa una arquitectura distribuida de microservicios para la gestión transaccional de un hotel, integrada con un pipeline de **Big Data (Apache Spark)** para el procesamiento analítico de 1.1+ millones de registros (logs, reservas y reseñas) y visualización en un Dashboard interactivo.

---

## 1. Topología de Infraestructura

El entorno está orquestado mediante **Vagrant** y **Docker Swarm** en dos nodos Ubuntu:

* **`servidorUbuntu1` (`192.168.100.2`):** Nodo Worker / Capa de Presentación. Aloja el contenedor del Frontend web (Apache) expuesto en el puerto `80`.
* **`servidorUbuntu2` (`192.168.100.3`):** Nodo Manager / Núcleo de Orquestación y Datos.
  * **Balanceador de Carga:** HAProxy (puerto `5080`).
  * **Microservicios Backend (Node.js/Express):** Usuarios (`3001`), Habitaciones (`3002`), Reservas (`3003`), Pagos (`3004`), Servicios (`3000`).
  * **Base de Datos Relacional:** MySQL 8.0 (`hotel_db-mysql` en puerto `3306`).
  * **Clúster de Procesamiento (Próxima Fase):** Apache Spark Master/Workers para análisis masivo.

---

## 2. Nomenclatura de Bases de Datos

El motor de MySQL en el contenedor contiene los siguientes esquemas:

* **Transaccionales:** `bd_usuarios`, `db_habitacion`, `db_reservas`, `bd_pagos`, `bd_servicios`
* **Big Data / Ingestión:** `db_logs` (contiene `log_evento`), `db_resenas`
* **Analítica Spark (En desarrollo):** `bd_analytics` (tablas agregadas de resumen)

---

## 3. Prerrequisitos (En el sistema Host)

* VirtualBox
* Vagrant
* Git

---

## 4. Guía de Despliegue Paso a Paso

### Paso 1: Levantar la Infraestructura
En la máquina anfitriona (Host):
```bash
git clone [https://github.com/juanrivera-d/Hotel-Proyecto.git](https://github.com/juanrivera-d/Hotel-Proyecto.git)
cd Hotel-Proyecto
vagrant up
```

### Paso 2: Instalación de Docker e Inicialización de Swarm
Si es la primera vez que se levantan los nodos, se deben instalar las dependencias y unir el clúster:

1. **En `servidorUbuntu2` (Manager):**
   ```bash
   vagrant ssh servidorUbuntu2
   sudo apt-get update && sudo apt-get install -y docker.io unzip
   sudo systemctl enable --now docker
   sudo usermod -aG docker vagrant && newgrp docker
   docker swarm init --advertise-addr 192.168.100.3
   ```
2. **En `servidorUbuntu1` (Worker):**
   ```bash
   vagrant ssh servidorUbuntu1
   sudo apt-get update && sudo apt-get install -y docker.io unzip
   sudo systemctl enable --now docker
   sudo usermod -aG docker vagrant && newgrp docker
   # Ejecutar el comando 'docker swarm join...' generado por el manager
   ```

### Paso 3: Desplegar el Stack de Servicios
Desde el nodo Manager (`servidorUbuntu2`):
```bash
cd /vagrant/servidorUbuntu2_Backend
docker stack deploy -c docker-compose.yml hotel
```

---

## 5. Carga e Ingestión del Dataset Masivo (1.1M Registros)

### Opción A: Restauración Rápida (.zip - Recomendado)
Restaura el volumen completo en segundos directamente sobre el contenedor de MySQL:

```bash
# 1. Descomprimir el dataset masivo desde la carpeta compartida
unzip /vagrant/database/dataset/backup_masivo_completo.zip -d /vagrant/database/dataset/

# 2. Restaurar el dataset completo en el contenedor de MySQL
docker exec -i $(docker ps -q -f name=hotel_db-mysql) mysql -u root -proot < /vagrant/database/dataset/backup_masivo_completo.sql

# 3. Validar la integridad de los registros cargados
docker exec -it $(docker ps -q -f name=hotel_db-mysql) mysql -u root -proot -e "USE db_logs; SELECT COUNT(*) FROM log_evento;"
```

### Opción B: Generación e Ingestión Programática (Python + CSVs)
Permite auditar el proceso de simulación masiva y carga por lotes:

```bash
# 1. Generar los datos masivos (1M de registros de prueba)
python3 /vagrant/database/bigdata_scripts/generar_dataset_hotel.py --logs-ruido 1000000 --salida /vagrant/csv_generados

# 2. Aplicar los esquemas de tablas
docker exec -i $(docker ps -q -f name=hotel_db-mysql) mysql -u root -proot < /vagrant/database/bigdata_scripts/01_esquema_resenas_logs.sql

# 3. Ejecutar la carga masiva mediante CSV
docker cp /vagrant/csv_generados $(docker ps -q -f name=hotel_db-mysql):/tmp/csv
docker exec -i $(docker ps -q -f name=hotel_db-mysql) mysql -u root -proot -e "SET GLOBAL local_infile=1;"
docker cp /vagrant/database/bigdata_scripts/02_cargar_csv.sql $(docker ps -q -f name=hotel_db-mysql):/tmp/
docker exec -it $(docker ps -q -f name=hotel_db-mysql) mysql --local-infile=1 -u root -proot -e "source /tmp/02_cargar_csv.sql;"
```

---

## 6. Verificación de Accesos

* **Aplicación Web (Frontend):** `http://192.168.100.2`
* **API Gateways / Backend (HAProxy):** `http://192.168.100.3:5080/api/{recurso}`
  * Endpoints transaccionales: `/api/usuarios`, `/api/habitaciones`, `/api/reservas`, `/api/pagos`, `/api/servicios`.

---

## 7. Fase Analítica (Apache Spark & Dashboard - Próximamente)

* **Pipeline de Datos:** Procesamiento distribuido de `db_logs` y `db_resenas` mediante PySpark.
* **Persistencia Analítica:** Escritura de resultados en la base de datos `bd_analytics`.
* **Visualización:** Integración de Dashboard web interactivo con Chart.js.



3. Contrato de API para definir con el Rol 3 (Backend Analítico)
Para dejar el terreno preparado antes de que el Rol 2 (Spark) entregue sus scripts, acuerda con el Rol 3 la creación de la nueva base de datos bd_analytics en MySQL y la estructura de endpoints que el backend expondrá.
Estructura de la Base de Datos bd_analytics
Spark escribirá los resúmenes procesados en estas 3 tablas dentro de bd_analytics:
1.	resumen_ocupacion_mensual
o	Campos: id, mes, anio, total_reservas, ingresos_totales, porcentaje_ocupacion.
2.	resumen_sentimiento_resenas
o	Campos: id, categoria_habitacion, promedio_calificacion, total_positivas, total_negativas.
3.	resumen_trafico_logs
o	Campos: id, endpoint_consultado, total_interacciones, errores_detectados, fecha_procesamiento.
Endpoints Analíticos a Implementar en el Backend (Rol 3)
El Rol 3 creará un microservicio o módulo analítico expuesto en HAProxy bajo las siguientes rutas:
•	GET [http://192.168.100.3:5080/api/analytics/ocupacion](http://192.168.100.3:5080/api/analytics/ocupacion)
o	Devuelve el JSON con la tendencia de ingresos y reservas mensuales.
•	GET [http://192.168.100.3:5080/api/analytics/sentimientos](http://192.168.100.3:5080/api/analytics/sentimientos)
o	Devuelve las métricas de satisfacción del cliente procesadas por Spark (NLP).
•	GET [http://192.168.100.3:5080/api/analytics/logs-resumen](http://192.168.100.3:5080/api/analytics/logs-resumen)
o	Devuelve los contadores de tráfico y rendimiento del sistema.

Pasarles mañana:
1. El Rol 2 (Spark) trabaja de forma 100% independiente
•	¿Qué necesita para empezar? Solo necesita los archivos .csv o la base de datos masiva (db_logs y db_resenas), los cuales ya existen y están validados en el repositorio.
•	¿Qué debe hacer? Montar su clúster/entorno de Spark, escribir los scripts en PySpark o Spark SQL para procesar el millón de datos y definir cómo agregará las métricas.
•	Su única tarea de integración: Una vez que cree la base de datos bd_analytics y las 3 tablas de resumen en MySQL, ejecutará sus scripts para poblarlas con los resultados procesados.



El Rol 2 no solo les pasa una idea de cómo debe verse la base de datos, sino que debe subir al repositorio (dentro de una carpeta como database/analytics_scripts/ o similar) dos cosas:
•	El script SQL del esquema (01_esquema_bd_analytics.sql): Con las sentencias CREATE DATABASE IF NOT EXISTS bd_analytics; y los CREATE TABLE de las 3 tablas analíticas (resumen_ocupacion_mensual, resumen_sentimiento_resenas, resumen_trafico_logs).
•	El script de PySpark / Spark SQL: Que procesa los 1.1M de datos y escribe directamente los registros finales en bd_analytics dentro de MySQL.



Con sofia: 
Estructura de la Base de Datos bd_analytics
Spark escribirá los resúmenes procesados en estas 3 tablas dentro de bd_analytics:
1.	resumen_ocupacion_mensual
o	Campos: id, mes, anio, total_reservas, ingresos_totales, porcentaje_ocupacion.
2.	resumen_sentimiento_resenas
o	Campos: id, categoria_habitacion, promedio_calificacion, total_positivas, total_negativas.
3.	resumen_trafico_logs
o	Campos: id, endpoint_consultado, total_interacciones, errores_detectados, fecha_procesamiento.
Endpoints Analíticos a Implementar en el Backend (Rol 3)
El Rol 3 creará un microservicio o módulo analítico expuesto en HAProxy bajo las siguientes rutas:
•	GET [http://192.168.100.3:5080/api/analytics/ocupacion](http://192.168.100.3:5080/api/analytics/ocupacion)
o	Devuelve el JSON con la tendencia de ingresos y reservas mensuales.
•	GET [http://192.168.100.3:5080/api/analytics/sentimientos](http://192.168.100.3:5080/api/analytics/sentimientos)
o	Devuelve las métricas de satisfacción del cliente procesadas por Spark (NLP).
•	GET [http://192.168.100.3:5080/api/analytics/logs-resumen](http://192.168.100.3:5080/api/analytics/logs-resumen)
o	Devuelve los contadores de tráfico y rendimiento del sistema.
Con esta definición, el Rol 4 (Frontend) puede ir armando la interfaz del Dashboard usando datos de prueba con ese mismo formato JSON, mientras el Rol 2 (Spark) termina de montar el pipeline de datos.

