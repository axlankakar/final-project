#!/usr/bin/env python3
"""
Stock Market Data Generator
Generates realistic stock market data and publishes to Kafka
"""

import json
import logging
import os
import random
import time
from datetime import datetime
from typing import Dict, List

from kafka import KafkaProducer
from kafka.errors import KafkaError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
KAFKA_TOPIC = 'stock_data'
STOCK_SYMBOLS = [
    'AAPL', 'GOOGL', 'MSFT', 'AMZN', 'META',
    'TSLA', 'NVDA', 'NFLX', 'AMD', 'INTC'
]

class StockDataGenerator:
    """Generates simulated stock market data with realistic price movements"""

    def __init__(self):
        self.prices: Dict[str, float] = {
            'AAPL': 180.0, 'GOOGL': 140.0, 'MSFT': 380.0,
            'AMZN': 145.0, 'META': 480.0, 'TSLA': 240.0,
            'NVDA': 850.0, 'NFLX': 480.0, 'AMD': 170.0, 'INTC': 43.0
        }
        self.volatilities: Dict[str, float] = {
            symbol: random.uniform(0.01, 0.02) for symbol in STOCK_SYMBOLS
        }
        self.producer = self._create_kafka_producer()

    def _create_kafka_producer(self) -> KafkaProducer:
        """Creates and returns a Kafka producer with retries"""
        max_retries = 5
        retry_delay = 5  # seconds

        for attempt in range(max_retries):
            try:
                return KafkaProducer(
                    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                    value_serializer=lambda x: json.dumps(x).encode('utf-8'),
                    retries=3
                )
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Failed to create Kafka producer after {max_retries} attempts: {str(e)}")
                    raise
                logger.warning(f"Attempt {attempt + 1} failed, retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)

    def _generate_price_movement(self, symbol: str) -> float:
        """Generates realistic price movement using random walk with drift"""
        volatility = self.volatilities[symbol]
        drift = 0.0001  # Slight upward bias
        current_price = self.prices[symbol]
        
        # Random walk with drift
        change_percent = random.gauss(drift, volatility)
        new_price = current_price * (1 + change_percent)
        
        # Add occasional price jumps (news events)
        if random.random() < 0.02:  # 2% chance of news event
            jump_multiplier = random.choice([1.02, 0.98])  # +/- 2% jump
            new_price *= jump_multiplier
            logger.info(f"Price jump for {symbol}: {jump_multiplier}")
        
        return round(new_price, 2)

    def _generate_volume(self) -> int:
        """Generates realistic trading volume"""
        base_volume = random.randint(1000, 10000)
        if random.random() < 0.1:  # 10% chance of volume spike
            base_volume *= random.randint(2, 5)
        return base_volume

    def generate_stock_data(self) -> List[Dict]:
        """Generates one batch of stock data for all symbols"""
        timestamp = datetime.utcnow().isoformat()
        data = []

        for symbol in STOCK_SYMBOLS:
            new_price = self._generate_price_movement(symbol)
            self.prices[symbol] = new_price
            
            stock_data = {
                'symbol': symbol,
                'price': new_price,
                'volume': self._generate_volume(),
                'timestamp': timestamp
            }
            data.append(stock_data)

        return data

    def run(self, interval: float = 1.0):
        """Runs the data generator continuously"""
        logger.info(f"Starting stock data generator, publishing to {KAFKA_BOOTSTRAP_SERVERS}")
        
        while True:
            try:
                stock_data = self.generate_stock_data()
                
                for data in stock_data:
                    self.producer.send(KAFKA_TOPIC, value=data)
                    logger.debug(f"Sent data: {data}")
                
                self.producer.flush()
                logger.info(f"Published {len(stock_data)} stock updates")
                
                time.sleep(interval)
                
            except KafkaError as e:
                logger.error(f"Kafka error: {str(e)}")
                time.sleep(5)  # Wait before retrying
                
            except Exception as e:
                logger.error(f"Unexpected error: {str(e)}")
                time.sleep(5)  # Wait before retrying

if __name__ == '__main__':
    generator = StockDataGenerator()
    generator.run() 