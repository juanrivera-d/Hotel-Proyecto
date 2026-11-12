import os
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

MYSQL_USER = os.getenv("HOTEL_MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("HOTEL_MYSQL_PASSWORD", "root")

spark = (
    SparkSession.builder
    .appName("HotelAnalyticsV2")
    .master("local[1]")
    .config("spark.jars.packages", "mysql:mysql-connector-java:8.0.28")
    .config("spark.driver.memory", "512m")
    .config("spark.sql.shuffle.partitions", "4")
    .getOrCreate()
)

BASE = "jdbc:mysql://192.168.100.3:3306/"

def leer(base_datos, tabla):
    return (
        spark.read.format("jdbc")
        .option("url", BASE + base_datos + "?useSSL=false&serverTimezone=UTC")
        .option("dbtable", tabla)
        .option("user", MYSQL_USER)
        .option("password", MYSQL_PASSWORD)
        .option("driver", "com.mysql.cj.jdbc.Driver")
        .load()
    )

try:
    # 1. TRAFICO DE LOGS
    print("\n=== TRAFICO DE LOGS ===")

    logs = leer("db_logs", "log_evento")

    trafico = (
        logs.groupBy("endpoint")
        .agg(
            F.count("*").alias("total_interacciones"),
            F.sum(
                F.when(F.col("statusCode") >= 400, 1)
                 .otherwise(0)
            ).alias("errores_detectados")
        )
        .withColumnRenamed("endpoint", "endpoint_consultado")
        .withColumn("fecha_procesamiento", F.current_date())
    )

    trafico.orderBy(
        F.desc("total_interacciones")
    ).show(10, truncate=False)

    # 2. SENTIMIENTO DE RESEÑAS
    print("\n=== SENTIMIENTO DE RESEÑAS ===")

    resenas = leer("db_resenas", "resena")
    habitaciones = leer("db_habitacion", "habitacion")

    sentimiento = (
        resenas.alias("r")
        .join(
            habitaciones.alias("h"),
            F.col("r.idHabitacion") == F.col("h.idHabitacion"),
            "inner"
        )
        .groupBy(F.col("h.tipo"))
        .agg(
            F.round(
                F.avg("r.calificacion"), 2
            ).alias("promedio_calificacion"),
            F.sum(
                F.when(F.col("r.calificacion") >= 4, 1)
                 .otherwise(0)
            ).alias("total_positivas"),
            F.sum(
                F.when(F.col("r.calificacion") <= 2, 1)
                 .otherwise(0)
            ).alias("total_negativas")
        )
        .withColumnRenamed("tipo", "categoria_habitacion")
    )

    sentimiento.show(truncate=False)


    # 3. OCUPACION MENSUAL
    print("\n=== OCUPACION MENSUAL ===")

    reservas = leer("db_reservas", "reserva")

    validas = reservas.filter(
        F.col("estado").isin("Confirmada", "Abonada")
    )

    # Contar cada reserva en su mes de entrada
    conteo_reservas = (
        validas
        .groupBy(
            F.year("fechaEntrada").alias("anio"),
            F.month("fechaEntrada").alias("mes")
        )
        .agg(F.count("*").alias("total_reservas"))
    )

    # Calcular la duración real de cada estancia
    reservas_con_noches = validas.withColumn(
        "duracion_noches",
        F.datediff("fechaSalida", "fechaEntrada")
    )

    # Distribuir cada estancia por noches, incluso entre meses
    noches = (
        reservas_con_noches
        .withColumn(
            "fecha_noche",
            F.explode(
                F.sequence(
                    F.to_date("fechaEntrada"),
                    F.date_sub(F.to_date("fechaSalida"), 1)
                )
            )
        )
        .withColumn("anio", F.year("fecha_noche"))
        .withColumn("mes", F.month("fecha_noche"))
        .withColumn(
            "ingreso_noche",
            F.col("precioTotal") / F.col("duracion_noches")
        )
    )

    resumen_noches = (
        noches.groupBy("anio", "mes")
        .agg(
            F.count("*").alias("noches_ocupadas"),
            F.sum("ingreso_noche").alias("ingresos_totales")
        )
    )

    ocupacion = (
        resumen_noches
        .join(conteo_reservas, ["anio", "mes"], "left")
        .fillna({"total_reservas": 0})
        .withColumn(
            "dias_mes",
            F.dayofmonth(
                F.last_day(
                    F.make_date("anio", "mes", F.lit(1))
                )
            )
        )
        .withColumn(
            "porcentaje_ocupacion",
            F.round(
                F.col("noches_ocupadas")
                / (F.lit(20) * F.col("dias_mes")) * 100,
                2
            )
        )
        .withColumn(
            "ingresos_totales",
            F.round("ingresos_totales", 2)
        )
    )

    print("\n=== VALIDACION FINANCIERA ===")

    validacion = ocupacion.agg(
        F.sum("ingresos_totales").alias("total_ingresos"),
        F.sum("total_reservas").alias("total_reservas"),
        F.count("*").alias("meses_procesados")
    )

    validacion.show(truncate=False)

    ocupacion.select(
        "anio",
        "mes",
        "total_reservas",
        "ingresos_totales",
        "porcentaje_ocupacion"
    ).orderBy(
        F.desc("anio"),
        F.desc("mes")
    ).show(12, truncate=False)


    # 4. CARGA DE RESULTADOS A MYSQL
    print("\n=== PREPARANDO CARGA ANALITICA ===")

    print("Iniciando carga.")

    def guardar(df, tabla):
        (
            df.write.format("jdbc")
            .option(
                "url",
                BASE + "bd_analytics?useSSL=false&serverTimezone=UTC"
            )
            .option("dbtable", tabla)
            .option("user", MYSQL_USER)
            .option("password", MYSQL_PASSWORD)
            .option("driver", "com.mysql.cj.jdbc.Driver")
            .option("batchsize", "1000")
            .option("truncate", "true")
            .mode("overwrite")
            .save()
        )

        print(f"Carga completada: {tabla}")

    guardar(
        trafico.select(
            "endpoint_consultado",
            F.col("total_interacciones").cast("int"),
            F.col("errores_detectados").cast("int"),
            "fecha_procesamiento"
        ),
        "resumen_trafico_logs"
    )

    guardar(
        sentimiento.select(
            "categoria_habitacion",
            F.col("promedio_calificacion").cast("decimal(3,2)"),
            F.col("total_positivas").cast("int"),
            F.col("total_negativas").cast("int")
        ),
        "resumen_sentimiento_resenas"
    )

    guardar(
        ocupacion.select(
            F.col("mes").cast("int"),
            F.col("anio").cast("int"),
            F.col("total_reservas").cast("int"),
            F.col("ingresos_totales").cast("decimal(12,2)"),
            F.col("porcentaje_ocupacion").cast("decimal(5,2)")
        ),
        "resumen_ocupacion_mensual"
    )

    print("\nCARGA ANALITICA FINALIZADA")


finally:
    spark.stop()
