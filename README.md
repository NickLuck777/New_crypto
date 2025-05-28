# My Pet Crypto Project

## Project Overview

This project is designed for collecting, processing, and analyzing data related to cryptocurrencies and blockchain technologies, specifically focusing on Ethereum. It utilizes Apache Airflow for workflow management, gathers Ethereum transaction data and RSS news feeds, processes them, and forwards the data to various storage and analysis systems such as Kafka, MongoDB, ClickHouse, etc.

Key components of the project:
- **Ethereum Data Collection**: A script to fetch transaction data from the Ethereum blockchain using Web3.py.
- **RSS News Processing**: An Airflow DAG to parse RSS feeds, perform sentiment analysis on news, and store the results.
- **Data Storage and Messaging**: Integration with Kafka for messaging, MongoDB for document storage, and PostgreSQL for visualization and transfer data to ClickHouse.
- **Data Visualization**: Grafana dashboards organized by tags (Kafka, PostgreSQL, ETH) for monitoring system performance and analyzing crypto data.

## System Architecture

The project follows a modern microservices architecture with the following data flow:

1. **Data Collection**:
   - Ethereum transaction data is collected using Web3.py and sent to Kafka topics
   - RSS news feeds are processed through Airflow, analyzed for sentiment, and stored in PostgreSQL

2. **Data Processing**:
   - Kafka Connect moves data from Kafka to PostgreSQL for operational storage
   - Airflow DAGs (DATA_MOVER_DAG) transfer data from PostgreSQL to ClickHouse for analytical processing

3. **Data Storage**:
   - PostgreSQL stores operational data (transactions, news)
   - MongoDB stores raw document data (news articles)
   - ClickHouse stores analytical data for high-performance queries, used as a data warehouse.

4. **Monitoring & Visualization**:
   - Prometheus collects metrics from Kafka, PostgreSQL, and other services
   - Grafana provides dashboards for system monitoring and data analysis

## Technologies Used

- **Python** (version 3.10): The primary programming language for scripting and data processing.
- **Apache Airflow**: For orchestrating complex data pipelines and scheduling tasks.
- **Docker**: Containerization of services for consistent development and deployment environments.
- **ClickHouse**: A columnar database for analytical data processing.
- **MongoDB**: A NoSQL database for storing unstructured data.
- **Kafka**: A distributed streaming platform for handling real-time data feeds.
- **Kafka Connect**: A tool for streaming data between Kafka and other systems.
- **Redis**: A key-value store for caching and session management.
- **RabbitMQ**: A message broker for queuing tasks.
- **Grafana**: A visualization and monitoring platform for monitoring and analyzing data.
- **Prometheus**: A monitoring system and time series database.
- **PostgreSQL**: A relational database for storing structured data.

## Airflow DAGs

The project includes several Airflow DAGs for different data processing tasks:

1. **GET_ETH_DAG**: Runs every minute to collect Ethereum transaction data and send it to Kafka.
2. **RSS_DAG**: Scheduled every 15 minutes to collect news from RSS feeds, performs sentiment analysis, and stores results in PostgreSQL and MongoDB.
3. **DATA_MOVER_DAG**: Scheduled daily job that moves data from PostgreSQL to ClickHouse for analytical purposes and performs cleanup.

## Monitoring Setup

The project includes a comprehensive monitoring stack:

- **Prometheus**: Collects metrics from all services
- **Grafana**: Provides dashboards organized by tags:
  - Kafka dashboards for monitoring message throughput and broker health
  - PostgreSQL dashboards for database performance metrics
  - ETH dashboards for blockchain transaction analysis

## Python Libraries and Versions

Below is a list of key Python libraries used in this project along with their versions:

- `apache-airflow-providers-mongo` (version 5.0.1): For MongoDB integration with Airflow.
- `apache-airflow-providers-redis` (version 4.0.1): For Redis integration with Airflow.
- `Telethon` (version 1.39.0): For interacting with Telegram API.
- `transformers` (version 4.49.0): For natural language processing tasks like sentiment analysis.
- `pika` (version 1.3.2): For interacting with RabbitMQ.
- `pendulum` (version 3.0.0): For datetime operations.
- `feedparser` (version 6.0.11): For parsing RSS feeds.
- `web3` (version 7.9.0): For interacting with the Ethereum blockchain.
- `kafka-python` (version 2.1.2): For interacting with Kafka.
- `hexbytes` (version 1.3.0): For handling hexadecimal byte strings.
- `pymongo` (version 4.11.3): For interacting with MongoDB.
- `torch` (version 2.6.0): For machine learning operations (using for sentiment analysis).
- `pandas` (version 2.2.3): For data manipulation and analysis.
- `clickhouse-connect` (version 0.8.15): For connecting to and querying ClickHouse.
- `inflection` (version 0.5.1): For string transformation (e.g., converting column names).
- `huggingface-hub` (version 0.30.1): For loading and managing models from the Hugging Face Hub.

## Setup and Installation

1. **Clone the Repository**: 
   ```bash
   git clone https://github.com/NickLuck777/New_crypto.git
   ```

2. **Docker Setup**: 
Ensure Docker and Docker Compose are installed on your system. Then, build and run the containers:

   ```bash
   cd New_crypto
   docker compose up -d --build
   ```

P.S. airflow-custom image creation may take a while (PyTorch is heavy). Please, be patient.

3. **Access Airflow UI**: 
Once the containers are up, access the Airflow web interface at `http://localhost:8080`. 
Default credentials are username: `airflow`, password: `airflow`.

4. **Configure Airflow Variables and Connections**: 
The Airflow variables and connections are already configured in the `connections.json` and `variables.json` files and imported on start.

5. **Run Airflow DAGs**: 
RSS_DAG and GET_ETH_DAG will be start automatically on start. 
DATA_MOVER_DAG scheduled to run daily at 00:00 but to see the result of the work of this dag we need to manually run it.

6. **Check the results**

To check the results of the work of the dags we can use Grafana dashboards or check the tables in the MongoDB,Postgres, Clickhouse databases.
Access Grafana at http://localhost:3000/dashboards
Default credentials are username: `admin`, password: `admin`.

Access Prometheus at http://localhost:9090/

## Project Structure

- `dags/`: Contains Airflow DAG definitions for workflows.
- `PyCode/`: Python scripts for data collection and processing.
- `DATABASE/CLICKHOUSE/init/`: Initialization scripts for ClickHouse database setup.
- `DATABASE/POSTGRES/`: PostgreSQL database setup scripts.
- `GRAFANA/`: Configuration files for Grafana dashboards.
- `KAFKA/`: Scripts and configuration files for Kafka setup.
- `KAFKA-CONNECT/`: Scripts and configuration files for Kafka Connect setup.

- `docker-compose.yml`: Configuration file for Docker services.
- `Dockerfile`: Custom Docker image definition for Airflow with additional dependencies.
- `requirements.txt`: Python dependencies for the project.
- `README.md`: Project documentation.
- `connections.json`: Airflow connections configuration.
- `variables.json`: Airflow variables configuration.
- `jmx_prometheus_javaagent.jar`: JMX agent for Prometheus metrics collection.
- `jmx_config.yml`: JMX configuration for Prometheus metrics collection.
- `prometheus.yml`: Prometheus configuration file.

## Database Structures

### ClickHouse Tables

- **blockchain_db**: Database name for ClickHouse.

- **etherium_transactions**: Stores Ethereum transaction data fetched from the blockchain.

- **agg_sender_values_tbl**: Stores aggregated values for each sender calculated by `agg_sender_values_mv`.

- **agg_sender_values_mv**: Materialized view for aggregated values for each sender calculated from `etherium_transactions`.
Check the query below to see the result:
select date, 
	   countMerge(trx_count),
       sumMerge(gas),
       sumMerge("maxFeePerGas"),
       sumMerge("maxPriorityFeePerGas"),
       sumMerge(value),
       sumMerge("gasPrice")       
  from agg_sender_values_mv group by date;

- **sum_all_values_tbl**: Stores sum of all values calculated by `sum_all_values_mv`.

- **sum_all_values_mv**: Materialized view for sum of all values calculated from `etherium_transactions`.

- **crypto_news**: Contains processed RSS news data with sentiment analysis results.

### PostgreSQL Tables

- **blockchain_db**: Database name for PostgreSQL.

- **eth_transactions**: Stores Ethereum transaction data fetched from the blockchain via Kafka-connect.

- **crypto_news**: Stores processed RSS news data with sentiment analysis results.

### MongoDB Collections

- **RSS**: Stores raw and processed RSS news items for flexible querying and archival.

## Usage

- **Ethereum Data Collection**: 
The script `get_eth_data.py` connects to an Ethereum node via Alchemy API, fetches the latest block transactions, and sends them to Kafka. Kafka Connect forwards the data to PostgreSQL.

- **RSS News Processing**: 
The `RSS_DAG.py` DAG periodically fetches news from configured RSS feeds, processes them for sentiment analysis using a transformers model, transforms the data, and stores it in MongoDB and PostgreSQL.

- **Data Movement**:
The `DATA_MOVER_DAG.py` DAG moves data from PostgreSQL to ClickHouse for analytical processing and performs cleanup of processed data to maintain database performance.

## Grafana Dashboards

The project includes several Grafana dashboards for monitoring and analysis, organized by tags:

### ETH Dashboards
- **Common network activity**: Displays Ethereum network metrics like average block time and transaction counts
- **Blob-transactions monitoring**: Focuses on EIP-4844 blob transactions
- **Gas and transactions price analysis**: Analyzes gas prices and transaction costs
- **User behavior and smart-contracts analysis**: Examines user interactions with smart contracts
- **Pipeline health check**: Monitors the overall health of the data pipeline

### Kafka Dashboards
- **Kafka Exporter Overview**: Monitors Kafka broker health, message throughput, and consumer groups

### PostgreSQL Dashboards
- **PostgreSQL Exporter**: Provides detailed metrics about database performance
- **News sentiment**: Analyzes sentiment trends in crypto news

