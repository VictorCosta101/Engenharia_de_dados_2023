from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType

spark = SparkSession.builder \
    .appName("KafkaConsumer forEachBatch") \
    .getOrCreate()

# Define o schema para as mensagens do Kafka
schema = StructType([
    StructField("id", StringType(), True),
    StructField("message", StringType(), True)
])
  

# Endereço do servidor Kafka e tópico
kafkaServer = "kafka:9092"
kafkaTopic = "spark"

# Lê as mensagens do tópico Kafka usando Structured Streaming
df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafkaServer) \
    .option("subscribe", kafkaTopic) \
    .load()
# Converte as mensagens do Kafka em um DataFrame
kafkaMessages = df.select(col("value").alias("message"))   


print("KM")
print(kafkaMessages)
# Seleciona e mostra o conteúdo da mensagem
messages = df.selectExpr("CAST(value AS STRING)")

# Escreve as mensagens no console (para demonstração)
query = messages \
    .writeStream \
    .outputMode("append") \
    .format("console") \
    .start()


	

print("Salvando no Banco de dados")

# Define a função para processamento em lotes (batch)
def processa_batch(dataf, batch_id):
    print("Processing batch:", dataf)
    decoded_df = dataf.withColumn("message", col("message").cast("string"))
    print("decoded")
    print(decoded_df)
    
    # Escrever os dados processados no banco de dados PostgreSQL
    decoded_df.write \
        .format("jdbc") \
        .option("url", "jdbc:postgresql://postgres:5432/sparkdb") \
        .option("dbtable", "kafkaMensage") \
        .option("user", "spark") \
        .option("password", "12345") \
        .option("driver", "org.postgresql.Driver") \
        .mode("append") \
        .save()
	
"""  
# Escreve o DataFrame na tabela PostgreSQL
kafkaMessages.writeStream \
    .outputMode("append") \
    .foreachBatch(lambda batchDF, batchId: batchDF.write \
        .format("jdbc") \
        .option("url", "jdbc:postgresql://postgres:5432/sparkdb") \
        .option("dbtable", "kafkaMensage") \
        .option("user", "spark") \
        .option("password", "12345") \
        .option("driver", "org.postgresql.Driver") \
        .mode("append") \
        .save()
    ) \
    .start() \
    .awaitTermination()
"""
# Configurar o fluxo de saída com o método forEachBatch
dfSaida = kafkaMessages.writeStream \
    .foreachBatch(processa_batch) \
    .outputMode("append") \
    .trigger(processingTime="10 seconds") \
    .start()

# Aguardar a conclusão do fluxo (opcional)
dfSaida.awaitTermination()

# Encerrar a sessão do Spark
spark.stop()
