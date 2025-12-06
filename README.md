# SEMS - Series Events Messaging System

A conversational event management system that lets users create, discover, join, and manage events entirely through SMS/iMessage. Includes a companion web dashboard for visual event management.

## Features

### SMS/iMessage Interface
- **Create Events** - Guided conversational flow to create public or private events
- **Discover Events** - Find and join events happening near you
- **Join Events** - Request to join events with host approval workflow
- **Edit Events** - Modify your hosted events
- **Delete Events** - Remove events you've created
- **Leave Events** - Drop out of events you've joined
- **Close Events** - Finalize events and create group chats with attendees
- **View Attendees** - See who's coming to your events
- **My Events** - Quick overview of hosted and joined events

### Web Dashboard
- Phone-based authentication (no passwords)
- Create, edit, and delete events
- View and manage attendees
- Approve/deny join requests
- Profile management (name, bio, age)

### AI Features
- Natural language intent detection using Google Gemini
- Group chat bot that responds to "when/where" questions

## Prerequisites

- Python 3.9+
- Node.js 18+
- [Poetry](https://python-poetry.org/docs/#installation)

## Setup

### 1. Clone and Install

```bash
git clone <your-repo-url>
cd Series-Hackathon

# Install Python dependencies
poetry install

# Install web dashboard dependencies
cd web
npm install
cd ..
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Series Messaging API
API_KEY=your_api_key
SENDER_NUMBER=+16463029478

# Kafka Configuration
BOOTSTRAP_SERVERS=your_bootstrap_servers
TOPIC_NAME=your_topic
CONSUMER_GROUP=your_consumer_group
SASL_USERNAME=your_username
SASL_PASSWORD=your_password

# AI Intent Detection (optional)
GOOGLE_API_KEY=your_google_api_key
```

For the web dashboard, create `web/.env.local`:
```env
SERIES_API_KEY=your_api_key
SERIES_SENDER_NUMBER=+16463029478
```

### 3. Initialize Data Directory

```bash
mkdir -p data
echo "[]" > data/events.json
echo "{}" > data/users.json
```

## Running

### SEMS Messaging Service

```bash
poetry run sems
```

Or with Poetry shell:
```bash
poetry shell
sems
```

### Web Dashboard

```bash
cd web
npm run dev
```

Access at `http://localhost:3000`

## SMS Commands

| Command | Description |
|---------|-------------|
| `create event` | Start creating a new event |
| `find events` | Discover available events |
| `join event` | Request to join an event |
| `my events` | View your hosted and joined events |
| `edit event` | Modify your hosted events |
| `delete event` | Remove your hosted events |
| `leave event` | Drop out of a joined event |
| `close event` | Finalize event and create group chat |
| `view attendees` | See who's attending your events |
| `invite` | Invite users to private events |
| `menu` / `help` | Show available commands |
| `cancel` | Cancel current operation |
| `restart` | Start over |

## Project Structure

```
Series-Hackathon/
├── src/sems/                    # SEMS messaging backend
│   ├── main.py                  # Entry point
│   ├── config.py                # Environment configuration
│   ├── message_processor.py     # Kafka message handler
│   ├── messaging_client.py      # Series API client
│   ├── intent_handler.py        # Intent detection & flow logic
│   ├── intent_analysis_agent.py # AI-powered intent detection
│   ├── state_store.py           # Conversation state management
│   ├── event_store.py           # Event persistence (JSON)
│   ├── user_store.py            # User persistence (JSON)
│   └── group_chat_bot.py        # Group chat AI responses
│
├── web/                         # Next.js web dashboard
│   ├── app/                     # App router pages & API routes
│   │   ├── api/events/          # Event CRUD endpoints
│   │   ├── api/users/           # User endpoints
│   │   └── api/auth/            # Authentication
│   ├── components/              # React components
│   └── lib/                     # Utilities
│
├── data/                        # Runtime data (gitignored)
│   ├── events.json              # Event storage
│   └── users.json               # User storage
│
└── Project-Requirements.txt     # Full system requirements
```

## API Endpoints

### Events
- `GET /api/events` - List events (with filters)
- `POST /api/events` - Create event
- `GET /api/events/[id]` - Get single event
- `PUT /api/events/[id]` - Update event
- `DELETE /api/events/[id]` - Delete event
- `POST /api/events/[id]/join` - Join event
- `POST /api/events/[id]/approve` - Approve join request
- `POST /api/events/[id]/deny` - Deny join request

### Users
- `GET /api/users/[phone]` - Get user profile
- `PUT /api/users/[phone]` - Update profile
- `POST /api/users/lookup` - Bulk phone-to-name lookup

### Auth
- `POST /api/auth/login` - Login/register by phone

## Data Models

### Event
```json
{
  "id": "uuid",
  "host_phone": "+1234567890",
  "title": "Event Title",
  "description": "Description",
  "datetime": "2025-12-10T15:00",
  "location": "Location",
  "capacity": 10,
  "participants": ["+1111111111"],
  "pending_requests": ["+2222222222"],
  "denied_requests": [],
  "status": "open",
  "private": false
}
```

### User
```json
{
  "+1234567890": {
    "name": "John",
    "registered_at": "2025-12-06T...",
    "bio": "Optional bio",
    "age": 25
  }
}
```

## Architecture

```
User (SMS/iMessage)
        │
        ▼
Series Messaging API ──► Kafka ──► SEMS Message Processor
        ▲                                    │
        │                                    ▼
        │                           Intent Handler
        │                                    │
        └────────────────────────────────────┘
                    (Response)

User (Web Browser)
        │
        ▼
   Next.js Dashboard ──► API Routes ──► JSON Data Store
```

## License

MIT
