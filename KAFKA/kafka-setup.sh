#!/bin/bash
echo "Waiting for Kafka to start..."
sleep 10

# Удаление существующих топиков Kafka Connect
echo "Deleting existing Kafka Connect topics if they exist..."
kafka-topics.sh --delete --topic connect-configs --bootstrap-server kafka:9092 --if-exists
kafka-topics.sh --delete --topic connect-offsets --bootstrap-server kafka:9092 --if-exists
kafka-topics.sh --delete --topic connect-status --bootstrap-server kafka:9092 --if-exists
kafka-topics.sh --delete --topic bitcoin --bootstrap-server kafka:9092 --if-exists
kafka-topics.sh --delete --topic solana --bootstrap-server kafka:9092 --if-exists

# Ожидание завершения удаления топиков
sleep 5
echo "Deleted existing Kafka Connect topics."

# Создание топиков для данных
echo "Creating data topics..."

kafka-topics.sh --create --topic ethereum --bootstrap-server kafka:9092 --partitions 1 --replication-factor 1 --if-not-exists
kafka-topics.sh --create --topic ethereum_clickhouse --bootstrap-server kafka:9092 --partitions 1 --replication-factor 1 --if-not-exists

# Создание топиков для Kafka Connect с правильной политикой очистки
echo "Creating Kafka Connect topics with compact cleanup policy..."
kafka-topics.sh --create --topic connect-configs --bootstrap-server kafka:9092 --partitions 1 --replication-factor 1 --if-not-exists --config cleanup.policy=compact
kafka-topics.sh --create --topic connect-offsets --bootstrap-server kafka:9092 --partitions 1 --replication-factor 1 --if-not-exists --config cleanup.policy=compact
kafka-topics.sh --create --topic connect-status --bootstrap-server kafka:9092 --partitions 1 --replication-factor 1 --if-not-exists --config cleanup.policy=compact
kafka-topics.sh --create --topic ethereum-dlq --bootstrap-server kafka:9092 --partitions 1 --replication-factor 1 --if-not-exists --config cleanup.policy=compact

echo "Kafka topics created successfully."

# Run the get data script for ETH
python3 /usr/local/bin/get_eth_data.py