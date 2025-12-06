"""SEMS Main Entry Point - Kafka Consumer for Event Creation Flow."""

from kafka import KafkaConsumer
from kafka import TopicPartition
import json
import logging

from sems import config
from sems.message_processor import handle_kafka_message

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Initialize Kafka consumer and start processing messages."""

    logger.info("Starting SEMS (Series Events Messaging System)...")
    logger.info(f"Connecting to Kafka: {config.KAFKA_BOOTSTRAP_SERVERS}")
    logger.info(f"Topic: {config.KAFKA_TOPIC}")

    # Initialize Consumer WITHOUT subscribing to topic yet
    consumer = KafkaConsumer(
        bootstrap_servers=config.KAFKA_BOOTSTRAP_SERVERS.split(','),
        security_protocol='SASL_SSL',
        sasl_mechanism='PLAIN',
        sasl_plain_username=config.KAFKA_USERNAME,
        sasl_plain_password=config.KAFKA_PASSWORD,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='latest',
        enable_auto_commit=True
    )

    # Get all partitions for the topic and manually assign ALL of them
    partitions = consumer.partitions_for_topic(config.KAFKA_TOPIC)
    if partitions:
        topic_partitions = [TopicPartition(config.KAFKA_TOPIC, p) for p in partitions]
        consumer.assign(topic_partitions)
        logger.info(f"Manually assigned to {len(partitions)} partitions: {sorted(partitions)}")
    else:
        logger.error("Could not get partitions for topic!")
        return

    logger.info("Connected! Waiting for messages...")
    logger.info("Text the Series number to start creating events.")
    logger.info("Press Ctrl+C to stop.")

    try:
        for message in consumer:
            logger.info(f"--- New message received ---")
            logger.info(f"Topic: {message.topic}, Partition: {message.partition}, Offset: {message.offset}")

            # Process the message through our handler
            handle_kafka_message(message.value)

    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        consumer.close()
        logger.info("Consumer closed. Goodbye!")

if __name__ == "__main__":
    main()
