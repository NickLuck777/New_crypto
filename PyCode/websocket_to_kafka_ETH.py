import websocket
import json
from kafka import KafkaProducer
import traceback
import time

# Настройка Kafka Producer с дополнительными параметрами для отладки
producer = KafkaProducer(
    bootstrap_servers=['127.0.0.1:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    acks='all',  # Ждем подтверждения от всех реплик
    retries=5,   # Количество повторных попыток
    request_timeout_ms=60000,  # Увеличиваем таймаут до 60 секунд
    api_version_auto_timeout_ms=60000,
    max_block_ms=60000,  # Максимальное время блокировки
    reconnect_backoff_ms=1000,  # Время между повторными попытками подключения
    reconnect_backoff_max_ms=10000  # Максимальное время между повторными попытками
)

def on_message(ws, message):
    print(f"Received message: {message}")  # Печатаем только начало сообщения
    
    # Отправляем сообщение в Kafka
    try:
        data = json.loads(message)
        print(f"Parsed JSON data: {json.dumps(data)}")
        
        print("Sending to Kafka topic 'ethereum'...")
        future = producer.send('ethereum', value=data)
        
        # Добавляем проверку успешной отправки
        try:
            record_metadata = future.get(timeout=10)
            print(f"Message sent to Kafka: Topic={record_metadata.topic}, Partition={record_metadata.partition}, Offset={record_metadata.offset}")
        except Exception as e:
            print(f"Failed to send message to Kafka: {e}")
            print(traceback.format_exc())
            
        producer.flush()
        print("Producer flushed")
    except Exception as e:
        print(f"Error processing message: {e}")
        print(traceback.format_exc())

def on_error(ws, error):
    print(f"Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print(f"Connection closed: {close_status_code} - {close_msg}")

def on_open(ws):
    print("Connection opened")
    # Подписка на транзакции Ethereum

    request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "eth_subscribe",
                "params": [
                    "alchemy_minedTransactions",
                    {
                        "includeRemoved": False,
                        "hashesOnly": True
                    }
                ]
            }

    subscribe_msg = json.dumps(request)
    ws.send(subscribe_msg)
    print(f"Sent subscription: {subscribe_msg}")

if __name__ == "__main__":
    # Подключение напрямую к WebSocket API Ethereum
    ws = websocket.WebSocketApp("wss://eth-mainnet.g.alchemy.com/v2/2wrUporcMxcIMvRrpuVaBYWFmeh_Mo7y",
                              on_open=on_open,
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)
    
    ws.run_forever()
