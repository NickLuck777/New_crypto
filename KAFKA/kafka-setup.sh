#!/bin/bash
echo "Waiting for Kafka to start..."
sleep 10

# Delete existing Kafka Connect topics if they exist
echo "Deleting existing Kafka Connect topics if they exist..."
kafka-topics.sh --delete --topic connect-configs --bootstrap-server kafka:9092 --if-exists
kafka-topics.sh --delete --topic connect-offsets --bootstrap-server kafka:9092 --if-exists
kafka-topics.sh --delete --topic connect-status --bootstrap-server kafka:9092 --if-exists

# Wait for the deletion to complete
sleep 5
echo "Deleted existing Kafka Connect topics."

# Create data topics
echo "Creating data topics..."

kafka-topics.sh --create --topic ethereum --bootstrap-server kafka:9092 --partitions 1 --replication-factor 1 --if-not-exists

# Create Kafka Connect topics with compact cleanup policy
echo "Creating Kafka Connect topics with compact cleanup policy..."
kafka-topics.sh --create --topic connect-configs --bootstrap-server kafka:9092 --partitions 1 --replication-factor 1 --if-not-exists --config cleanup.policy=compact
kafka-topics.sh --create --topic connect-offsets --bootstrap-server kafka:9092 --partitions 1 --replication-factor 1 --if-not-exists --config cleanup.policy=compact
kafka-topics.sh --create --topic connect-status --bootstrap-server kafka:9092 --partitions 1 --replication-factor 1 --if-not-exists --config cleanup.policy=compact
kafka-topics.sh --create --topic ethereum-dlq --bootstrap-server kafka:9092 --partitions 1 --replication-factor 1 --if-not-exists --config cleanup.policy=compact

echo "Kafka topics created successfully."