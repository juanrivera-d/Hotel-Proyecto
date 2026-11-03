-- Creación de la base de datos analítica
CREATE DATABASE IF NOT EXISTS bd_analytics;
USE bd_analytics;

-- Tabla 1: Resumen de Ocupación Mensual
CREATE TABLE IF NOT EXISTS resumen_ocupacion_mensual (
    id INT AUTO_INCREMENT PRIMARY KEY,
    mes INT NOT NULL,
    anio INT NOT NULL,
    total_reservas INT NOT NULL,
    ingresos_totales DECIMAL(12,2) NOT NULL,
    porcentaje_ocupacion DECIMAL(5,2) NOT NULL
);

-- Tabla 2: Resumen de Sentimiento de Reseñas
CREATE TABLE IF NOT EXISTS resumen_sentimiento_resenas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    categoria_habitacion VARCHAR(100) NOT NULL,
    promedio_calificacion DECIMAL(3,2) NOT NULL,
    total_positivas INT NOT NULL,
    total_negativas INT NOT NULL
);

-- Tabla 3: Resumen de Tráfico de Logs
CREATE TABLE IF NOT EXISTS resumen_trafico_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    endpoint_consultado VARCHAR(255) NOT NULL,
    total_interacciones INT NOT NULL,
    errores_detectados INT NOT NULL,
    fecha_procesamiento DATE NOT NULL
);