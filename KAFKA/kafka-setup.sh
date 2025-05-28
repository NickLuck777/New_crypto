#!/bin/bash
echo "Waiting for Kafka to start..."
sleep 10

# Create data topics
echo "Creating data topics..."

kafka-topics.sh --create --topic ethereum --bootstrap-server kafka:9092 --partitions 1 --replication-factor 1 --if-not-exists
kafka-topics.sh --create --topic ethereum-dlq --bootstrap-server kafka:9092 --partitions 1 --replication-factor 1 --if-not-exists --config cleanup.policy=compact

echo "Kafka topics created successfully."