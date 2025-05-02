FROM confluentinc/cp-kafka-connect:latest

USER root

# Установка необходимых коннекторов
RUN confluent-hub install --no-prompt confluentinc/kafka-connect-jdbc:latest 
#RUN confluent-hub install --no-prompt ./clickhouse-kafka-connect-v1.2.9-confluent.jar

# Копирование скрипта для автоматической настройки
COPY setup-connect.sh /usr/local/bin/setup-connect.sh
RUN chmod +x /usr/local/bin/setup-connect.sh

# Копирование конфигураций коннекторов
COPY connectors/ /etc/kafka-connect/connectors/