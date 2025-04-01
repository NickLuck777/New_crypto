FROM bitnami/kafka:latest

USER root
COPY kafka-setup.sh /usr/local/bin/kafka-setup.sh
RUN chmod +x /usr/local/bin/kafka-setup.sh

COPY get_eth_data_1_msg.py /usr/local/bin/get_eth_data_1_msg.py
RUN chmod +x /usr/local/bin/get_eth_data_1_msg.py

COPY get_eth_data.py /usr/local/bin/get_eth_data.py
RUN chmod +x /usr/local/bin/get_eth_data.py

# Установка Python и создание виртуального окружения
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Создание и активация виртуального окружения
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Установка Python-библиотек в виртуальное окружение
RUN pip install web3 kafka-python
RUN mkdir -p /usr/local/bin/logs
