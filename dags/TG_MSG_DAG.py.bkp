from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.utils.task_group import TaskGroup
from airflow.providers.mongo.hooks.mongo import MongoHook
from airflow.providers.redis.hooks.redis import RedisHook
from airflow.hooks.base import BaseHook
from airflow.models import Variable

from telethon.sync import TelegramClient
from transformers import pipeline
from pika.credentials import PlainCredentials
from datetime import datetime

import json
import pendulum
import pika
import logging

con = BaseHook.get_connection('rabbitmq_conn')
creds = PlainCredentials(username=con.login, password=con.password)

queue_name = Variable.get('rmq_tg_queue')
collection_name = Variable.get('mongo_tg_collection')
api_id = Variable.get('tg_api_id')
api_hash = Variable.get('tg_api_hash')
channels = json.loads(Variable.get('tg_channels'))
posts_limit = Variable.get('tg_posts_limit')


def get_posts():
    """Fetch posts from Telegram channels and publish to RabbitMQ queue"""
    message_count = 0
    logging.info("Starting Telegram posts collection")
    try:
        with TelegramClient('Get_msg', api_id, api_hash) as tg_client:
            logging.info("Connected to Telegram API")
            try:
                with pika.BlockingConnection(pika.ConnectionParameters(host=con.host,
                                                                   port=con.port,
                                                                   virtual_host='/',
                                                                   credentials=creds)) as rmq_con:
                    logging.info("Connected to RabbitMQ")
                    redis_client = RedisHook(redis_conn_id='redis_conn').get_conn()
                    logging.info("Connected to Redis")
                    
                    # Process each channel in the configuration
                    for channel in channels:
                        logging.info(f"Processing Telegram channel: {channel}")
                        try:
                            # Get the last processed message ID from Redis
                            last_msg_id = int(redis_client.get(channel + '_last_id') or 0)
                            logging.info(f"Last processed message ID for {channel}: {last_msg_id}")
                            
                            # Fetch messages from the channel
                            messages = tg_client.get_messages(channel, limit=posts_limit)
                            logging.info(f"Retrieved {len(messages)} messages from {channel}")

                            # Update the last message ID in Redis if we have messages
                            if messages and messages[0].id is not None:
                                redis_client.set(channel + '_last_id', messages[0].id)
                                logging.info(f"Updated last message ID for {channel} to {messages[0].id}")

                            # Process each message
                            for msg in messages:
                                if msg.id > last_msg_id:
                                    logging.debug(f"Processing new message {msg.id} from {channel}")
                                    json_msg = json.dumps({'id': msg.id,
                                                       'date': str(msg.date),  # Convert datetime to string for JSON
                                                       'text': msg.text})

                                    # Publish message to RabbitMQ
                                    channel_rmq = rmq_con.channel()
                                    channel_rmq.queue_declare(queue=queue_name)
                                    channel_rmq.basic_publish(exchange='', routing_key=queue_name, body=json_msg)
                                    message_count += 1
                                    logging.debug(f"Published message {msg.id} to RabbitMQ")
                                else:
                                    logging.debug(f"Skipping already processed message {msg.id}")
                        except Exception as e:
                            logging.error(f"Error processing channel {channel}: {e} (Type: {type(e).__name__})")
                    
                    # Store the total message count in Redis
                    redis_client.set('message_count', message_count)
                    logging.info(f"Successfully published {message_count} messages to RabbitMQ")
            except pika.exceptions.AMQPConnectionError as e:
                logging.error(f"RabbitMQ connection error: {e}")
                raise  # Re-raise the exception to fail the task
            except Exception as e:
                logging.error(f"Error in RabbitMQ or Redis operations: {e} (Type: {type(e).__name__})")
                raise  # Re-raise the exception to fail the task
    except Exception as e:
        logging.error(f"Telegram API connection error: {e} (Type: {type(e).__name__})")
        raise  # Re-raise the exception to fail the task


def process_posts():
    """Process posts from RabbitMQ queue, perform sentiment analysis, and store in MongoDB"""
    
    def action_on_msg(ch, method, properties, body):
        """Callback function for processing each message from RabbitMQ"""
        # Use nonlocal to modify variables from the outer scope
        nonlocal message_count, messages, collection, sentiment_model

        try:
            # Parse the message JSON
            msg = json.loads(body.decode('utf-8'))
            logging.debug(f"Received message from RabbitMQ: {msg.get('id')}")
            
            try:
                # Perform sentiment analysis on the message text
                content_value = msg.get("text", "")
                if content_value:  # Analyze only if there is content
                    msg['sentiment'] = sentiment_model(content_value)
                    logging.debug(f"Sentiment analysis completed for message {msg.get('id')}")
                else:
                    logging.warning(f"No content found for sentiment analysis in message {msg.get('id', 'N/A')}")
                    msg['sentiment'] = None
            except Exception as e:
                logging.error(f"Error during sentiment analysis for message {msg.get('id', 'N/A')}: {e}")
                msg['sentiment'] = None  # Assign default value

            # Check if message already exists in MongoDB
            msg_id = msg.get('id')
            if msg_id:
                if not collection.find_one({'id': msg_id}, {'_id': 1}):  # Query only _id for efficiency
                    messages.append(msg)
                    logging.debug(f"Added message {msg_id} to batch for MongoDB insertion")
                else:
                    logging.info(f"Message with id {msg_id} already exists. Skipping.")
            else:
                logging.warning("Received message without id. Skipping.")

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
                        logging.info("MongoDB insertion completed successfully")
                        messages.clear()  # Clear after successful insertion
                    except Exception as e:
                        logging.error(f"Error inserting messages into MongoDB: {e} (Type: {type(e).__name__})")
                else:
                    logging.info("No new messages to insert.")
                
                try:
                    logging.info("Stopping RabbitMQ consumer...")
                    ch.stop_consuming()
                    logging.info("Stopped consuming RabbitMQ messages.")
                except Exception as e:
                    logging.warning(f"Failed to stop consumer (may be expected if connection is closed): {e}")

    try:
        logging.info("Starting Telegram posts processing")
        
        # Initialize sentiment analysis model
        logging.info("Initializing sentiment analysis model...")
        sentiment_model = pipeline('sentiment-analysis')
        logging.info("Sentiment analysis model loaded.")
        
        # Get message count from Redis
        redis_conn = RedisHook(redis_conn_id='redis_conn').get_conn()
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
        
        # Connect to MongoDB
        mongo_conn = MongoHook(mongo_conn_id='mongo_conn').get_conn()
        collection = mongo_conn['DB'][collection_name]
        logging.info(f"Connected to MongoDB collection: DB.{collection_name}")
        
        # Initialize messages list
        messages = []

        # Process messages if any are expected
        if message_count > 0:
            logging.info("Connecting to RabbitMQ to consume messages")
            with pika.BlockingConnection(pika.ConnectionParameters(host=con.host,
                                                               port=con.port,
                                                               virtual_host='/',
                                                               credentials=creds)) as rmq_con:
                channel = rmq_con.channel()
                # Make sure the queue exists before consuming
                channel.queue_declare(queue=queue_name, durable=False)
                channel.basic_consume(queue=queue_name, on_message_callback=action_on_msg, auto_ack=True)
                logging.info(f"Starting RabbitMQ consumer on queue '{queue_name}'. Expecting {message_count} messages...")
                channel.start_consuming()
                logging.info("RabbitMQ consumption completed.")
        else:
            logging.info("No messages expected (message_count=0). Skipping RabbitMQ consumption.")
    
    except Exception as e:  # Catch any Redis, MongoDB, or RabbitMQ errors
        logging.error(f"Unexpected error in process_posts: {e} (Type: {type(e).__name__})")
        raise  # Re-raise the exception to fail the task


default_args = {
    "owner": "user",
    "retries": 0,
    "catchup": False,
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False
}

with DAG(dag_id='Telegram',
         start_date=datetime(2025, 1, 1, tzinfo=pendulum.timezone('Europe/Moscow')),
         schedule_interval="1 * * * *",
         description='DAG for Telegram ETL',
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

    get_posts = PythonOperator(
        task_id='get_posts',
        python_callable=get_posts
    )

    process_posts = PythonOperator(
        task_id='process_posts',
        python_callable=process_posts
    )

    end = EmptyOperator(task_id='end')

start >> init >> get_posts >> process_posts >> end
