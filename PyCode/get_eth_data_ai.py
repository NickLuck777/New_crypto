from web3 import Web3, HTTPProvider
from kafka import KafkaProducer
import json
import traceback
import logging
import time
import sys

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/usr/local/bin/eth_data.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('eth_data_collector')


def hex_encode_binary_keys(d):
    for key, value in d.items():
        if isinstance(value, bytes):
            d[key] = value.hex()
        elif isinstance(value, dict):
            hex_encode_binary_keys(value)
    return d


# Настройка Kafka Producer
logger.info("Initializing Kafka producer with bootstrap_servers='172.27.128.1:9092'")
producer = KafkaProducer(bootstrap_servers='172.27.128.1:9092',
                         value_serializer=lambda v: json.dumps(hex_encode_binary_keys(v), indent=4, sort_keys=True, default=str).encode('utf-8'))

# Подключение к Ethereum
logger.info("Connecting to Ethereum network...")
w3 = Web3(HTTPProvider("https://eth-mainnet.g.alchemy.com/v2/2wrUporcMxcIMvRrpuVaBYWFmeh_Mo7y"))
logger.info(f"Connected to Ethereum: {w3.is_connected()}")

# Получение последнего блока
start_time = time.time()
logger.info("Getting latest block number...")
last_block_number = w3.eth.get_block_number()
logger.info(f"Latest block number: {last_block_number} (took {time.time() - start_time:.2f} seconds)")

# Получение количества транзакций
start_time = time.time()
logger.info(f"Getting transaction count for block {last_block_number}...")
trx_count = w3.eth.get_block_transaction_count(last_block_number)
logger.info(f"Transaction count: {trx_count} (took {time.time() - start_time:.2f} seconds)")

# Обработка транзакций
logger.info(f"Processing {trx_count} transactions...")
successful_transactions = 0
failed_transactions = 0

for i in range(trx_count):
    start_time = time.time()
    logger.info(f"Getting transaction {i}/{trx_count}...")
    
    try:
        trx = w3.eth.get_transaction_by_block(last_block_number, i)
        logger.debug(f"Transaction hash: {trx.get('hash', 'unknown').hex() if hasattr(trx.get('hash', 'unknown'), 'hex') else trx.get('hash', 'unknown')}")
        logger.info(f"Got transaction {i} (took {time.time() - start_time:.2f} seconds)")
        
        # Отправляем транзакцию в Kafka
        logger.info(f"Sending transaction {i} to Kafka...")
        send_start_time = time.time()
        
        try:
            # Преобразуем в словарь и отправляем
            trx_dict = dict(trx)
            logger.debug(f"Transaction size: {len(json.dumps(hex_encode_binary_keys(trx_dict)))} bytes")
            
            future = producer.send('ethereum', value=trx_dict)
            logger.debug(f"Future created: {future}")
            
            # Ожидаем подтверждения
            logger.debug("Waiting for Kafka confirmation...")
            record_metadata = future.get(timeout=10)
            
            logger.info(f"Transaction {i} sent to Kafka: Topic={record_metadata.topic}, "
                       f"Partition={record_metadata.partition}, Offset={record_metadata.offset} "
                       f"(took {time.time() - send_start_time:.2f} seconds)")
            
            successful_transactions += 1
            
        except Exception as e:
            logger.error(f"Failed to send transaction {i} to Kafka: {e}")
            logger.debug(traceback.format_exc())
            failed_transactions += 1
    
    except Exception as e:
        logger.error(f"Failed to get transaction {i}: {e}")
        logger.debug(traceback.format_exc())
        failed_transactions += 1

# Завершение работы
logger.info("Flushing Kafka producer...")
flush_start_time = time.time()
producer.flush()
logger.info(f"Producer flushed (took {time.time() - flush_start_time:.2f} seconds)")

# Итоговая статистика
logger.info(f"Summary: Processed {trx_count} transactions, "
           f"Successfully sent: {successful_transactions}, "
           f"Failed: {failed_transactions}")
