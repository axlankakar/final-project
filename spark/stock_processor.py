from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, window, avg, max, min, count,
    expr, from_json, struct, when, lit
)
from pyspark.sql.types import (
    StructType, StructField, StringType,
    DoubleType, IntegerType, TimestampType
)
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define schema for incoming stock data
stock_schema = StructType([
    StructField("symbol", StringType(), True),
    StructField("price", DoubleType(), True),
    StructField("volume", IntegerType(), True),
    StructField("timestamp", TimestampType(), True)
])

def create_spark_session():
    """Creates and configures Spark session"""
    return (SparkSession.builder
            .appName("StockDataProcessor")
            .config("spark.sql.shuffle.partitions", "2")
            .config("spark.streaming.stopGracefullyOnShutdown", "true")
            .getOrCreate())

def calculate_technical_indicators(df):
    """Calculates technical indicators for stock data"""
    
    # Calculate 5-minute moving averages
    window_5min = df.withWatermark("timestamp", "10 minutes") \
        .groupBy("symbol", window("timestamp", "5 minutes")) \
        .agg(
            avg("price").alias("ma_5min"),
            max("price").alias("high_5min"),
            min("price").alias("low_5min"),
            avg("volume").alias("avg_volume_5min")
        )
    
    # Calculate price change and volatility
    price_stats = df.withWatermark("timestamp", "10 minutes") \
        .groupBy("symbol", window("timestamp", "5 minutes")) \
        .agg(
            (max("price") - min("price")).alias("price_range"),
            ((max("price") - min("price")) / avg("price") * 100).alias("volatility")
        )
    
    return window_5min, price_stats

def detect_anomalies(df, price_stats):
    """Detects price and volume anomalies"""
    
    # Detect sudden price changes
    price_anomalies = price_stats \
        .where(col("volatility") > 2.0) \  # More than 2% change
        .select(
            col("symbol"),
            col("window"),
            col("volatility"),
            lit("High volatility detected").alias("alert_type")
        )
    
    # Detect unusual volume
    volume_anomalies = df \
        .withWatermark("timestamp", "10 minutes") \
        .groupBy("symbol", window("timestamp", "5 minutes")) \
        .agg(avg("volume").alias("avg_volume")) \
        .where(col("avg_volume") > 50000) \  # High volume threshold
        .select(
            col("symbol"),
            col("window"),
            col("avg_volume"),
            lit("High volume detected").alias("alert_type")
        )
    
    return price_anomalies.union(volume_anomalies)

def write_to_postgres(df, table, mode="append"):
    """Writes DataFrame to PostgreSQL"""
    try:
        df.write \
            .format("jdbc") \
            .option("url", "jdbc:postgresql://postgres:5432/stockdata") \
            .option("driver", "org.postgresql.Driver") \
            .option("dbtable", table) \
            .option("user", "airflow") \
            .option("password", "airflow") \
            .mode(mode) \
            .save()
    except Exception as e:
        logger.error(f"Failed to write to PostgreSQL: {str(e)}")
        raise

def process_stock_data():
    """Main processing function"""
    spark = create_spark_session()
    logger.info("Created Spark session")

    # Read from Kafka
    df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "kafka:9092") \
        .option("subscribe", "stock_data") \
        .option("startingOffsets", "latest") \
        .load()

    # Parse JSON data
    parsed_df = df.select(
        from_json(col("value").cast("string"), stock_schema).alias("data")
    ).select("data.*")

    # Calculate indicators
    moving_averages, price_stats = calculate_technical_indicators(parsed_df)
    anomalies = detect_anomalies(parsed_df, price_stats)

    # Write to PostgreSQL
    query_raw = parsed_df.writeStream \
        .foreachBatch(lambda df, epoch_id: write_to_postgres(df, "stock_prices")) \
        .outputMode("append") \
        .start()

    query_stats = price_stats.writeStream \
        .foreachBatch(lambda df, epoch_id: write_to_postgres(df, "price_stats")) \
        .outputMode("append") \
        .start()

    query_anomalies = anomalies.writeStream \
        .foreachBatch(lambda df, epoch_id: write_to_postgres(df, "anomalies")) \
        .outputMode("append") \
        .start()

    # Wait for termination
    spark.streams.awaitAnyTermination()

if __name__ == "__main__":
    process_stock_data() 