# Voicebot with RAG

A real-time voice chatbot with Retrieval-Augmented Generation (RAG) capabilities, featuring streaming audio output and intelligent conversation management.

## What is this?

This project combines voice interaction with AI to create a conversational assistant that can:
- Listen to your voice and convert it to text
- Generate intelligent responses using RAG (context-aware AI)
- Speak back to you with natural-sounding voice synthesis
- Stream audio in real-time for responsive interaction

## Project Structure

```
voicebot-with-rag/
├── backend/          # Python API server with clean architecture
│   ├── internal/     # Domain logic, services, and adapters
│   ├── api/          # FastAPI web endpoints
│   └── cmd/          # Command-line utilities
├── frontend/         # SvelteKit web interface
│   └── src/          # UI components and services
├── docker-compose.yaml  # Database setup
└── Tiltfile         # Development orchestration
```

**Backend**: Python-based API using FastAPI, Google Cloud services, and PostgreSQL with vector search
**Frontend**: SvelteKit application with TypeScript for the web interface

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Docker
- Google Cloud credentials (for speech services)
- Gemini API key

### Setup

1. **Clone and configure**:
   ```bash
   git clone <repository-url>
   cd voicebot-with-rag
   cp .env.example .env  # Add your API keys
   ```

2. **Start with Tilt** (recommended):
   ```bash
   tilt up
   ```
   This starts everything: database, backend, and frontend.

3. **Access the application**:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000

### Manual Setup (alternative)

If you prefer to run services individually:

```bash
# Start database
docker-compose up postgres

# Start backend
cd backend
pip install -r requirements.txt
python -m backend.run_api

# Start frontend
cd frontend
npm install
npm run dev
```

## Environment Variables

Create a `.env` file with:
```
GEMINI_API_KEY=your_gemini_api_key
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
POSTGRES_DB=vectordb
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_HOST=localhost
POSTGRES_PORT=5050
```

## Usage

1. Open the web interface at http://localhost:5173
2. Allow microphone access when prompted
3. Click to start speaking or type your message
4. The AI will respond with both text and voice

The system supports both voice and text input, with real-time audio streaming for natural conversation flow.
