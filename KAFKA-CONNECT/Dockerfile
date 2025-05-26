FROM confluentinc/cp-kafka-connect:7.9.0

USER root

# Install the necessary connectors
RUN confluent-hub install --no-prompt confluentinc/kafka-connect-jdbc:latest 

# Copy the setup script
COPY setup-connect.sh /usr/local/bin/setup-connect.sh
RUN chmod +x /usr/local/bin/setup-connect.sh

# Copy the connector configurations
COPY connectors/ /etc/kafka-connect/connectors/