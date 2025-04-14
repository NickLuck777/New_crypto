from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.bash import BashOperator
from datetime import datetime
import pendulum

default_args = {
    "owner": "user",
    "retries": 0,
    "catchup": False,
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False
}

with DAG(dag_id='Get_eth_data',
         start_date=datetime(2025, 1, 1, tzinfo=pendulum.timezone('Europe/Moscow')),
         schedule_interval="* * * * *",
         description='DAG for getting ETH data',
         default_args=default_args,
         catchup=False,
         max_active_runs=1):

    start = EmptyOperator(task_id='start')

    get_eth_data = BashOperator(
        task_id='get_eth_data',
        bash_command='python /opt/airflow/py_scripts/get_eth_data.py'
    )

    end = EmptyOperator(task_id='end')

start >> get_eth_data >> end
