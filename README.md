# My Pet Crypto Project

## Project Overview

This project is designed for collecting, processing, and analyzing data related to cryptocurrencies and blockchain technologies, specifically focusing on Ethereum. It utilizes Apache Airflow for workflow management, gathers Ethereum transaction data and RSS news feeds, processes them, and forwards the data to various storage and analysis systems such as Kafka, MongoDB, and ClickHouse.

Key components of the project:
- **Ethereum Data Collection**: A script to fetch transaction data from the Ethereum blockchain using Web3.py.
- **RSS News Processing**: An Airflow DAG to parse RSS feeds, perform sentiment analysis on news, and store the results.
- **Data Storage and Messaging**: Integration with Kafka for messaging, MongoDB for document storage, and ClickHouse for analytical queries.

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
- **PostgreSQL**: A relational database for storing structured data (YandexCloud).

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

## Setup and Installation

1. **Clone the Repository**: 
   ```bash
   git clone https://github.com/NickLuck777/New_crypto.git
   cd New_crypto
   ```

2. **Docker Setup**: 
Ensure Docker and Docker Compose are installed on your system. Then, build and run the containers:

   ```bash
   cd KAFKA
   docker build -t kafka-custom .
   cd ../KAFKA-CONNECT
   docker build -t kafka-connect-custom .
   cd ../
   docker build -t airflow-custom .
   docker-compose up --build
   ```

P.S. airflow-custom image creation may take a while (PyTorch is heavy). Please, be patient.

3. **Access Airflow UI**: 
Once the containers are up, access the Airflow web interface at `http://localhost:8080`. Default credentials are username: `airflow`, password: `airflow`.

4. **Configure Variables and Connections**: 
The variables and connections are already configured in the `connections.json` and `variables.json` files and imported into Airflow.

## Project Structure

- `dags/`: Contains Airflow DAG definitions for workflows like RSS processing.
- `PyCode/`: Python scripts for data collection and processing, such as `get_eth_data.py` for Ethereum transactions.
- `clickhouse/init/`: Initialization scripts for ClickHouse database setup.
- `docker-compose.yml`: Configuration file for Docker services.
- `Dockerfile`: Custom Docker image definition for Airflow with additional dependencies.

## Database Structures

### ClickHouse Tables

- **blockchain_db**: Database name for ClickHouse.

- **kafka_etherium**: Table with kafka engine for Ethereum transactions in ClickHouse (consumer).

- **ethereum_consumer**: Materialized view for Ethereum transactions in ClickHouse based on `kafka_etherium`. Populates `etherium_transactions`.

- **etherium_transactions**: Stores Ethereum transaction data fetched from the blockchain.

- **crypto_news**: Contains processed RSS news data with sentiment analysis results.

### PostgreSQL Tables

- **eth_transactions**: Stores Ethereum transaction data fetched from the blockchain via Kafka-connect.

### MongoDB Collections

- **RSS**: Stores raw and processed RSS news items for flexible querying and archival.

## Usage

- **Ethereum Data Collection**: 
The script `get_eth_data.py` connects to an Ethereum node via Alchemy API, fetches the latest block transactions, and sends them to Kafka. Kafka sends the data to ClickHouse and PostgreSQL (YandexCloud).

- **RSS News Processing**: 
The `RSS_DAG.py` DAG periodically fetches news from configured RSS feeds, processes them for sentiment analysis using a transformers model, transforms the data, and stores it in MongoDB and ClickHouse.
