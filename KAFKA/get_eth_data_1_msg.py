from time import sleep
from web3 import Web3, HTTPProvider
from kafka import KafkaProducer
import json
import traceback
import logging
import sys
from hexbytes import HexBytes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/usr/local/bin/logs/eth_data_collector.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('eth_data_collector')

# Schema for transaction
schema = {
    "type": "struct",
    "fields": [
        {"field": "blockHash", "type": "string"},
        {"field": "blockNumber", "type": "int64"},
        {"field": "chainId", "type": "int64"},
        {"field": "from", "type": "string"},
        {"field": "gas", "type": "int64"},
        {"field": "gasPrice", "type": "int64"},
        {"field": "hash", "type": "string"},
        {"field": "input", "type": "string"},
        {"field": "maxFeePerGas", "type": "int64", "optional": True}, # Missing in the legacy transactions, ruin the msg processing
        {"field": "maxPriorityFeePerGas", "type": "int64", "optional": True}, # Missing in the legacy transactions, ruin the msg processing
        {"field": "nonce", "type": "int64"},
        {"field": "r", "type": "string"},
        {"field": "s", "type": "string"},
        {"field": "to", "type": "string"},
        {"field": "transactionIndex", "type": "int64"},
        {"field": "type", "type": "int32"},
        {"field": "v", "type": "int32"},
        {"field": "value", "type": "int64"},
        {"field": "yParity", "type": "int32","optional": True},
        {"field": "blobVersionedHashes", "type": "array", "items": "string", "optional": True},
        {"field": "maxFeePerBlobGas", "type": "int64", "optional": True}
    ]
}

def hex_encode_binary_keys(d):
    for key, value in d.items():
        if value is None:
            if key in ["blockNumber", "gas", "nonce", "chainId", "maxFeePerGas", "maxPriorityFeePerGas", "value", "transactionIndex", "type", "v", "yParity"]:
                d[key] = 0  # Explicitly set 0 for INT64/INT32 fields
            else:
                d[key] = ""  # For string fields, if needed
        elif isinstance(value, HexBytes):  # Handle HexBytes
            d[key] = value.hex()
        elif isinstance(value, bytes):
            d[key] = value.hex()
        elif isinstance(value, dict):
            hex_encode_binary_keys(value)
        elif isinstance(value, list):  # Add list processing
            d[key] = [v.hex() if isinstance(v, HexBytes) else v for v in value]

    return d

def serialize_with_schema(value):
    data = hex_encode_binary_keys(dict(value))
    return json.dumps({"schema": schema, "payload": data}).encode('utf-8')

producer = KafkaProducer(
    bootstrap_servers='172.28.0.10:9092',
    value_serializer=serialize_with_schema,
    key_serializer=lambda k: k.encode('utf-8')
)

logger.info("Initializing Kafka producer with bootstrap_servers='172.28.0.10:9092'")

w3 = Web3(HTTPProvider("https://eth-mainnet.g.alchemy.com/v2/2wrUporcMxcIMvRrpuVaBYWFmeh_Mo7y"))
logger.info(f"Connected to Ethereum: {w3.is_connected()}")

while True:
    logger.info("Getting latest block number...")
    last_block_number = w3.eth.get_block_number()
    logger.info(f"Last block number: {last_block_number}")

    trx_count = w3.eth.get_block_transaction_count(last_block_number)
    logger.info(f"Transaction count: {trx_count}")

    trx = w3.eth.get_transaction_by_block(last_block_number, 0)
    trx = dict(trx)
    if 'accessList' in trx:
        del trx['accessList']

    try:
        logger.info("Sending transaction to Kafka...")
        future = producer.send('ethereum', value=trx, key=str(trx['hash'].hex()))
        record_metadata = future.get(timeout=10)
        logger.info(f"Transaction sent to Kafka: Topic={record_metadata.topic}, Partition={record_metadata.partition}, Offset={record_metadata.offset}")
    except Exception as e:
        logger.error(f"Failed to send transaction to Kafka: {e}")
        logger.error(traceback.format_exc())

    producer.flush()
    logger.info("Producer flushed")
    break
