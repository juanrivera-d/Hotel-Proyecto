from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, sum, avg, month, year, when, current_date

# Inicializar Spark con el conector JDBC de MySQL
spark = SparkSession.builder \
    .appName("HotelBigDataAnalytics") \
    .config("spark.jars.packages", "mysql:mysql-connector-java:8.0.28") \
    .getOrCreate()

jdbc_url_base = "jdbc:mysql://10.0.1.13:3306/"
connection_properties = {
    "user": "root",
    "password": "root",
    "driver": "com.mysql.cj.jdbc.Driver"
}

print("--- PROCESANDO RESUMEN DE TRÁFICO DE LOGS ---")
df_logs = spark.read.jdbc(jdbc_url_base + "db_logs?useSSL=false&serverTimezone=UTC", "log_evento", properties=connection_properties)
df_trafico = df_logs.groupBy("endpoint") \
    .agg(
        count("*").alias("total_interacciones"),
        sum(when(col("statusCode") >= 400, 1).otherwise(0)).alias("errores_detectados")
    ) \
    .withColumnRenamed("endpoint", "endpoint_consultado") \
    .withColumn("fecha_procesamiento", current_date())

df_trafico.write.jdbc(jdbc_url_base + "bd_analytics?useSSL=false&serverTimezone=UTC", "resumen_trafico_logs", mode="overwrite", properties=connection_properties)

print("--- PROCESANDO SENTIMIENTO DE RESEÑAS ---")
df_resenas = spark.read.jdbc(jdbc_url_base + "db_resenas?useSSL=false&serverTimezone=UTC", "resena", properties=connection_properties)
df_sentimiento = df_resenas.groupBy("idHabitacion") \
    .agg(
        avg("calificacion").alias("promedio_calificacion"),
        sum(when(col("calificacion") >= 4, 1).otherwise(0)).alias("total_positivas"),
        sum(when(col("calificacion") <= 2, 1).otherwise(0)).alias("total_negativas")
    ) \
    .withColumnRenamed("idHabitacion", "categoria_habitacion")
df_sentimiento.write.jdbc(jdbc_url_base + "bd_analytics?useSSL=false&serverTimezone=UTC", "resumen_sentimiento_resenas", mode="overwrite", properties=connection_properties)

print("--- PROCESANDO OCUPACIÓN MENSUAL ---")
df_reservas = spark.read.jdbc(jdbc_url_base + "db_reservas?useSSL=false&serverTimezone=UTC", "reserva", properties=connection_properties)
df_ocupacion = df_reservas \
    .withColumn("mes", month(col("fechaEntrada"))) \
    .withColumn("anio", year(col("fechaEntrada"))) \
    .groupBy("mes", "anio") \
    .agg(
        count("idReserva").alias("total_reservas"),
        sum("precioTotal").alias("ingresos_totales"),
        (count("idReserva") * 2.5).alias("porcentaje_ocupacion")
    )
df_ocupacion.write.jdbc(jdbc_url_base + "bd_analytics?useSSL=false&serverTimezone=UTC", "resumen_ocupacion_mensual", mode="overwrite", properties=connection_properties)

print("--- PIPELINE EJECUTADO Y TABLAS POBLADAS CON ÉXITO ---")