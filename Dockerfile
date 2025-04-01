FROM apache/airflow:2.9.2

USER root
RUN apt-get update
RUN apt install -y default-jdk curl unzip erlang
RUN apt-get autoremove -yqq --purge
RUN apt-get install -y wget
RUN apt-get clean
RUN rm -rf /var/lib/apt/lists/*

RUN wget https://download.oracle.com/java/23/latest/jdk-23_linux-x64_bin.tar.gz && \ 
			mkdir -p /opt/java && \ 
			tar -xvf jdk-23_linux-x64_bin.tar.gz -C /opt/java && \ 
			rm jdk-23_linux-x64_bin.tar.gz

RUN wget -O jre-8u421-linux-x64.tar.gz https://javadl.oracle.com/webapps/download/AutoDL?BundleId=250118_d8aa705069af427f9b83e66b34f5e380 && \
    tar -xvf jre-8u421-linux-x64.tar.gz -C /opt/java && \
    rm jre-8u421-linux-x64.tar.gz
	
RUN wget https://downloads.apache.org/spark/spark-3.5.4/spark-3.5.4-bin-hadoop3.tgz && \
    mkdir -p /opt/spark && \
    tar -xvf spark-3.5.4-bin-hadoop3.tgz -C /opt/spark && \
    rm spark-3.5.4-bin-hadoop3.tgz
	
RUN wget https://jdbc.postgresql.org/download/postgresql-42.7.5.jar && \
    mkdir -p /opt/spark/jars && \
	mv postgresql-42.7.5.jar /opt/spark/jars/postgresql-connector.jar 

RUN curl -LO https://github.com/rabbitmq/rabbitmq-server/releases/download/v3.12.5/rabbitmq-server-generic-unix-3.12.5.tar.xz \
    && tar -xf rabbitmq-server-generic-unix-3.12.5.tar.xz \
    && cp rabbitmq_server-3.12.5/sbin/rabbitmqctl /usr/local/bin/ \
    && chmod +x /usr/local/bin/rabbitmqctl

RUN chmod 777 /opt/spark

ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV SPARK_HOME=/opt/spark/spark-3.5.4-bin-hadoop3
ENV PATH=$PATH:$JAVA_HOME/bin
ENV PATH=$PATH:$SPARK_HOME/bin
ENV PYTHONPATH=$SPARK_HOME/python/lib/py4j-0.10.9.7-src.zip


COPY requirements.txt /requirements.txt
RUN chmod 777 /requirements.txt

COPY connections.json /opt/airflow/connections.json
COPY variables.json   /opt/airflow/variables.json
#COPY dags/DAG.py   	  /opt/airflow/dags/DAG.py

USER airflow
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r /requirements.txt
