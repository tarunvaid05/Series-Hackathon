"""Configuration module for SEMS environment variables."""

import os
from dotenv import load_dotenv

load_dotenv()

# Series Messaging API
API_BASE_URL = "https://series-hackathon-service-202642739529.us-east1.run.app"
API_KEY = os.getenv("API_KEY")
SENDER_NUMBER = os.getenv("SENDER_NUMBER")

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("BOOTSTRAP_SERVERS")
KAFKA_TOPIC = os.getenv("TOPIC_NAME")
KAFKA_GROUP_ID = os.getenv("CONSUMER_GROUP")
KAFKA_USERNAME = os.getenv("SASL_USERNAME")
KAFKA_PASSWORD = os.getenv("SASL_PASSWORD")
