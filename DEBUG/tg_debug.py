import json
import pika
from pika.credentials import PlainCredentials
from telethon.sync import TelegramClient
from transformers import pipeline
import pymongo
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Configuration - replace with direct values for debugging
# You can modify these values as needed for your debugging
rmq_host = "localhost"
rmq_port = 5672
rmq_login = "nick"
rmq_password = "nick"
queue_name = "TELEGRAM"
collection_name = "TELEGRAM"

# Telegram API credentials - REPLACE WITH YOUR OWN
api_id = 27948937  # Replace with your actual API ID
api_hash = "c080ddb27bcafabd88c52b78f7c6a0e1"  # Replace with your actual API hash
channels = ["@Pro_Blockchain", "@forklog", "@invcryptonews"]  # Replace with your channel usernames or IDs
posts_limit = 10  # Number of posts to fetch per channel

# MongoDB settings
mongo_db = "DB"
mongo_user = "root"
mongo_password = "123"

# Create RabbitMQ credentials
creds = PlainCredentials(username=rmq_login, password=rmq_password)


def get_posts():
    """Fetch posts from Telegram channels and publish to RabbitMQ queue"""
    message_count = 0
    
    logging.info("Starting Telegram posts collection")
    try:
        with TelegramClient('Get_msg', api_id, api_hash) as tg_client:
            logging.info("Connected to Telegram API")
            
            try:
                with pika.BlockingConnection(pika.ConnectionParameters(
                    host=rmq_host, 
                    port=rmq_port, 
                    virtual_host='/',
                    credentials=creds
                )) as rmq_con:
                    logging.info("Connected to RabbitMQ")
                    
                    # Process each channel in the configuration
                    for channel in channels:
                        logging.info(f"Processing Telegram channel: {channel}")
                        try:
                            # For debugging, we don't use Redis to track last message ID
                            # Instead, we just fetch the most recent messages
                            last_msg_id = 0
                            
                            # Fetch messages from the channel
                            messages = tg_client.get_messages(channel, limit=posts_limit)
                            logging.info(f"Retrieved {len(messages)} messages from {channel}")

                            # Process each message
                            for msg in messages:
                                if msg.id > last_msg_id:
                                    logging.info(f"Processing message {msg.id} from {channel}")
                                    
                                    # Extract message content
                                    msg_text = msg.text if msg.text else ""
                                    
                                    # Create JSON message
                                    json_msg = json.dumps({
                                        'id': msg.id,
                                        'date': str(msg.date),  # Convert datetime to string for JSON
                                        'text': msg_text,
                                        'channel': channel
                                    })

                                    # Publish message to RabbitMQ
                                    channel_rmq = rmq_con.channel()
                                    channel_rmq.queue_declare(queue=queue_name)
                                    channel_rmq.basic_publish(
                                        exchange='', 
                                        routing_key=queue_name, 
                                        body=json_msg
                                    )
                                    message_count += 1
                                    logging.info(f"Published message {msg.id} to RabbitMQ")
                        except Exception as e:
                            logging.error(f"Error processing channel {channel}: {e}")
                    
                    # Print total message count
                    logging.info(f"Successfully published {message_count} messages to RabbitMQ")
                    return message_count
                    
            except pika.exceptions.AMQPConnectionError as e:
                logging.error(f"RabbitMQ connection error: {e}")
                raise
            except Exception as e:
                logging.error(f"Error in RabbitMQ operations: {e}")
                raise
    except Exception as e:
        logging.error(f"Telegram API connection error: {e}")
        raise


def process_posts(message_count):
    """Process posts from RabbitMQ queue, perform sentiment analysis, and store in MongoDB"""
    sentiment_model = None
    messages = []
    collection = None
    
    def action_on_msg(ch, method, properties, body):
        nonlocal message_count, messages, collection, sentiment_model
        
        if collection is None or sentiment_model is None:
            logging.error("Handler called before MongoDB collection or sentiment model initialization.")
            message_count -= 1
            if message_count <= 0:
                try:
                    ch.stop_consuming()
                except Exception as e:
                    logging.error(f"Error stopping consumer after initialization failure: {e}")
            return
        
        try:
            # Parse the message JSON
            msg = json.loads(body.decode('utf-8'))
            logging.info(f"Received message from RabbitMQ: {msg.get('id')} from {msg.get('channel')}")
            
            try:
                # Perform sentiment analysis on the message text
                content_value = msg.get("text", "")
                if content_value:
                    msg['sentiment'] = sentiment_model(content_value)
                    logging.info(f"Sentiment analysis for message {msg.get('id')}: {msg['sentiment']}")
                else:
                    logging.warning(f"No content found for sentiment analysis in message {msg.get('id', 'N/A')}")
                    msg['sentiment'] = None
            except Exception as e:
                logging.error(f"Error during sentiment analysis for message {msg.get('id', 'N/A')}: {e}")
                msg['sentiment'] = None
            
            # Check if message already exists in MongoDB
            msg_id = msg.get('id')
            if msg_id:
                if not collection.find_one({'id': msg_id}, {'_id': 1}):
                    messages.append(msg)
                    logging.info(f"Added message {msg_id} to batch for MongoDB insertion")
                else:
                    logging.info(f"Message with id {msg_id} already exists. Skipping.")
            else:
                logging.warning("Received message without id. Skipping.")
                
        except json.JSONDecodeError as e:
            logging.error(f"Failed to decode message body: {e} Body: {body[:100]}...")
        except Exception as e:
            logging.error(f"Error processing message: {e}")
        finally:
            # Decrement the counter even on processing error
            message_count -= 1
            logging.info(f"Messages remaining: {message_count}")
            if message_count <= 0:
                logging.info("All expected messages processed or counter reached zero.")
                if messages:
                    try:
                        logging.info(f"Inserting {len(messages)} new messages into MongoDB.")
                        collection.insert_many(messages, ordered=False)
                        logging.info("MongoDB insertion completed successfully")
                        messages.clear()
                    except pymongo.errors.BulkWriteError as bwe:
                        write_errors = bwe.details.get('writeErrors', [])
                        dup_keys = sum(1 for err in write_errors if err.get('code') == 11000)
                        other_errors = len(write_errors) - dup_keys
                        logging.warning(f"MongoDB bulk write error: {dup_keys} duplicate keys ignored. {other_errors} other errors.")
                        if other_errors > 0:
                            logging.error(f"Details about non-duplicate errors: {bwe.details}")
                        messages.clear()
                    except Exception as e:
                        logging.error(f"Error inserting messages into MongoDB: {e}")
                else:
                    logging.info("No new messages to insert.")
                
                try:
                    logging.info("Stopping RabbitMQ consumer...")
                    ch.stop_consuming()
                    logging.info("Stopped consuming RabbitMQ messages.")
                except Exception as e:
                    logging.warning(f"Failed to stop consumer: {e}")
    
    try:
        logging.info("Initializing sentiment analysis model...")
        sentiment_model = pipeline('sentiment-analysis')
        logging.info("Sentiment analysis model loaded.")
        
        # Connect to MongoDB
        mongo_client = pymongo.MongoClient(
            host="localhost", 
            port=27017, 
            username=mongo_user, 
            password=mongo_password
        )
        collection = mongo_client[mongo_db][collection_name]
        # Test connection/authentication
        collection.find_one({}, {'_id': 1})
        logging.info(f"Connected to MongoDB collection: {mongo_db}.{collection_name}")
        
        if message_count > 0:
            with pika.BlockingConnection(pika.ConnectionParameters(
                host=rmq_host,
                port=rmq_port,
                virtual_host='/',
                credentials=creds
            )) as connection:
                channel = connection.channel()
                channel.queue_declare(queue=queue_name, durable=False)
                channel.basic_consume(
                    queue=queue_name, 
                    on_message_callback=action_on_msg, 
                    auto_ack=True
                )
                logging.info(f"Starting RabbitMQ consumer on queue '{queue_name}'. Expecting {message_count} messages...")
                channel.start_consuming()
                logging.info("RabbitMQ consumption completed.")
        else:
            logging.info("No messages expected (message_count=0). Skipping RabbitMQ consumption.")
            
    except Exception as e:
        logging.error(f"Unexpected error in process_posts: {e}")
        raise


def main():
    """Main function to run the Telegram processing pipeline"""
    logging.info("Starting Telegram debug script...")
    try:
        # Get posts from Telegram channels
        msg_count = get_posts()
        
        # Process posts if any were found
        if msg_count > 0:
            process_posts(msg_count)
        else:
            logging.info("No messages to process.")
            
        logging.info("Telegram debug script completed successfully.")
    except Exception as e:
        logging.error(f"Error in main function: {e}")


if __name__ == "__main__":
    main()
