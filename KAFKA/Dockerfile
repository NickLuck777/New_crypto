FROM bitnami/kafka:3.9.0 
# 4.0.0 at the moment is the latest version and it has a bug with Histogram, so, use 3.9.0

USER root
COPY kafka-setup.sh /usr/local/bin/kafka-setup.sh
RUN chmod +x /usr/local/bin/kafka-setup.sh
