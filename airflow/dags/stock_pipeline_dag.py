from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from datetime import datetime, timedelta
import logging
from kafka import KafkaAdminClient
from kafka.errors import KafkaError
import socket
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 3, 19),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(hours=1)
}

dag = DAG(
    'stock_data_pipeline',
    default_args=default_args,
    description='A DAG to orchestrate stock data processing',
    schedule_interval='@daily',
    catchup=False,
    tags=['stock', 'data', 'pipeline']
)

def wait_for_service(host, port, timeout=30):
    """Wait for a service to be ready"""
    start_time = time.time()
    while True:
        try:
            socket.create_connection((host, port), timeout=5)
            return True
        except (socket.timeout, socket.error) as ex:
            time.sleep(5)
            if time.time() - start_time >= timeout:
                raise Exception(f"Timeout waiting for {host}:{port}: {str(ex)}")

def check_kafka_health():
    """Check if Kafka is healthy"""
    try:
        # First wait for Kafka to be available
        wait_for_service('kafka', 9092)
        
        # Then check if we can connect and list topics
        max_retries = 3
        for attempt in range(max_retries):
            try:
                admin_client = KafkaAdminClient(
                    bootstrap_servers='kafka:9092',
                    client_id='airflow-kafka-check'
                )
                topics = admin_client.list_topics()
                logger.info(f"Kafka topics found: {topics}")
                admin_client.close()
                return True
            except KafkaError as e:
                if attempt == max_retries - 1:
                    raise
                logger.warning(f"Kafka connection attempt {attempt + 1} failed: {str(e)}")
                time.sleep(5)
    except Exception as e:
        logger.error(f"Kafka health check failed: {str(e)}")
        raise

def check_spark_health():
    """Check if Spark is healthy"""
    try:
        wait_for_service('spark-master', 7077)
        logger.info("Spark master is available")
        return True
    except Exception as e:
        logger.error(f"Spark health check failed: {str(e)}")
        raise

# Task to check Kafka health
check_kafka = PythonOperator(
    task_id='check_kafka_health',
    python_callable=check_kafka_health,
    dag=dag
)

# Task to check Spark health
check_spark = PythonOperator(
    task_id='check_spark_health',
    python_callable=check_spark_health,
    dag=dag
)

# Task to process data with Spark
process_stock_data = SparkSubmitOperator(
    task_id='process_stock_data',
    application='/opt/airflow/spark/stock_processor.py',
    conn_id='spark_default',
    conf={
        'spark.master': 'spark://spark-master:7077',
        'spark.submit.deployMode': 'client',
        'spark.driver.memory': '1g',
        'spark.executor.memory': '2g',
        'spark.executor.cores': '2',
        'spark.jars.packages': 'org.apache.spark:spark-sql-kafka-0-10_2.12:3.1.2,org.postgresql:postgresql:42.2.18',
        'spark.driver.extraJavaOptions': '-Dlog4j.configuration=file:///opt/spark/conf/log4j.properties',
        'spark.executor.extraJavaOptions': '-Dlog4j.configuration=file:///opt/spark/conf/log4j.properties'
    },
    verbose=True,
    dag=dag
)

# Set up task dependencies
[check_kafka, check_spark] >> process_stock_data 