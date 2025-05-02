FROM apache/airflow:2.9.2

USER root
RUN apt-get update
RUN apt install -y default-jdk unzip
RUN apt-get autoremove -yqq --purge

COPY requirements.txt /requirements.txt
RUN chmod 744 /requirements.txt

COPY connections.json /opt/airflow/connections.json
COPY variables.json /opt/airflow/variables.json
RUN chmod 766 /opt/airflow/*.json

COPY dags/*.py /opt/airflow/dags/
RUN chmod 755 /opt/airflow/dags/*.py

RUN mkdir -p /opt/airflow/py_scripts
RUN chmod 777 /opt/airflow/py_scripts

RUN mkdir -p /opt/airflow/logs/py_scripts
RUN chmod 777 /opt/airflow/logs/py_scripts

COPY PyCode/get_eth_data.py /opt/airflow/py_scripts/get_eth_data.py
#COPY dags/transform_md.py /opt/airflow/py_scripts/transform_md.py
RUN chmod 755 /opt/airflow/py_scripts/*.py

USER airflow
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r /requirements.txt
