import websocket
import json
from kafka import KafkaProducer

# Настройка Kafka Producer
producer = KafkaProducer(
    bootstrap_servers=['127.0.0.1:9092'],  # Используем 127.0.0.1 вместо localhost для доступа извне Docker
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def on_message(ws, message):
    print(f"Received message: {message[:100]}...")  # Печатаем только начало сообщения
    
    # Отправляем сообщение в Kafka
    try:
        data = json.loads(message)
        producer.send('solana', value=data)
        producer.flush()
        print("Message sent to Kafka")
    except Exception as e:
        print(f"Error sending to Kafka: {e}")

def on_error(ws, error):
    print(f"Error: {error}")

def on_close(ws, close_status_code, close_msg):
    print(f"Connection closed: {close_status_code} - {close_msg}")

def on_open(ws):
    print("Connection opened")
    # Подписка на транзакции Solana

    request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "programSubscribe",
                "params": [
                    "11111111111111111111111111111111",
                    {
                    "encoding": "base64",
                    "commitment": "finalized"
                    }
                ]
            }

    subscribe_msg = json.dumps(request)
    ws.send(subscribe_msg)
    print(f"Sent subscription: {subscribe_msg}")

if __name__ == "__main__":
    # Подключение напрямую к WebSocket API Solana
    ws = websocket.WebSocketApp("wss://api.mainnet-beta.solana.com",
                              on_open=on_open,
                              on_message=on_message,
                              on_error=on_error,
                              on_close=on_close)
    
    ws.run_forever()
