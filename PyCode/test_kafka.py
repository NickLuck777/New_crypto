import json
from kafka import KafkaProducer
import time

# Тестируем разные варианты подключения
hosts = [
    'localhost:9092',
    '127.0.0.1:9092',
    'kafka:9092'
]

for host in hosts:
    print(f"\nПробуем подключиться к {host}...")
    try:
        # Настройка Kafka Producer
        producer = KafkaProducer(
            bootstrap_servers=[host],
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            # Добавляем таймаут для быстрого определения проблемы
            api_version_auto_timeout_ms=5000,
            request_timeout_ms=5000,
            metadata_max_age_ms=5000
        )
        
        # Отправляем тестовое сообщение
        test_data = {"test": f"message from {host} at {time.time()}"}
        print(f"Sending: {test_data}")
        
        future = producer.send('ethereum', value=test_data)
        # Ждем подтверждения отправки
        record_metadata = future.get(timeout=5)
        print(f"Success! Message sent to: Topic={record_metadata.topic}, Partition={record_metadata.partition}, Offset={record_metadata.offset}")
        
        producer.flush()
        producer.close()
        print(f"Успешно подключились к {host}")
        
    except Exception as e:
        print(f"Ошибка при подключении к {host}: {e}")

print("\nТест завершен.")
