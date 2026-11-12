# Sistema de Gestión Hotelera & Analítica Big Data (Docker Swarm + Apache Spark)

Este proyecto implementa una arquitectura distribuida de microservicios para la gestión transaccional de un hotel, integrada con un pipeline de **Big Data (Apache Spark / PySpark)** para el procesamiento analítico de más de 1.1 millones de registros (logs, reservas y reseñas) y su posterior visualización en un Dashboard interactivo.

---

## 1. Topología de Infraestructura

El entorno está orquestado mediante **Vagrant** y **Docker Swarm** a través de dos nodos virtualizados en Ubuntu interconectados mediante una red overlay (`red-hotel`):

- **`servidorUbuntu1` (`192.168.100.2`):** Nodo Worker / Capa de Presentación. Aloja el contenedor del servidor web estático (Apache HTTPD en puerto interno `80`), servido al exterior a través de HAProxy.
- **`servidorUbuntu2` (`192.168.100.3`):** Nodo Manager / Punto de Entrada Único, Datos y Analítica.
  - **Reverse Proxy & Balanceador de Carga:** HAProxy (puerto `5080`), actúa como puerta de entrada unificada (*Same-Origin*) tanto para la interfaz web (`default_backend`) como para todas las rutas `/api/*`. Panel de estadísticas en `/haproxy?stats`.
  - **Microservicios Backend (Node.js/Express):** Servicios (`3000`), Usuarios (`3001`), Habitaciones (`3002`), Reservas (`3003`), Pagos (`3004`) y Backend Analítico (`3005`).
  - **Base de Datos Relacional:** MySQL 8.0 (`db-mysql` en puerto `3306`).
  - **Motor de Big Data:** Apache Spark (PySpark) + Conector JDBC MySQL.

---

## 2. Nomenclatura de Bases de Datos

El contenedor de MySQL (`db-mysql`) alberga los siguientes esquemas:

- **Bases Transaccionales Operativas:** `bd_usuarios`, `db_habitacion`, `db_reservas`, `bd_pagos`, `bd_servicios`.
- **Ingestión Masiva / Big Data:** `db_logs` (tabla `log_evento`), `db_resenas` (tabla `resena`).
- **Base de Datos Analítica Spark:** `bd_analytics` (tablas agregadas: `resumen_trafico_logs`, `resumen_sentimiento_resenas`, `resumen_ocupacion_mensual`).

---

## 3. Prerrequisitos (En la Máquina Host)

Antes de comenzar, se deben instalar las siguientes herramientas en la máquina anfitriona:

- [VirtualBox](https://www.virtualbox.org/)
- [Vagrant](https://www.vagrantup.com/)
- [Git](https://git-scm.com/)

---

## 4. Guía de Despliegue Paso a Paso

### Paso 1: Clonar e Iniciar las Máquinas Virtuales

En la máquina anfitriona (Host):

```bash
git clone https://github.com/juanrivera-d/Hotel-Proyecto.git
cd Hotel-Proyecto
vagrant up
```

### Paso 2: Configuración del Clúster Docker Swarm e Instalación de Dependencias

**1. En `servidorUbuntu2` (Manager & Nodo Analítico):**

```bash
vagrant ssh servidorUbuntu2

# Actualizar sistema e instalar Docker, Java 11 JDK, Python3, Pip y Unzip
sudo apt-get update && sudo apt-get install -y docker.io openjdk-11-jdk python3 python3-pip unzip
sudo systemctl enable --now docker
sudo usermod -aG docker vagrant && newgrp docker

# Instalar la librería PySpark en Python
pip3 install pyspark==3.3.2

# Inicializar Docker Swarm
docker swarm init --advertise-addr 192.168.100.3
```

**Importante:** Copia la línea de comando `docker swarm join --token ...` que imprimirá la terminal.

**2. En `servidorUbuntu1` (Worker):**

```bash
vagrant ssh servidorUbuntu1

# Instalar Docker
sudo apt-get update && sudo apt-get install -y docker.io unzip
sudo systemctl enable --now docker
sudo usermod -aG docker vagrant && newgrp docker

# Pegar el comando 'docker swarm join --token...' obtenido del nodo Manager
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

Restaura todo el dataset operacional y los logs en segundos directamente sobre el contenedor de MySQL:

```bash
# 1. Descomprimir el dataset masivo
unzip /vagrant/database/dataset/backup_masivo_completo.zip -d /vagrant/database/dataset/

# 2. Restaurar el dataset en el contenedor de MySQL
docker exec -i $(docker ps -q -f name=db-mysql) mysql -u root -proot < /vagrant/database/dataset/backup_masivo_completo.sql

# 3. Validar la integridad de los 1.1M de registros cargados
docker exec -it $(docker ps -q -f name=db-mysql) mysql -u root -proot -e "USE db_logs; SELECT COUNT(*) FROM log_evento;"
```

### Opción B: Generación e Ingestión Programática (Python + CSVs)

Permite auditar el proceso de simulación masiva y carga por lotes:

```bash
# 1. Generar los datos masivos
python3 /vagrant/database/bigdata_scripts/generar_dataset_hotel.py --logs-ruido 1000000 --salida /vagrant/csv_generados

# 2. Aplicar los esquemas de tablas
docker exec -i $(docker ps -q -f name=db-mysql) mysql -u root -proot < /vagrant/database/bigdata_scripts/01_esquema_resenas_logs.sql

# 3. Ejecutar la carga masiva mediante CSV
docker cp /vagrant/csv_generados $(docker ps -q -f name=db-mysql):/tmp/csv
docker exec -i $(docker ps -q -f name=db-mysql) mysql -u root -proot -e "SET GLOBAL local_infile=1;"
docker cp /vagrant/database/bigdata_scripts/02_cargar_csv.sql $(docker ps -q -f name=db-mysql):/tmp/
docker exec -it $(docker ps -q -f name=db-mysql) mysql --local-infile=1 -u root -proot -e "source /tmp/02_cargar_csv.sql;"
```

---

## 6. Ejecución del Pipeline de Big Data & Analítica (Apache Spark)

Una vez cargados los datos masivos, se procesan las agregaciones analíticas con PySpark y se guardan en la base de datos `bd_analytics`.

```bash
# 1. Crear el esquema de tablas en MySQL para recibir la analítica
docker exec -i $(docker ps -q -f name=db-mysql) mysql -u root -proot < /vagrant/big_data_analytics/01_esquema_bd_analytics.sql

# 2. Ejecutar el pipeline de procesamiento en PySpark
python3 /vagrant/big_data_analytics/pipeline_spark_hotel.py

# 3. Verificar el llenado de las tablas analíticas en MySQL
docker exec -it $(docker ps -q -f name=db-mysql) mysql -u root -proot -e "USE bd_analytics; SHOW TABLES; SELECT COUNT(*) FROM resumen_trafico_logs;"
```

---

## 7. Verificación de Accesos y Endpoints

Una vez desplegados los servicios y ejecutado el pipeline de Spark, todo el tráfico ingresa de forma centralizada a través de **HAProxy (`192.168.100.3:5080`)**:

- **Aplicación Web Frontend (Punto de Entrada Único):** [http://192.168.100.3:5080](http://192.168.100.3:5080)
- **Dashboard Analítico (Solo Administradores):** [http://192.168.100.3:5080/dashboard.html](http://192.168.100.3:5080/dashboard.html)
- **Panel de Estadísticas HAProxy:** [http://192.168.100.3:5080/haproxy?stats](http://192.168.100.3:5080/haproxy?stats)
- **Rutas API Gateway (Rutas Relativas):** `http://192.168.100.3:5080/api/{recurso}`

### Acceso y Visualización del Dashboard Analítico

- **Control de Acceso:** La vista `dashboard.html` está integrada en el menú desplegable **Administración** de todas las vistas administrativas y valida la sesión activa (`localStorage`), redirigiendo automáticamente a usuarios sin rol de Administrador.
- **Indicadores y Gráficas (Chart.js):** Consume los datos agregados de `bd_analytics` mediante rutas relativas (`/api/analytics/...`) enrutadas por HAProxy para mostrar KPIs en tiempo real y tres visualizaciones: distribución de tráfico de logs, análisis de sentimiento de reseñas por categoría de habitación y porcentaje real de ocupación mensual.

### Endpoints Transaccionales (Enrutados por HAProxy)

- `/api/servicios` $\rightarrow$ `backend-servicios` (Puerto interno `3000`)
- `/api/usuarios`, `/api/login`, `/api/perfil` $\rightarrow$ `backend-usuarios` (Puerto interno `3001`)
- `/api/habitaciones` $\rightarrow$ `backend-habitaciones` (Puerto interno `3002`)
- `/api/reservas` $\rightarrow$ `backend-reservas` (Puerto interno `3003`)
- `/api/pagos` $\rightarrow$ `backend-pagos` (Puerto interno `3004`)

### Endpoints Analíticos - Big Data (Enrutados por HAProxy)

- `/api/analytics/trafico-logs` $\rightarrow$ `backend-analitica` (Puerto interno `3005`)
- `/api/analytics/sentimiento-resenas` $\rightarrow$ `backend-analitica` (Puerto interno `3005`)
- `/api/analytics/ocupacion-mensual` $\rightarrow$ `backend-analitica` (Puerto interno `3005`)