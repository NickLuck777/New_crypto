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

con = BaseHook.get_connection('rabbitmq_conn')
creds = PlainCredentials(username=con.login, password=con.password)

queue_name = Variable.get('rmq_tg_queue')
collection_name = Variable.get('mongo_tg_collection')
api_id = Variable.get('tg_api_id')
api_hash = Variable.get('tg_api_hash')
channels = json.loads(Variable.get('tg_channels'))
posts_limit = Variable.get('tg_posts_limit')


def get_posts():
    message_count = 0
    with TelegramClient('Get_msg', api_id, api_hash) as tg_client:
        with pika.BlockingConnection(pika.ConnectionParameters(host=con.host,
                                                               port=con.port,
                                                               virtual_host='/',
                                                               credentials=creds)) as rmq_con:
            redis_client = RedisHook(redis_conn_id='redis_conn').get_conn()
            for channel in channels:
                last_msg_id = int(redis_client.get(channel + '_last_id') or 0)
                messages = tg_client.get_messages(channel, limit=posts_limit)

                if messages[0].id is not None:
                    redis_client.set(channel + '_last_id', messages[0].id)

                for msg in messages:
                    if msg.id > last_msg_id:
                        json_msg = json.dumps({'id': msg.id,
                                               'date': msg.date,
                                               'text': msg.text})

                    channel = rmq_con.channel()
                    channel.queue_declare(queue=queue_name)

                    channel.basic_publish(exchange='', routing_key=queue_name, body=json_msg)
                    message_count += 1

            redis_client.set('message_count', message_count)


def process_posts():
    def action_on_msg(ch, method, properties, body):
        nonlocal message_count, messages, collection

        msg = json.loads(body.decode('utf-8'))
        sentiment_model = pipeline('sentiment-analysis')
        msg['sentiment'] = sentiment_model(msg.get("text", "")) 

        if not collection.find_one({'id': msg['id']}):
            messages.append(msg)

        message_count -= 1
        if message_count == 0:
            collection.insert_many(messages)
            ch.stop_consuming()

    message_count = RedisHook(redis_conn_id='redis_conn').get_conn().get('message_count')
    collection = MongoHook(mongo_conn_id='mongo_conn').get_conn()['DB'][collection_name]
    messages = []

    with pika.BlockingConnection(pika.ConnectionParameters(host=con.host,
                                                           port=con.port,
                                                           virtual_host='/',
                                                           credentials=creds)) as rmq_con:
        channel = rmq_con.channel()
        channel.basic_consume(queue=queue_name, on_message_callback=action_on_msg, auto_ack=True)
        channel.start_consuming()


default_args = {
    "owner": "user",
    "retries": 0,
    "catchup": False
}

with DAG(dag_id='Telegram',
         start_date=datetime(2025, 1, 1, tzinfo=pendulum.timezone('Europe/Moscow')),
         schedule_interval="1 * * * *",
         description='DAG for Telegram ETL',
         default_args=default_args):

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
