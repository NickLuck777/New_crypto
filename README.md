# Crypto Data Collector

## Project Overview

This project uses Apache Airflow to manage workflows, collect Ethereum transaction data and RSS news feeds, process them, and send them to various data storage and analysis systems such as Kafka, MongoDB, ClickHouse, etc.

## Installation and Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/NickLuck777/New_crypto.git
   ```

2. **Run Docker Compose**:
   Make sure Docker is installed on your computer. Then run the following command:

   ```bash
   cd New_crypto
   docker compose up -d --build
   ```

P.S. The airflow-custom image takes a while to build (PyTorch is heavy). Please be patient.

## System Architecture

![System Architecture](schema.png)

## Airflow DAGs Description

The project includes several Airflow DAGs for different data processing tasks:

1. **GET_ETH_DAG**: Runs every minute to collect Ethereum transaction data and send it to Kafka.
2. **RSS_DAG**: Runs every 15 minutes to collect news from RSS feeds, perform sentiment analysis, and store results in PostgreSQL and MongoDB.
3. **DATA_MOVER_DAG**: Runs a daily task that moves data from PostgreSQL to ClickHouse for analytical purposes and cleans up processed data to maintain database performance.

## Monitoring

The project includes a comprehensive monitoring system:

- **Prometheus**: Collects metrics from all services
- **Grafana**: Provides dashboards organized by tags:
  - Kafka dashboards for monitoring throughput and broker health
  - PostgreSQL dashboards for database performance metrics
  - ETH dashboards for blockchain transaction analysis

## Usage

- **Ethereum Transaction Data Collection**:
  The `get_eth_data.py` script connects to an Ethereum node via Alchemy API, retrieves the latest block transactions, and sends them to Kafka. Kafka Connect then transfers the data to PostgreSQL.

- **RSS News Processing**:
  The `RSS_DAG.py` DAG periodically fetches news from configured RSS feeds, analyzes sentiment using transformers models, transforms the data, and saves it to MongoDB and PostgreSQL.

- **Data Movement**:
  The `DATA_MOVER_DAG.py` DAG moves data from PostgreSQL to ClickHouse for analytical purposes and cleans up processed data to maintain database performance.

**Accessing Airflow UI**:
After starting the containers, access the Airflow UI at `http://localhost:8080`.
Credentials: username: `airflow`, password: `airflow`.

**Airflow Variables and Connections Configuration**:
Airflow variables and connections are pre-configured in `connections.json` and `variables.json` files and are imported at startup.

**Running Airflow DAGs**:
RSS_DAG and GET_ETH_DAG will start automatically. DATA_MOVER_DAG is scheduled to run daily at 00:00, but you can also run it manually to see the results.

**Checking Results**

To verify the DAGs' results, you can use Grafana dashboards or check the tables in MongoDB, PostgreSQL, and ClickHouse.
Access Grafana at http://localhost:3000/dashboards
Credentials: username: `admin`, password: `admin`.

Access Prometheus at http://localhost:9090

## Grafana Dashboards

The project includes several Grafana dashboards for monitoring and analysis, organized by tags:

### ETH Dashboards
- **Common network activity**: Displays Ethereum network metrics such as average block time and transaction count
- **Blob-transactions monitoring**: Focuses on EIP-4844 blob transactions
- **Gas and transactions price analysis**: Analyzes gas prices and transaction costs
- **User behavior and smart-contracts analysis**: Examines user interactions with smart contracts
- **Pipeline health check**: Monitors overall data health

### Kafka Dashboards
- **Kafka Exporter Overview**: Monitors Kafka broker health, throughput, and consumer groups

### PostgreSQL Dashboards
- **PostgreSQL Exporter**: Provides detailed database performance metrics
- **News sentiment**: Analyzes trends in cryptocurrency news sentiment

---

# Сборщик крипто данных

## Обзор проекта

Данный проект использует Apache Airflow для управления workflow, собирает данные транзакций Ethereum и RSS-лент новостей, обрабатывает их и отправляет в разные системы хранения и анализа данных, такие как Kafka, MongoDB, ClickHouse и т.д.

## Установка и настройка

1. **Клонирование репозитория**: 
   ```bash
   git clone https://github.com/NickLuck777/New_crypto.git
   ```

2. **Запуск Docker compose**: 
Убедитесь, что Docker установлен на вашем компьютере. Затем выполните команду:

   ```bash
   cd New_crypto
   docker compose up -d --build
   ```

P.S. airflow-custom образ создается долго (PyTorch тяжелый). Пожалуйста, подождите.

## Системная архитектура

![Системная архитектура](schema.png)

##  Описание дагов Airflow

Проект включает несколько Airflow DAGs для разных задач обработки данных:

1. **GET_ETH_DAG**: Запускается каждую минуту для сбора данных транзакций Ethereum и отправки их в Kafka.
2. **RSS_DAG**: Запускается каждые 15 минут для сбора новостей из RSS-лент, анализа настроения и хранения результатов в PostgreSQL и MongoDB.
3. **DATA_MOVER_DAG**: Запускается ежедневную задачу, которая перемещает данные из PostgreSQL в ClickHouse для аналитических целей и выполняет очистку обработанных данных для поддержания производительности базы данных.

## Мониторинг

Проект включает в себя комплексную систему мониторинга:

- **Prometheus**: Собирает метрики из всех сервисов
- **Grafana**: Предоставляет дашборды, организованные по тегам:
  - Kafka dashboards для мониторинга пропускной способности и здоровья брокера
  - PostgreSQL dashboards для метрик производительности базы данных
  - ETH dashboards для анализа транзакций блокчейна

## Использование

- **Сбор данных транзакций Ethereum**: 
Скрипт `get_eth_data.py` подключается к узлу Ethereum через API Alchemy, получает последние транзакции блоков и отправляет их в Kafka. Kafka Connect передает данные в PostgreSQL.

- **Обработка новостей RSS**: 
The `RSS_DAG.py` DAG периодически получает новости из настроенных RSS-лент, анализирует настроение с помощью transformers-модели, трансформирует данные и сохраняет их в MongoDB и PostgreSQL.

- **Перемещение данных**: 
The `DATA_MOVER_DAG.py` DAG перемещает данные из PostgreSQL в ClickHouse для аналитических целей и выполняет очистку обработанных данных для поддержания производительности базы данных.

**Доступ к Airflow UI**: 
После запуска контейнеров доступ к Airflow UI осуществляется по адресу `http://localhost:8080`. 
Пользовательские данные: username: `airflow`, password: `airflow`.

**Конфигурация переменных и подключений Airflow**: 
Переменные и подключения Airflow уже настроены в файлах `connections.json` и `variables.json` и импортированы при запуске.

**Запуск Airflow DAGs**: 
RSS_DAG и GET_ETH_DAG будут запущены автоматически при запуске. 
DATA_MOVER_DAG запланирован на ежедневное выполнение в 00:00, но для просмотра результата работы этого дага нужно его запустить вручную.

**Проверка результатов**

Для проверки результатов работы дагов можно использовать дашборды Grafana или проверить таблицы в базах данных MongoDB,Postgres, Clickhouse.
Доступ к Grafana осуществляется по адресу http://localhost:3000/dashboards
Пользовательские данные: username: `admin`, password: `admin`.

Доступ к Prometheus осуществляется по адресу http://localhost:9090

## Дашборды Grafana

Проект включает несколько дашбордов Grafana для мониторинга и анализа, организованных по тегам:

### ETH дашборды
- **Common network activity**: Отображает метрики сети Ethereum, такие как среднее время блока и количество транзакций
- **Blob-transactions monitoring**: Фокусируется на транзакциях EIP-4844 blob
- **Gas and transactions price analysis**: Анализирует цены газа и стоимость транзакций
- **User behavior and smart-contracts analysis**: Исследует взаимодействие пользователей с смарт-контрактами
- **Pipeline health check**: Мониторит общее здоровье данных

### Kafka дашборды
- **Kafka Exporter Overview**: Мониторит здоровье брокера Kafka, пропускную способность и группы потребителей

### PostgreSQL дашборды
- **PostgreSQL Exporter**: Предоставляет подробные метрики о производительности базы данных
- **News sentiment**: Анализирует тенденции в настроении новостей криптовалют
