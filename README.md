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


