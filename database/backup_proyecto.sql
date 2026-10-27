-- MySQL dump 10.13  Distrib 8.0.46, for Linux (x86_64)
--
-- Host: localhost    Database: bd_usuarios
-- ------------------------------------------------------
-- Server version	8.0.46

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Current Database: `bd_usuarios`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `bd_usuarios` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;

USE `bd_usuarios`;

--
-- Table structure for table `usuario`
--

DROP TABLE IF EXISTS `usuario`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuario` (
  `idUsuario` int NOT NULL AUTO_INCREMENT,
  `documento` varchar(20) NOT NULL,
  `nombreCompleto` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `telefono` varchar(20) DEFAULT NULL,
  `password` varchar(255) NOT NULL,
  `estado` enum('Activo','Inactivo') DEFAULT 'Activo',
  `rol` enum('Cliente','Admin') NOT NULL DEFAULT 'Cliente',
  PRIMARY KEY (`idUsuario`),
  UNIQUE KEY `documento` (`documento`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usuario`
--

LOCK TABLES `usuario` WRITE;
/*!40000 ALTER TABLE `usuario` DISABLE KEYS */;
INSERT INTO `usuario` VALUES (1,'100101','Carlos Mendoza (Administrador)','admin@hotelleyton.com','3000000001','$2b$10$yuT4cuPXJC3iAOcGn8htW.wmwBlRqn2kpx5RyGIzn2s3xqhDJOyIa','Activo','Admin'),(2,'1080050144','Santiago Eraso (Cliente)','santiagoerasoortega@gmail.com','300123454515','$2b$10$yuT4cuPXJC3iAOcGn8htW.wmwBlRqn2kpx5RyGIzn2s3xqhDJOyIa','Activo','Cliente'),(3,'1231','Javier Bedoya','cualquier@gmail.com','894644','$2b$10$T7x.1fC.FWrjCyCNYwfA2.B2vPLN66IrKHggBC0RpR9vWZYSVUQRu','Activo','Cliente'),(4,'12365','Johan Vivas','ejemplo2@gmail.com','2132465','$2b$10$ChVRmww8w9bgSFDh.sm4bev9013hlN9M94t0T79A9mS39LKSep7jC','Activo','Cliente');
/*!40000 ALTER TABLE `usuario` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Current Database: `bd_servicios`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `bd_servicios` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;

USE `bd_servicios`;

--
-- Table structure for table `servicio`
--

DROP TABLE IF EXISTS `servicio`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `servicio` (
  `idServicio` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `descripcion` text,
  `precio` decimal(10,2) NOT NULL,
  `estado` enum('Disponible','No disponible') DEFAULT 'Disponible',
  PRIMARY KEY (`idServicio`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `servicio`
--

LOCK TABLES `servicio` WRITE;
/*!40000 ALTER TABLE `servicio` DISABLE KEYS */;
INSERT INTO `servicio` VALUES (1,'Spa Completo','Acceso a piscina, sauna y masajes',120000.00,'Disponible'),(2,'Desayuno Buffet','Incluye bebidas calientes y frutas',35000.00,'Disponible'),(3,'Transporte al Aeropuerto','Servicio privado de traslado',80000.00,'Disponible');
/*!40000 ALTER TABLE `servicio` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Current Database: `bd_pagos`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `bd_pagos` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;

USE `bd_pagos`;

--
-- Table structure for table `pago`
--

DROP TABLE IF EXISTS `pago`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pago` (
  `idPago` int NOT NULL AUTO_INCREMENT,
  `monto` decimal(10,2) NOT NULL,
  `fechaPago` datetime DEFAULT CURRENT_TIMESTAMP,
  `metodoPago` enum('Efectivo','Tarjeta','Transferencia') NOT NULL,
  `estado` enum('Exitoso','Pendiente','Rechazado','Reembolsado') DEFAULT 'Exitoso',
  `idReserva` int NOT NULL,
  PRIMARY KEY (`idPago`),
  KEY `idx_reserva` (`idReserva`)
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pago`
--

LOCK TABLES `pago` WRITE;
/*!40000 ALTER TABLE `pago` DISABLE KEYS */;
INSERT INTO `pago` VALUES (1,480000.00,'2026-09-16 14:42:14','Efectivo','Exitoso',1),(2,240000.00,'2026-09-25 00:33:13','Efectivo','Exitoso',5),(3,240000.00,'2026-09-25 13:14:19','Efectivo','Exitoso',6),(4,240000.00,'2026-09-25 13:14:49','Efectivo','Exitoso',6),(5,275000.00,'2026-09-25 15:15:25','Efectivo','Exitoso',8),(6,275000.00,'2026-09-25 15:15:37','Efectivo','Exitoso',8),(7,200000.00,'2026-09-25 15:17:16','Efectivo','Exitoso',9),(8,200000.00,'2026-09-28 15:00:14','Efectivo','Exitoso',10),(9,150000.00,'2026-09-30 06:32:48','Tarjeta','Exitoso',11),(10,5000.00,'2026-09-30 06:35:18','Tarjeta','Exitoso',11),(11,75000.00,'2026-09-30 07:01:35','Tarjeta','Exitoso',10),(12,440000.00,'2026-09-30 09:15:33','Tarjeta','Exitoso',15),(13,100000.00,'2026-09-30 09:22:23','Tarjeta','Exitoso',16),(14,75000.00,'2026-09-30 09:28:03','Tarjeta','Exitoso',9),(15,50000.00,'2026-09-30 15:32:01','Tarjeta','Exitoso',19),(16,100000.00,'2026-09-30 16:31:38','Efectivo','Exitoso',20),(17,55000.00,'2026-09-30 16:33:13','Tarjeta','Exitoso',20),(18,240000.00,'2026-09-30 16:40:10','Tarjeta','Exitoso',21),(19,240000.00,'2026-10-19 00:34:10','Tarjeta','Exitoso',34);
/*!40000 ALTER TABLE `pago` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Current Database: `db_habitacion`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `db_habitacion` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;

USE `db_habitacion`;

--
-- Table structure for table `habitacion`
--

DROP TABLE IF EXISTS `habitacion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `habitacion` (
  `idHabitacion` int NOT NULL AUTO_INCREMENT,
  `numeroHabitacion` varchar(10) NOT NULL,
  `tipo` varchar(50) NOT NULL,
  `capacidad` int NOT NULL,
  `precioNoche` decimal(10,2) NOT NULL,
  `descripcion` text,
  PRIMARY KEY (`idHabitacion`),
  UNIQUE KEY `numeroHabitacion` (`numeroHabitacion`)
) ENGINE=InnoDB AUTO_INCREMENT=21 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `habitacion`
--

LOCK TABLES `habitacion` WRITE;
/*!40000 ALTER TABLE `habitacion` DISABLE KEYS */;
INSERT INTO `habitacion` VALUES (1,'101','Sencilla',2,120000.00,'Vista al jardín interno bonito, cama individual'),(2,'102','Sencilla',1,120000.00,'Vista a la calle principal, escritorio de trabajo'),(3,'103','Sencilla',1,120000.00,'Habitación estándar cama individual'),(4,'104','Sencilla',1,120000.00,'Cama individual, TV por cable'),(5,'105','Sencilla',1,120000.00,'En reparación de aire acondicionado'),(6,'201','Doble',2,220000.00,'Dos camas individuales, balcón privado'),(7,'202','Doble',2,220000.00,'Cama King size, baño privado amplio'),(8,'203','Doble',2,220000.00,'Dos camas semi-dobles'),(9,'204','Doble',2,220000.00,'Cama matrimonial, vista a la piscina'),(10,'205','Doble',2,220000.00,'Vista a la ciudad, escritorio doble'),(11,'206','Doble',2,220000.00,'Dos camas individuales, frigobar'),(12,'207','Doble',2,220000.00,'Pintura y mantenimiento general'),(13,'301','Suite',4,450000.00,'Suite familiar con 2 habitaciones separadas y sala'),(14,'302','Suite',4,450000.00,'Suite nupcial con Jacuzzi y balcón'),(15,'303','Suite',4,450000.00,'Suite ejecutiva con sala de reuniones y minibar'),(16,'304','Suite',4,450000.00,'Vista panorámica, 2 camas Queen size'),(17,'305','Suite',4,450000.00,'Suite de lujo con terraza privada'),(18,'401','Penthouse',8,700000.00,'Piso completo, Jacuzzi, terraza y cocina equipada'),(19,'402','Penthouse',8,700000.00,'Penthouse con vista 360, zona de BBQ y bar'),(20,'403','Penthouse',8,700000.00,'Penthouse VIP con acceso a elevador privado');
/*!40000 ALTER TABLE `habitacion` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Current Database: `db_reservas`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `db_reservas` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;

USE `db_reservas`;

--
-- Table structure for table `reserva`
--

DROP TABLE IF EXISTS `reserva`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `reserva` (
  `idReserva` int NOT NULL AUTO_INCREMENT,
  `idUsuario` int NOT NULL,
  `idHabitacion` int NOT NULL,
  `fechaEntrada` date NOT NULL,
  `fechaSalida` date NOT NULL,
  `precioTotal` decimal(10,2) DEFAULT NULL,
  `estado` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT 'Pendiente',
  `fechaCreacion` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`idReserva`)
) ENGINE=InnoDB AUTO_INCREMENT=138 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `reserva`
--

LOCK TABLES `reserva` WRITE;
/*!40000 ALTER TABLE `reserva` DISABLE KEYS */;
INSERT INTO `reserva` VALUES (1,1,1,'2026-11-01','2026-11-05',480000.00,'Confirmada','2026-09-22 01:51:40'),(2,2,6,'2026-11-10','2026-11-12',440000.00,'Cancelada','2026-09-22 01:51:40'),(3,1,1,'2026-10-01','2026-10-03',395000.00,'Cancelada','2026-09-24 02:52:37'),(4,1,1,'2026-01-01','2026-01-03',395000.00,'Cancelada','2026-09-24 03:44:17'),(5,2,1,'2026-02-12','2026-02-13',240000.00,'Confirmada','2026-09-24 23:56:51'),(6,2,1,'2026-02-14','2026-02-15',240000.00,'Confirmada','2026-09-25 13:11:54'),(7,2,1,'2026-02-20','2026-02-21',240000.00,'Cancelada','2026-09-25 15:10:23'),(8,2,1,'2026-02-22','2026-02-23',275000.00,'Confirmada','2026-09-25 15:13:14'),(9,2,1,'2026-02-25','2026-02-26',275000.00,'Confirmada','2026-09-25 15:17:08'),(10,2,1,'2026-02-26','2026-02-27',275000.00,'Confirmada','2026-09-28 14:59:22'),(11,2,3,'2026-10-01','2026-10-02',155000.00,'Confirmada','2026-09-30 06:06:19'),(12,2,1,'2026-09-01','2026-09-02',120000.00,'Cancelada','2026-09-30 08:17:07'),(13,2,1,'2026-02-11','2026-02-12',120000.00,'Cancelada','2026-09-30 08:18:26'),(14,2,2,'2026-02-11','2026-02-12',120000.00,'Cancelada','2026-09-30 08:31:06'),(15,2,6,'2026-11-09','2026-11-11',440000.00,'Confirmada','2026-09-30 09:07:40'),(16,2,1,'2026-09-30','2026-10-01',120000.00,'Abonada','2026-09-30 09:21:22'),(17,2,1,'2026-10-01','2026-10-02',120000.00,'Cancelada','2026-09-30 09:28:55'),(18,2,1,'2026-09-17','2026-09-18',240000.00,'Cancelada','2026-09-30 15:28:48'),(19,2,1,'2026-09-17','2026-09-18',120000.00,'Abonada','2026-09-30 15:30:58'),(20,4,1,'2026-10-07','2026-10-08',155000.00,'Confirmada','2026-09-30 16:29:12'),(21,2,2,'2026-10-05','2026-10-06',240000.00,'Confirmada','2026-09-30 16:39:23'),(22,1,1,'2026-03-01','2026-03-05',0.00,'Cancelada','2026-10-18 01:42:09'),(31,1,1,'2026-05-26','2026-05-27',0.00,'Cancelada','2026-10-18 06:04:28'),(33,1,1,'2026-05-01','2026-05-02',120000.00,'Cancelada','2026-10-19 00:31:24'),(34,2,2,'2026-10-18','2026-10-19',240000.00,'Confirmada','2026-10-19 00:33:44'),(135,1,1,'2026-05-02','2026-05-03',120000.00,'Cancelada','2026-10-19 00:47:02'),(136,1,1,'2026-05-02','2026-05-03',155000.00,'Cancelada','2026-10-19 01:01:44'),(137,1,1,'2026-05-02','2026-05-03',120000.00,'Cancelada','2026-10-19 01:04:10');
/*!40000 ALTER TABLE `reserva` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `reserva_servicio`
--

DROP TABLE IF EXISTS `reserva_servicio`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `reserva_servicio` (
  `idReserva` int NOT NULL,
  `idServicio` int NOT NULL,
  `cantidad` int DEFAULT '1',
  `precioUnitario` decimal(10,2) NOT NULL,
  PRIMARY KEY (`idReserva`,`idServicio`),
  CONSTRAINT `reserva_servicio_ibfk_1` FOREIGN KEY (`idReserva`) REFERENCES `reserva` (`idReserva`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `reserva_servicio`
--

LOCK TABLES `reserva_servicio` WRITE;
/*!40000 ALTER TABLE `reserva_servicio` DISABLE KEYS */;
INSERT INTO `reserva_servicio` VALUES (3,1,1,120000.00),(3,2,1,35000.00),(4,1,1,120000.00),(4,2,1,35000.00),(5,1,1,120000.00),(6,1,1,120000.00),(7,1,1,120000.00),(8,1,1,120000.00),(8,2,1,35000.00),(9,1,1,120000.00),(9,2,1,35000.00),(10,1,1,120000.00),(10,2,1,35000.00),(18,1,1,120000.00),(20,2,1,35000.00),(21,1,1,120000.00),(34,1,1,120000.00),(136,2,1,35000.00);
/*!40000 ALTER TABLE `reserva_servicio` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-10-27  2:16:41
