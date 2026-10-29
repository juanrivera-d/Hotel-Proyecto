-- Esquemas de los 2 microservicios nuevos (misma convencion que tu dump)
CREATE DATABASE IF NOT EXISTS `db_resenas` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE `db_resenas`;
DROP TABLE IF EXISTS `resena`;
CREATE TABLE `resena` (
  `idResena` int NOT NULL AUTO_INCREMENT,
  `idReserva` int NOT NULL,
  `idUsuario` int NOT NULL,
  `idHabitacion` int NOT NULL,
  `calificacion` tinyint NOT NULL,
  `titulo` varchar(120) DEFAULT NULL,
  `comentario` text,
  `fechaResena` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`idResena`),
  UNIQUE KEY `uk_resena_reserva` (`idReserva`),
  CONSTRAINT `chk_calificacion` CHECK (`calificacion` BETWEEN 1 AND 5)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE DATABASE IF NOT EXISTS `db_logs` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE `db_logs`;
DROP TABLE IF EXISTS `log_evento`;
CREATE TABLE `log_evento` (
  `idLog` bigint NOT NULL AUTO_INCREMENT,
  `fechaHora` datetime(3) NOT NULL,
  `servicio` varchar(30) NOT NULL,
  `metodo` varchar(7) NOT NULL,
  `endpoint` varchar(150) NOT NULL,
  `statusCode` smallint NOT NULL,
  `latenciaMs` int NOT NULL,
  `nivel` enum('INFO','WARN','ERROR') NOT NULL,
  `idUsuario` int DEFAULT NULL,
  `ip` varchar(45) DEFAULT NULL,
  `userAgent` varchar(120) DEFAULT NULL,
  `mensaje` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`idLog`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
