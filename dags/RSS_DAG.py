from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup
from airflow.providers.mongo.hooks.mongo import MongoHook
from airflow.providers.redis.hooks.redis import RedisHook
from airflow.hooks.base import BaseHook
from airflow.models import Variable

import feedparser
import pika
from pika.credentials import PlainCredentials
import json
from datetime import datetime
import pendulum
from transformers import pipeline
from transformers.models.bert import BertModel
import logging
import pymongo
import pandas as pd


rmq_con = BaseHook.get_connection('rabbitmq_conn')
creds = PlainCredentials(username=rmq_con.login, password=rmq_con.password)
queue_name = Variable.get('rmq_rss_queue')
collection_name = Variable.get('mongo_rss_collection')
rss_feeds = json.loads(Variable.get('rss_channels'))
mongo_db = Variable.get('mongo_db')


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
                if content_value:  # Analyze only if there is content
                    msg['sentiment'] = sentiment_model(content_value)
                else:
                    logging.warning(f"No content found for sentiment analysis in message {msg.get('id', 'N/A')}")
                    msg['sentiment'] = None
            except Exception as e:
                logging.error(f"Error during sentiment analysis for message {msg.get('id', 'N/A')}: {e}")
                msg['sentiment'] = None  # Assign default value

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
                        messages.clear()  # Clear after successful/attempted insertion
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
        logging.info("Initializing sentiment analysis model...")
        model = BertModel.from_pretrained('google-bert/bert-base-cased')
        sentiment_model = pipeline(task='sentiment-analysis', model=model)
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
         max_active_runs=1):
    start = EmptyOperator(task_id='start')

    with TaskGroup(group_id='init', tooltip='Importing variables and connections') as init:
        set_variables = BashOperator(
            task_id='set_variables',
            bash_command='airflow variables import /opt/airflow/variables.json'
        )

        set_connections = BashOperator(
            task_id='set_connections',
            bash_command='airflow connections import /opt/airflow/connections.json'
        )

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
