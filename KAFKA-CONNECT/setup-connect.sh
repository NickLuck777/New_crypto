#!/bin/bash
echo "Waiting for Kafka Connect to start..."
sleep 30  # Increase waiting time to 30 seconds

# Check if Kafka Connect is available
echo "Checking if Kafka Connect is available..."
MAX_ATTEMPTS=30
ATTEMPT=0
while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if curl -s http://localhost:8083/connectors >/dev/null; then
        echo "Kafka Connect is available, proceeding with connector configuration"
        break
    fi
    ATTEMPT=$((ATTEMPT+1))
    echo "Attempt $ATTEMPT/$MAX_ATTEMPTS: Kafka Connect not yet available, waiting..."
    sleep 5
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo "Kafka Connect did not become available after $MAX_ATTEMPTS attempts, exiting"
    exit 1
fi

# Register Sink connectors
echo "Configuring PostgreSQL sink connector..."
curl -X POST -H "Content-Type: application/json" --data @/etc/kafka-connect/connectors/postgres-sink.json http://localhost:8083/connectors

echo "Kafka Connect connectors configured."

# Keep the script running to prevent the container from exiting
tail -f /dev/null