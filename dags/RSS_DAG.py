from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup
from airflow.providers.mongo.hooks.mongo import MongoHook
from airflow.providers.redis.hooks.redis import RedisHook
from airflow.hooks.base import BaseHook
from airflow.models import Variable

from pika.credentials import PlainCredentials
from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer
from datetime import datetime

import feedparser
import pika
import json
import pendulum
import logging
import pymongo
import clickhouse_connect
import pandas as pd
import inflection


rmq_con = BaseHook.get_connection('rabbitmq_conn')
creds = PlainCredentials(username=rmq_con.login, password=rmq_con.password)
queue_name = Variable.get('rmq_rss_queue')
collection_name = Variable.get('mongo_rss_collection')
rss_feeds = json.loads(Variable.get('rss_channels'))
mongo_db = Variable.get('mongo_db')

def transform_rss(msgs):
    logging.info(f'Transforming messages...')
    logging.info(f'Message count: {len(msgs)}')
    try:
        df = pd.DataFrame(msgs)
    except Exception as e:
        logging.error(f"Failed to create DataFrame from messages: {e}")
        return None

    logging.info('Deleting columns...')
    try:
        df = df[['id', 'title', 'published', 'sentiment']]
    except KeyError as e:
        logging.error(f"Missing expected columns: {e}")
    logging.info('Deleting columns... done.')

    logging.info('Cast published to DateTime...')
    try:
        # Приводим первые буквы дня недели и месяца к заглавным для соответствия формату
        df['published'] = df['published'].apply(
            lambda date_string: datetime.strptime(
            ' '.join(word.capitalize() if i in [0, 2] else word for i, word in enumerate(date_string.split())).replace('gmt', '+0000').replace('GMT', '+0000'),
                '%a, %d %b %Y %H:%M:%S %z'
        ).strftime('%Y-%m-%d %H:%M:%S')
        )
    except Exception as e:
        logging.error(f"Error parsing date in 'published' column: {e}")
        df['published'] = '1970-01-01 00:00:00'  # Значение по умолчанию при ошибке
    logging.info('Cast published to DateTime... done.')

    logging.info('Casting the columns types...')
    try:
        df['published'] = pd.to_datetime(df['published'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
        df['sentiment'] = df['sentiment'].astype('float64', errors='ignore')
        df['id'] = df['id'].astype(str)
        df['title'] = df['title'].astype(str)
    except Exception as e:
        logging.error(f"Error casting column types: {e}")
    logging.info('Casting the columns types... done.')

    logging.info('Columns transformation...')
    try:
        df.columns = [inflection.underscore(col) for col in df.columns]
    except Exception as e:
        logging.error(f"Error transforming columns: {e}")
    logging.info('Columns transformation... done.')

    logging.info('Drop duplicates...')
    try:
        df.drop_duplicates(subset=['id'], inplace=True)
    except Exception as e:
        logging.error(f"Error dropping duplicates: {e}")
    logging.info('Drop duplicates... done.')

    logging.info('Fill empty values...')
    try:
        numeric_columns = df.select_dtypes(include=['int64', 'float64', 'datetime64']).columns
        string_columns = df.select_dtypes(include=['object']).columns
        df[numeric_columns] = df[numeric_columns].fillna(0)
        df[string_columns] = df[string_columns].fillna('N/A')
    except Exception as e:
        logging.error(f"Error filling empty values: {e}")
    logging.info('Fill empty values... done.')

    logging.info('Removing newlines and tabs...')
    try:
        df[string_columns] = df[string_columns].apply(lambda col: col.str.replace('\\n', ''))
        df[string_columns] = df[string_columns].apply(lambda col: col.str.replace('\\t', ' '))
        df[string_columns] = df[string_columns].apply(lambda col: col.str.replace(' {2,}', ' ', regex=True))
        df[string_columns] = df[string_columns].apply(lambda col: col.str.strip())
    except Exception as e:
        logging.error(f"Error removing newlines and tabs: {e}")
    logging.info('Removing newlines and tabs... done.')

    logging.info('Delete emodji...')
    try:
        df = df.astype(str).map(lambda x: x.encode('ascii', 'ignore').decode('ascii'))
    except Exception as e:
        logging.error(f"Error deleting emodji: {e}")
    logging.info('Delete emodji... done.')

    logging.info('To lowercase...')
    try:
        df[string_columns] = df[string_columns].apply(lambda col: col.str.lower())
    except Exception as e:
        logging.error(f"Error converting to lowercase: {e}")
    logging.info('To lowercase... done.')

    logging.info('Transforming messages... done.')
    return df

def get_news():
    message_count = 0
    redis_hook = RedisHook(redis_conn_id='redis_conn')
    try:
        with pika.BlockingConnection(pika.ConnectionParameters(host=rmq_con.host, port=rmq_con.port, virtual_host='/',
                                                               credentials=creds)) as connection:
            channel = connection.channel()
            channel.queue_declare(queue=queue_name)

            for feed_url in rss_feeds:
                try:
                    logging.info(f"Parsing RSS feed: {feed_url}")
                    feed = feedparser.parse(feed_url)
                    for entry in feed.entries:
                        try:
                            channel.basic_publish(exchange='', routing_key=queue_name, body=json.dumps(entry))
                            message_count += 1
                        except pika.exceptions.AMQPError as e:
                            logging.error(f"Error publishing message from {feed_url}: {e}")
                        except Exception as e:
                            logging.error(f"Error processing entry from {feed_url}: {entry.get('id', 'N/A')} - {e}")
                except feedparser.FeedParserError as e:
                    logging.error(f"Error parsing feed {feed_url}: {e}")
                except Exception as e:
                    logging.error(f"Unexpected error processing feed {feed_url}: {e}")

            redis_conn = redis_hook.get_conn()
            redis_conn.set('message_count', message_count)
            logging.info(f"Successfully published {message_count} messages.")

    except pika.exceptions.AMQPConnectionError as e:
        logging.error(f"RabbitMQ connection error in get_news: {e}")
        raise  # Re-raise the exception to fail the task
    except Exception as e:  # Перехватываем общее исключение для ошибок Redis или других
        logging.error(f"Redis or other error in get_news: {e} (Type: {type(e).__name__})")
        raise  # Re-raise the exception to fail the task


def process_news():
    sentiment_model = None
    message_count = 0
    messages = []
    collection = None
    redis_hook = RedisHook(redis_conn_id='redis_conn')
    mongo_hook = MongoHook(mongo_conn_id='mongo_conn')

    clickhouse_con = BaseHook.get_connection('clickhouse_conn')

    client = clickhouse_connect.get_client(host=clickhouse_con.host,
                                           port=clickhouse_con.port)

    def action_on_msg(ch, method, properties, body):

        # Use nonlocal to modify variables from the outer scope
        nonlocal message_count, messages, collection, sentiment_model

        if collection is None or sentiment_model is None:
            logging.error("Handler called before MongoDB collection or sentiment model initialization.")
            # Decide how to handle: possibly reject the message and put it back in the queue
            # For now, just decrement the counter and log the error
            message_count -= 1
            if message_count <= 0:
                try:
                    ch.stop_consuming()
                except Exception as e:
                    logging.error(f"Error stopping consumer after initialization failure: {e}")
            return

        try:
            msg = json.loads(body.decode('utf-8'))
            try:
                # Carefully handle potentially missing keys
                content_value = msg.get("title", "")

                if content_value:
                    # Анализ настроения
                    result = sentiment_model(content_value)
                    msg['sentiment'] = result[0]['score'] if result[0]['label'] == 'POSITIVE' else -result[0]['score']
                else:
                    logging.warning(f"No content found for sentiment analysis in message {msg.get('id', 'N/A')}")
                    msg['sentiment'] = None
            except Exception as e:
                logging.error(f"Error during sentiment analysis for message {msg.get('id', 'N/A')}: {e}")
                msg['sentiment'] = None    

            # Check if message already exists
            msg_id = msg.get('id')
            if msg_id:
                if not collection.find_one({'id': msg_id}, {'_id': 1}):  # Query only _id for efficiency
                    messages.append(msg)
                else:
                    logging.info(f"Message with id {msg_id} already exists. Skipping.")
            else:
                logging.warning(f"Received message without id. Skipping duplicate check and adding.")
                messages.append(msg)

        except json.JSONDecodeError as e:
            logging.error(f"Failed to decode message body: {e} Body: {body[:100]}...")  # Log part of the body
        except Exception as e:
            logging.error(f"Error processing message: {e} (Type: {type(e).__name__})")
        finally:
            # Decrement the counter even on processing error, as the message is automatically acknowledged
            message_count -= 1
            logging.debug(f"Messages remaining: {message_count}")
            if message_count <= 0:
                logging.info("All expected messages processed or counter reached zero.")
                if messages:
                    try:
                        logging.info(f"Inserting {len(messages)} new messages into MongoDB.")
                        collection.insert_many(messages, ordered=False)  # Use ordered=False to continue on duplicate errors
                        logging.info("Inserting messages into MongoDB... done.")

                    except pymongo.errors.BulkWriteError as bwe:
                        # Log details about duplicate keys and other errors
                        write_errors = bwe.details.get('writeErrors', [])
                        dup_keys = sum(1 for err in write_errors if err.get('code') == 11000)
                        other_errors = len(write_errors) - dup_keys
                        logging.warning(f"MongoDB bulk write error: {dup_keys} duplicate keys ignored. {other_errors} other errors.")
                        if other_errors > 0:
                            logging.error(f"Details about non-duplicate errors: {bwe.details}")
                        messages.clear()  # Clear the list even on errors, as we attempted to insert
                    except (pymongo.errors.ConnectionFailure, pymongo.errors.OperationFailure) as op_err:
                        logging.error(f"MongoDB connection/operation error during insert: {op_err}")
                        # Decide whether to keep messages for retry or clear them
                    except Exception as e:
                        logging.error(f"Error inserting messages into MongoDB: {e} (Type: {type(e).__name__})")

                    try:
                        df = transform_rss(messages)
                        if not df.empty:
                            logging.info("Inserting messages into ClickHouse...")
                            client.insert_df(df=df,
                                database='blockchain_db',
                                table='crypto_news',
                                column_names=['id', 'title', 'published', 'sentiment'])
                            client.close()
                            logging.info("Inserting messages into ClickHouse... done.")
                    except Exception as e:
                        logging.error(f"Error inserting messages into ClickHouse: {e} (Type: {type(e).__name__})")

                    messages.clear()  # Clear after successful/attempted insertion
                    # Decide whether to keep messages for retry or clear them
                else:
                    logging.info("No new messages to insert.")

                try:
                    logging.info("Attempting to stop RabbitMQ consumer...")
                    ch.stop_consuming()
                    logging.info("Stopped consuming RabbitMQ messages.")
                except Exception as e:
                    # This may happen if the connection is already closed, etc.
                    logging.warning(f"Failed to stop consumer (may be expected if connection is closed): {e}")

    try:
        # logging.info("Initializing sentiment analysis model...")
        # model = BertModel.from_pretrained('google-bert/bert-base-cased')
        # sentiment_model = pipeline(task='sentiment-analysis', model=model)
        # logging.info("Sentiment analysis model loaded.")

        logging.info("Initializing sentiment analysis model...")
        # Загружаем модель и токенизатор для анализа настроений
        model_name = "distilbert-base-uncased-finetuned-sst-2-english"  # Подходящая модель для sentiment-analysis
        model = AutoModelForSequenceClassification.from_pretrained(model_name)
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        sentiment_model = pipeline(task='sentiment-analysis', model=model, tokenizer=tokenizer)
        logging.info("Sentiment analysis model loaded.")

        redis_conn = redis_hook.get_conn()
        message_count_bytes = redis_conn.get('message_count')
        if message_count_bytes is None:
            logging.warning("Could not find 'message_count' in Redis. Assuming 0 messages to process.")
            message_count = 0
        else:
            try:
                message_count = int(message_count_bytes.decode('utf-8'))
            except ValueError:
                logging.error(f"Invalid value for 'message_count' in Redis: {message_count_bytes}. Assuming 0.")
                message_count = 0
        logging.info(f"Expecting {message_count} messages based on Redis counter.")

        mongo_conn = mongo_hook.get_conn()
        collection = mongo_conn[mongo_db][collection_name]
        # Test connection/authentication in advance
        collection.find_one({}, {'_id': 1})  # Simple read operation
        logging.info(f"Connected to MongoDB collection: {mongo_db}.{collection_name}")

        if message_count > 0:
            with pika.BlockingConnection(pika.ConnectionParameters(host=rmq_con.host,
                                                                   port=rmq_con.port,
                                                                   virtual_host='/',
                                                                   credentials=creds)) as connection:
                channel = connection.channel()
                # Make sure the queue exists before consuming
                channel.queue_declare(queue=queue_name, durable=False)  # Assume the queue should exist, declare defensively
                channel.basic_consume(queue=queue_name, on_message_callback=action_on_msg, auto_ack=True)
                logging.info(f"Starting RabbitMQ consumer on queue '{queue_name}'. Expecting {message_count} messages...")
                channel.start_consuming()
                logging.info("RabbitMQ consumption completed.")
        else:
            logging.info("No messages expected (message_count=0). Skipping RabbitMQ consumption.")

    except Exception as e:  # Catch any Redis, MongoDB, or RabbitMQ errors
        logging.error(f"Unexpected error in process_news: {e} (Type: {type(e).__name__})")
        raise  # Re-raise the exception to fail the task


default_args = {

    "owner": "user",
    "retries": 0,
    "catchup": False,
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False
}

with DAG(dag_id='RSS',
         start_date=datetime(2025, 1, 1, tzinfo=pendulum.timezone('Europe/Moscow')),
         schedule_interval="1 * * * *",
         description='DAG for RSS ETL',
         default_args=default_args,
         catchup=False,
         max_active_runs=1,
         is_paused_upon_creation=False):
    start = EmptyOperator(task_id='start')

    get_news = PythonOperator(
        task_id='get_news',
        python_callable=get_news
    )

    process_news = PythonOperator(
        task_id='process_news',
        python_callable=process_news
    )

    end = EmptyOperator(task_id='end')

start >> get_news >> process_news >> end
