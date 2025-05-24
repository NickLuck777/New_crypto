from kafka import KafkaConsumer, TopicPartition

KAFKA_BROKER = '172.28.0.10:9092'  # или IP контейнера, если запускаешь с хоста
TOPIC = 'ethereum'

consumer = KafkaConsumer(bootstrap_servers=KAFKA_BROKER)

partitions = consumer.partitions_for_topic(TOPIC)
if partitions is None:
    print(f"❌ Топик '{TOPIC}' не найден.")
    exit(1)

total_messages = 0

for partition in partitions:
    tp = TopicPartition(TOPIC, partition)
    consumer.assign([tp])

    consumer.seek_to_beginning(tp)
    start_offset = consumer.position(tp)

    consumer.seek_to_end(tp)
    end_offset = consumer.position(tp)

    count = end_offset - start_offset
    print(f"🧩 Партиция {partition}: {count} сообщений")
    total_messages += count

print(f"\n✅ Всего сообщений в топике '{TOPIC}': {total_messages}")
consumer.close()
