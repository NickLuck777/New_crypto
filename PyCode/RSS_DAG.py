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

rmq_con = BaseHook.get_connection('rabbitmq_conn')
creds = PlainCredentials(username=rmq_con.login, password=rmq_con.password)
queue_name = Variable.get('rmq_rss_queue')
collection_name = Variable.get('mongo_rss_collection')
rss_feeds = json.loads(Variable.get('rss_channels'))
mongo_db = Variable.get('mongo_db')


def get_news():
    message_count = 0
    with pika.BlockingConnection(pika.ConnectionParameters(host=rmq_con.host, port=rmq_con.port, virtual_host='/',
                                                           credentials=creds)).channel() as channel:
        channel.queue_declare(queue=queue_name)

        for feed_url in rss_feeds:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                channel.basic_publish(exchange='', routing_key=queue_name, body=json.dumps(entry))
                message_count += 1

        RedisHook(redis_conn_id='redis_conn').get_conn().set('message_count', message_count)


def process_news():
    def action_on_msg(ch, method, properties, body):
        nonlocal message_count, messages, collection

        msg = json.loads(body.decode('utf-8'))
        sentiment_model = pipeline('sentiment-analysis')
        msg['sentiment'] = sentiment_model(msg.get("content", [{}])[0].get("value", ""))

        if not collection.find_one({'guid': msg['guid']}):
            messages.append(msg)

        message_count -= 1
        if message_count == 0:
            collection.insert_many(messages)
            ch.stop_consuming()

    message_count = RedisHook(redis_conn_id='redis_conn').get_conn().get('message_count')
    collection = MongoHook(mongo_conn_id='mongo_conn').get_conn()[mongo_db][collection_name]
    messages = []

    with pika.BlockingConnection(pika.ConnectionParameters(host=rmq_con.host,
                                                           port=rmq_con.port,
                                                           virtual_host='/',
                                                           credentials=creds)).channel() as channel:
        channel.basic_consume(queue=queue_name, on_message_callback=action_on_msg, auto_ack=True)
        channel.start_consuming()


default_args = {
    "owner": "user",
    "retries": 0,
    "catchup": False
}

with DAG(dag_id='RSS',
         start_date=datetime(2025, 1, 1, tzinfo=pendulum.timezone('Europe/Moscow')),
         schedule_interval="1 * * * *",
         description='DAG for RSS ETL',
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

    get_news = PythonOperator(
        task_id='get_news',
        python_callable=get_news
    )

    process_news = PythonOperator(
        task_id='process_news',
        python_callable=process_news
    )

    end = EmptyOperator(task_id='end')

start >> init >> get_news >> process_news >> end
