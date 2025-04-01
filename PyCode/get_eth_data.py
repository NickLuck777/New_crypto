from time import sleep
from web3 import Web3, HTTPProvider
from kafka import KafkaProducer
import json
import traceback
import logging
import sys

def hex_encode_binary_keys(d):
    for key, value in d.items():
        if isinstance(value, bytes):
            d[key] = value.hex()
        elif isinstance(value, dict):
            hex_encode_binary_keys(value)
    return d

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/usr/local/bin/logs/eth_data_collector.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('eth_data_collector')

# Настройка Kafka Producer
producer = KafkaProducer(bootstrap_servers='172.28.0.10:9092',
                         value_serializer=lambda v: json.dumps(hex_encode_binary_keys(v), indent=4, sort_keys=True, default=str).encode('utf-8'))

logger.info("Initializing Kafka producer with bootstrap_servers='172.28.0.10:9092'")

w3 = Web3(HTTPProvider("https://eth-mainnet.g.alchemy.com/v2/2wrUporcMxcIMvRrpuVaBYWFmeh_Mo7y"))
logger.info(f"Connected to Ethereum: {w3.is_connected()}")

while True:
    logger.info("Getting latest block number...")

    last_block_number = w3.eth.get_block_number()
    logger.info(f"Last block number: {last_block_number}")

    trx_count = w3.eth.get_block_transaction_count(last_block_number)
    logger.info(f"Transaction count: {trx_count}")

    for i in range(trx_count):
        trx = w3.eth.get_transaction_by_block(last_block_number, i)
        
        # Отправляем транзакцию в Kafka
        try:
            logger.info("Sending transaction to Kafka...")
            future = producer.send('ethereum', value=dict(trx))
            record_metadata = future.get(timeout=10)
            logger.info(f"Transaction sent to Kafka: Topic={record_metadata.topic}, Partition={record_metadata.partition}, Offset={record_metadata.offset}")
        except Exception as e:
            logger.error(f"Failed to send transaction to Kafka: {e}")
            logger.error(traceback.format_exc())

    producer.flush()
    logger.info("Producer flushed")

    # Wait for 15 seconds before processing the next block. Usually, the new ETH block are created every 12 seconds
    logger.info("Waiting for 15 seconds before processing the next block...")
    sleep(15)

# TODO: посмотреть как зашедулить скрипт, прикрутить постгнрес в облако, соединить с кафкой через кафка коннект, прикрутить solana. 
# Не грузить дубли транзакций
