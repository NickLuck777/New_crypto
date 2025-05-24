from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.hooks.base import BaseHook
from datetime import datetime

import logging
import clickhouse_connect
import pandas as pd

def get_ch_client():
    con = BaseHook.get_connection('clickhouse_conn')
    client = clickhouse_connect.get_client(host=con.host,
                                           port=con.port)
    return client


def move_trx():
    
    logging.info('Moving transactions data from Postgres to Clickhouse...')

    try:
        logging.info('Fetching data from Postgres into Pandas dataframe...')
        # There should be "<" instead of "<="  to move the data only for the previous day by design for the "prod" flow.
        # But to see result right after the first run of the flow we need to move the data for the current day.
        # Because this dag is scheduled to run daily at 00:00. So, we need manually run the dag to move the data for the current day.
        pandas_df = PostgresHook('postgres_con').get_pandas_df("select * from eth_transactions where date_trunc('day', timestamp) <= current_date")
        logging.info(f'The Pandas dataframe with eth_transactions data has been created with {len(pandas_df)} rows.')
    except Exception as e:
        logging.error(f"Failed to fetch data from Postgres: {e}")
        raise

    try:
        logging.info('Connecting to Clickhouse...')
        client = get_ch_client()
        logging.info('The connection to Clickhouse has been established.')
    except Exception as e:
        logging.error(f"Failed to connect to Clickhouse: {e}")
        raise

    try:
        logging.info('Transforming None from blobVersionedHashes to empty list...')
        pandas_df['blobVersionedHashes'] = pandas_df['blobVersionedHashes'].apply(lambda x: [] if x is None else list(x))
        logging.info('The None from blobVersionedHashes has been transformed to empty list.')
    except Exception as e:
        logging.error(f"Failed to transform None from blobVersionedHashes to empty list: {e}")
        raise

    try:
        logging.info('Inserting data into Clickhouse table etherium_transactions...')
        client.insert_df(df=pandas_df,
                         database='blockchain_db',
                         table='etherium_transactions',
                         column_names=['timestamp', 'type', 'chainId', 'nonce', 'gas', 'maxFeePerGas', 'maxPriorityFeePerGas', 
                                    'to', 'value', 'input', 'r', 's', 'yParity', 'v', 'hash', 'blockHash', 'blockNumber', 
                                    'transactionIndex', 'from', 'gasPrice', 'blobVersionedHashes', 'maxFeePerBlobGas'])
        logging.info('The data has been inserted into Clickhouse table etherium_transactions.')
    except Exception as e:
        logging.error(f"Failed to insert data into Clickhouse: {e}")
        raise

    logging.info('Closing the Clickhouse connection...')
    client.close()
    logging.info('The Clickhouse connection has been closed.')

def move_news():
    
    logging.info('Moving news data from Postgres to Clickhouse...')

    try:
        logging.info('Fetching data from Postgres into Pandas dataframe...')    
        # There should be "<" instead of "<="  to move the data only for the previous day by design for the "prod" flow.
        # But to see result right after the first run of the flow we need to move the data for the current day.
        # Because this dag is scheduled to run daily at 00:00. So, we need manually run the dag to move the data for the current day.
        pandas_df = PostgresHook('postgres_con').get_pandas_df("select * from crypto_news where date_trunc('day', insertion_date) <= current_date")
        logging.info(f'The Pandas dataframe with crypto_news data has been created with {len(pandas_df)} rows.')
    except Exception as e:
        logging.error(f"Failed to fetch data from Postgres: {e}")
        raise

    try:
        logging.info('Connecting to Clickhouse...')
        client = get_ch_client()
        logging.info('The connection to Clickhouse has been established.')
    except Exception as e:
        logging.error(f"Failed to connect to Clickhouse: {e}")
        raise

    try:
        logging.info('Inserting data into Clickhouse table crypto_news...')
        client.insert_df(df=pandas_df,
                         database='blockchain_db',
                         table='crypto_news',
                         column_names=['id', 'title', 'published', 'sentiment', 'insertion_date'])
        logging.info('The data has been inserted into Clickhouse table crypto_news.')
    except Exception as e:
        logging.error(f"Failed to insert data into Clickhouse: {e}")
        raise

    logging.info('Closing the Clickhouse connection...')
    client.close()
    logging.info('The Clickhouse connection has been closed.')


def purge_trx():
    try:
        logging.info('Purging the data from Postgres...')
        PostgresHook('postgres_con').run("delete from eth_transactions where date_trunc('day', timestamp) < current_date")
        logging.info('The data has been purged from Postgres.')
    except Exception as e:
        logging.error(f"Failed to purge data from Postgres: {e}")
        raise

def purge_news():
    try:
        logging.info('Purging the data from Postgres...')
        PostgresHook('postgres_con').run("delete from crypto_news where date_trunc('day', insertion_date) < current_date")
        logging.info('The data has been purged from Postgres.')
    except Exception as e:
        logging.error(f"Failed to purge data from Postgres: {e}")
        raise


default_args = {
    "owner": "user",
    "retries": 0,
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False
}
    
with DAG(
    dag_id='DATA_MOVER',
    schedule_interval='@daily',
    start_date= datetime(2025, 5, 20),
    description='DAG for moving data from Postgres to Clickhouse',
    default_args=default_args,
    catchup=False,
    max_active_runs=1,
    is_paused_upon_creation=False) as dag:

    start = EmptyOperator(task_id='start')

    move_trx = PythonOperator(
        task_id='move_trx',
        python_callable=move_trx
    )
    
    purge_trx = PythonOperator(
        task_id='purge_trx',
        python_callable=purge_trx
    )
    
    move_news = PythonOperator(
        task_id='move_news',
        python_callable=move_news
    )
    
    purge_news = PythonOperator(
        task_id='purge_news',
        python_callable=purge_news
    )
    
    end = EmptyOperator(task_id='end')

start >> move_trx >> purge_trx >> end
start >> move_news >> purge_news >> end