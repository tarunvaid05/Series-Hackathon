# SEMS - Series Events Messaging System

SMS/iMessage-based event creation system using Kafka for message transport.

## Prerequisites

- Python 3.9+
- [Poetry](https://python-poetry.org/docs/#installation)

## Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd Series-Hackathon
   ```

2. **Install Poetry** (if not already installed)
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

3. **Install dependencies**
   ```bash
   poetry install
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your credentials:
   - `API_KEY` - Series Messaging API key
   - `SENDER_NUMBER` - Your Series phone number
   - `BOOTSTRAP_SERVERS` - Kafka bootstrap servers
   - `TOPIC_NAME` - Kafka topic name
   - `CONSUMER_GROUP` - Kafka consumer group
   - `SASL_USERNAME` - Kafka username
   - `SASL_PASSWORD` - Kafka password

## Running

```bash
poetry run sems
```

Or activate the virtual environment first:
```bash
poetry shell
sems
```

## Usage

1. Text the Series number to start
2. Send "create event" to begin event creation
3. Follow the prompts:
   - Event title
   - Description
   - Date and time
   - Location
   - Capacity (or "skip" for no limit)
4. Reply "confirm" to create the event

### Commands
- `create event` - Start creating a new event
- `cancel` - Cancel current event creation
- `restart` - Start over from the beginning
- `confirm` - Confirm and create the event
- `skip` - Skip optional fields (capacity)

## Project Structure

```
src/sems/
├── __init__.py
├── config.py           # Environment configuration
├── state_store.py      # In-memory conversation state
├── intent_handler.py   # Intent detection and flow logic
├── messaging_client.py # Series Messaging API client
├── message_processor.py# Kafka message handler
└── main.py             # Entry point
```
