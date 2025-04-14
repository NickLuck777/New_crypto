import feedparser
import pika
from pika.credentials import PlainCredentials
import json
from datetime import datetime
import pendulum
from transformers import pipeline
import pymongo

# Configuration - replace with direct values for debugging
# You can modify these values as needed for your debugging
rmq_host = "localhost"
rmq_port = 5672
rmq_login = "nick"
rmq_password = "nick"
queue_name = "rss_queue"
collection_name = "rss_news"
rss_feeds = [
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "https://cointelegraph.com/rss"
    # Add your RSS feeds here
]
# Настройки MongoDB
mongo_db = "DB"
mongo_user = "root"
mongo_password = "123"

# Create credentials
creds = PlainCredentials(username=rmq_login, password=rmq_password)


def get_news():
    """Fetch news from RSS feeds and publish to RabbitMQ queue"""
    message_count = 0
    
    try:
        with pika.BlockingConnection(pika.ConnectionParameters(host=rmq_host, port=rmq_port, virtual_host='/',
                                                               credentials=creds)) as connection:
            channel = connection.channel()
            channel.queue_declare(queue=queue_name)

            for feed_url in rss_feeds:
                try:
                    print(f"Parsing RSS feed: {feed_url}")
                    feed = feedparser.parse(feed_url)
                    for entry in feed.entries:
                        try:
                            channel.basic_publish(exchange='', routing_key=queue_name, body=json.dumps(entry))
                            #print(f"Published message from {feed_url}: {json.dumps(entry)}")
                            message_count += 1
                        except pika.exceptions.AMQPError as e:
                            print(f"Error publishing message from {feed_url}: {e}")
                        except Exception as e:
                            print(f"Error processing entry from {feed_url}: {entry.get('id', 'N/A')} - {e}")
                except feedparser.FeedParserError as e:
                    print(f"Error parsing feed {feed_url}: {e}")
                except Exception as e:
                    print(f"Unexpected error processing feed {feed_url}: {e}")

            # Store message count for later use
            print(f"Successfully published {message_count} messages.")
            return message_count

    except pika.exceptions.AMQPConnectionError as e:
        print(f"RabbitMQ connection error in get_news: {e}")
        raise
    except Exception as e:
        print(f"Error in get_news: {e} (Type: {type(e).__name__})")
        raise


def process_news(message_count):
    """Process news from RabbitMQ queue and store in MongoDB"""
    sentiment_model = None
    messages = []
    collection = None

    def action_on_msg(ch, method, properties, body):
        nonlocal message_count, messages, collection, sentiment_model

        if collection is None or sentiment_model is None:
            print("Handler called before MongoDB collection or sentiment model initialization.")
            message_count -= 1
            if message_count <= 0:
                try:
                    ch.stop_consuming()
                except Exception as e:
                    print(f"Error stopping consumer after initialization failure: {e}")
            return

        try:
            msg = json.loads(body.decode('utf-8'))
            print(f"Received message from RabbitMQ: {msg['title']}")
            try:
                content_value = msg['title']
                if content_value:
                    msg['sentiment'] = sentiment_model(content_value)
                else:
                    print(f"No content found for sentiment analysis in message {msg.get('id', 'N/A')}")
                    msg['sentiment'] = None
            except Exception as e:
                print(f"Error during sentiment analysis for message {msg.get('id', 'N/A')}: {e}")
                msg['sentiment'] = None

            # Check if message already exists
            msg_id = msg.get('id')
            if msg_id:
                if not collection.find_one({'id': msg_id}, {'_id': 1}):
                    messages.append(msg)
                else:
                    print(f"Message with id {msg_id} already exists. Skipping.")
            else:
                print(f"Received message without id. Skipping duplicate check and adding.")
                messages.append(msg)

        except json.JSONDecodeError as e:
            print(f"Failed to decode message body: {e} Body: {body[:100]}...")
        except Exception as e:
            print(f"Error processing message: {e} (Type: {type(e).__name__})")
        finally:
            message_count -= 1
            print(f"Messages remaining: {message_count}")
            if message_count <= 0:
                print("All expected messages processed or counter reached zero.")
                if messages:
                    try:
                        print(f"Inserting {len(messages)} new messages into MongoDB.")
                        collection.insert_many(messages, ordered=False)
                        messages.clear()
                    except pymongo.errors.BulkWriteError as bwe:
                        write_errors = bwe.details.get('writeErrors', [])
                        dup_keys = sum(1 for err in write_errors if err.get('code') == 11000)
                        other_errors = len(write_errors) - dup_keys
                        print(f"MongoDB bulk write error: {dup_keys} duplicate keys ignored. {other_errors} other errors.")
                        if other_errors > 0:
                            print(f"Details about non-duplicate errors: {bwe.details}")
                        messages.clear()
                    except (pymongo.errors.ConnectionFailure, pymongo.errors.OperationFailure) as op_err:
                        print(f"MongoDB connection/operation error during insert: {op_err}")
                    except Exception as e:
                        print(f"Error inserting messages into MongoDB: {e} (Type: {type(e).__name__})")
                else:
                    print("No new messages to insert.")

                try:
                    print("Attempting to stop RabbitMQ consumer...")
                    ch.stop_consuming()
                    print("Stopped consuming RabbitMQ messages.")
                except Exception as e:
                    print(f"Failed to stop consumer (may be expected if connection is closed): {e}")

    try:
        print("Initializing sentiment analysis model...")
        sentiment_model = pipeline('sentiment-analysis')
        print("Sentiment analysis model loaded.")

        # Connect to MongoDB
        mongo_client = pymongo.MongoClient(host="localhost", port=27017, username="root", password="123")
        collection = mongo_client[mongo_db][collection_name]
        # Test connection/authentication in advance
        collection.find_one({}, {'_id': 1})
        print(f"Connected to MongoDB collection: {mongo_db}.{collection_name}")

        if message_count > 0:
            with pika.BlockingConnection(pika.ConnectionParameters(host=rmq_host,
                                                                   port=rmq_port,
                                                                   virtual_host='/',
                                                                   credentials=creds)) as connection:
                channel = connection.channel()
                channel.queue_declare(queue=queue_name, durable=False)
                channel.basic_consume(queue=queue_name, on_message_callback=action_on_msg, auto_ack=True)
                print(f"Starting RabbitMQ consumer on queue '{queue_name}'. Expecting {message_count} messages...")
                channel.start_consuming()
                print("RabbitMQ consumption completed.")
        else:
            print("No messages expected (message_count=0). Skipping RabbitMQ consumption.")

    except Exception as e:
        print(f"Unexpected error in process_news: {e} (Type: {type(e).__name__})")
        raise


def main():
    """Main function to run the RSS processing pipeline"""
    print("Starting RSS debug script...")
    try:
        # Get news from RSS feeds
        msg_count = get_news()
        
        # Process news if any were found
        if msg_count > 0:
            process_news(msg_count)
        else:
            print("No messages to process.")
            
        print("RSS debug script completed successfully.")
    except Exception as e:
        print(f"Error in main function: {e}")


if __name__ == "__main__":
    main()
