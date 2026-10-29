-- Ejecutar DESDE la carpeta donde estan los CSV:
--   mysql --local-infile=1 -h 127.0.0.1 -P 3306 -u root -p < 02_cargar_csv.sql
-- (el servidor necesita: SET GLOBAL local_infile=1;)
SET SESSION foreign_key_checks=0, unique_checks=0, sql_log_bin=0;

USE bd_usuarios;
LOAD DATA LOCAL INFILE '/tmp/csv/usuarios.csv' INTO TABLE usuario CHARACTER SET utf8mb4 FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 LINES
  (idUsuario,documento,nombreCompleto,email,telefono,password,estado,rol);

USE db_habitacion;
LOAD DATA LOCAL INFILE '/tmp/csv/habitaciones.csv' INTO TABLE habitacion CHARACTER SET utf8mb4 FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 LINES
  (idHabitacion,numeroHabitacion,tipo,capacidad,precioNoche,descripcion);

USE db_reservas;
LOAD DATA LOCAL INFILE '/tmp/csv/reservas.csv' INTO TABLE reserva CHARACTER SET utf8mb4 FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 LINES
  (idReserva,idUsuario,idHabitacion,fechaEntrada,fechaSalida,precioTotal,estado,fechaCreacion);
LOAD DATA LOCAL INFILE '/tmp/csv/reserva_servicio.csv' INTO TABLE reserva_servicio CHARACTER SET utf8mb4 FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 LINES
  (idReserva,idServicio,cantidad,precioUnitario);

USE bd_pagos;
LOAD DATA LOCAL INFILE '/tmp/csv/pagos.csv' INTO TABLE pago CHARACTER SET utf8mb4 FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 LINES
  (idPago,monto,fechaPago,metodoPago,estado,idReserva);

USE db_resenas;
LOAD DATA LOCAL INFILE '/tmp/csv/resenas.csv' INTO TABLE resena CHARACTER SET utf8mb4 FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 LINES
  (idResena,idReserva,idUsuario,idHabitacion,calificacion,titulo,comentario,fechaResena);

USE db_logs;
LOAD DATA LOCAL INFILE '/tmp/csv/logs.csv' INTO TABLE log_evento CHARACTER SET utf8mb4 FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' LINES TERMINATED BY '\n' IGNORE 1 LINES
  (idLog,fechaHora,servicio,metodo,endpoint,statusCode,latenciaMs,nivel,idUsuario,ip,userAgent,mensaje);

-- Indices DESPUES de cargar (mucho mas rapido)
ALTER TABLE db_reservas.reserva ADD INDEX idx_usuario (idUsuario), ADD INDEX idx_hab_fecha (idHabitacion, fechaEntrada);
ALTER TABLE db_resenas.resena ADD INDEX idx_hab (idHabitacion), ADD INDEX idx_usuario (idUsuario);
ALTER TABLE db_logs.log_evento ADD INDEX idx_fecha (fechaHora), ADD INDEX idx_servicio_status (servicio, statusCode);

-- Verificacion rapida
SELECT 'usuario' t, COUNT(*) FROM bd_usuarios.usuario UNION ALL
SELECT 'habitacion', COUNT(*) FROM db_habitacion.habitacion UNION ALL
SELECT 'reserva', COUNT(*) FROM db_reservas.reserva UNION ALL
SELECT 'pago', COUNT(*) FROM bd_pagos.pago UNION ALL
SELECT 'resena', COUNT(*) FROM db_resenas.resena UNION ALL
SELECT 'log_evento', COUNT(*) FROM db_logs.log_evento;
