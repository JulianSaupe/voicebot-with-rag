# Voicebot with RAG

A sophisticated real-time voice chatbot with Retrieval-Augmented Generation (RAG) capabilities, featuring streaming audio output, intelligent conversation management, and clean hexagonal architecture.

## What is this?

This project combines voice interaction with AI to create a conversational assistant that can:
- Listen to your voice and convert it to text using Google Cloud Speech-to-Text
- Generate intelligent responses using RAG (context-aware AI) with Gemini
- Speak back to you with natural-sounding voice synthesis
- Stream audio in real-time for responsive interaction
- Store and retrieve contextual information using vector embeddings

## Architecture

This project demonstrates advanced software architecture principles with modern AI capabilities:

### Backend (Python)
- **Clean Architecture**: Hexagonal/Ports-and-Adapters pattern for maintainable code
- **Domain Layer**: Pure business logic and models
- **Application Layer**: Use cases and orchestration services
- **Ports**: Input (driving) and Output (driven) interfaces
- **Adapters**: Driving (web controllers) and Driven (external services)
- **Dependency Injection**: Centralized container for clean separation of concerns

### Frontend (TypeScript/Svelte)
- **SvelteKit**: Modern full-stack framework with TypeScript
- **Service Architecture**: Modular services for audio, WebSocket, and input handling
- **Real-time Communication**: WebSocket-based bidirectional communication

### Key Technologies
- **RAG Implementation**: Sentence-transformers for embeddings and pgvector for similarity search
- **Voice Processing**: WebRTC VAD for voice activity detection
- **Multi-language Support**: Configured for German (de-DE) by default
- **Real-time Audio**: Streams audio chunks for low-latency playback

## Project Structure

```
voicebot-with-rag/
├── backend/                    # Python API server with clean architecture
│   ├── internal/              # Domain logic, services, and adapters
│   │   ├── domain/            # Business logic and models
│   │   ├── ports/             # Interface definitions
│   │   │   ├── input/         # Driving ports (controllers)
│   │   │   └── output/        # Driven ports (external services)
│   │   ├── adapters/          # Implementation of ports
│   │   │   ├── driving/       # Web controllers, CLI
│   │   │   └── driven/        # External service implementations
│   │   ├── application/       # Use cases and services
│   │   └── container.py       # Dependency injection container
│   ├── api/                   # FastAPI web endpoints
│   └── cmd/                   # Command-line utilities
├── frontend/                  # SvelteKit web interface
│   ├── src/                   # UI components and services
│   │   ├── lib/               # Reusable components
│   │   ├── routes/            # SvelteKit routes
│   │   └── services/          # Frontend business logic
│   ├── e2e/                   # End-to-end tests
│   └── tests/                 # Unit tests
├── docker-compose.yaml        # Database setup
├── Tiltfile                   # Development orchestration
└── credentials.json           # Google Cloud credentials (not in repo)
```

**Backend**: Python-based API using FastAPI, Google Cloud services, and PostgreSQL with vector search
**Frontend**: SvelteKit application with TypeScript for the web interface

## Quick Start

### Prerequisites
- Python 3.10+ with pip
- Node.js 18+ with npm
- Docker and Docker Compose
- Tilt (for development orchestration)
- Google Cloud credentials (for Speech-to-Text and Text-to-Speech APIs)
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
   - PostgreSQL: localhost:5050
   - WebSocket endpoints: 
     - Speech: ws://localhost:8000/ws/speech
     - Text: ws://localhost:8000/ws/text

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

## Development Workflow

### Using Tilt (Recommended)
Tilt provides automated development orchestration for the entire stack:

```bash
tilt up    # Start all services (database, backend, frontend)
tilt down  # Stop all services
```

Tilt automatically handles:
- Database initialization with pgvector extension
- Backend API server with hot reload
- Frontend development server with live updates
- Dependency management and service coordination

### Key Dependencies

#### Backend (Python)
- **FastAPI** (0.115.14): Modern web framework for building APIs
- **Google Cloud Speech** (2.21.0): Speech-to-Text and Text-to-Speech services
- **Sentence Transformers** (5.0.0): Embeddings for RAG implementation
- **PostgreSQL** with pgvector: Vector database for similarity search
- **WebRTC VAD** (2.0.10): Voice activity detection
- **MediaPipe & FFmpeg**: Audio processing pipeline
- **Uvicorn** (0.35.0): ASGI server for FastAPI

#### Frontend (TypeScript/Svelte)
- **SvelteKit**: Full-stack framework with TypeScript
- **Vite**: Build tool and development server
- **ESLint & Prettier**: Code quality and formatting
- **Playwright**: End-to-end testing
- **Vitest**: Unit testing framework

## Testing

### Backend Testing

**Architecture Validation**:
```bash
python backend/test_ports_adapters_architecture.py
```
This comprehensive test validates:
- Dependency injection container
- Domain models and business logic
- Ports and adapters structure
- Clean architecture implementation

### Frontend Testing

**Unit Tests**:
```bash
cd frontend
npm run test:unit
```

**End-to-End Tests**:
```bash
cd frontend
npm run test:e2e
```

**Development Scripts**:
```bash
npm run dev      # Start development server
npm run build    # Build for production
npm run preview  # Preview production build
npm run lint     # Run ESLint
npm run format   # Format code with Prettier
```

## WebSocket Communication Protocol

The application uses WebSocket connections for real-time communication:

### Message Formats
- **PCM Audio**: `{"type": "pcm", "data": [float32_array]}`
- **Text Input**: `{"type": "text_prompt", "data": {"text": string, "voice": string}}`
- **Transcription Response**: `{"type": "transcription", "transcription": string, "confidence": float}`
- **Audio Chunks**: `{"type": "audio", "data": [int16_array], "chunk_number": int}`

### Endpoints
- **Speech Processing**: `ws://localhost:8000/ws/speech`
- **Text Processing**: `ws://localhost:8000/ws/text`

## Code Style and Development Practices

### Backend (Python)
- **Clean Architecture**: Strict separation of concerns with hexagonal pattern
- **Domain-Driven Design**: Rich domain models with business logic
- **Dependency Injection**: Use the centralized container for all dependencies
- **Async/Await**: Consistent use of async patterns for I/O operations
- **Type Hints**: Use Python type hints for better code documentation

### Frontend (TypeScript/Svelte)
- **ESLint Configuration**: Modern flat config with TypeScript and Svelte support
- **Prettier Integration**: Automatic code formatting with Svelte plugin
- **TypeScript**: Strict type checking enabled
- **Service Pattern**: Modular services for different functionalities
- **Component Structure**: Clean separation of logic and presentation

## Debugging and Troubleshooting

### Common Issues

**Backend Issues**:
- Check Google Cloud credentials and API quotas
- Verify PostgreSQL connection and pgvector extension
- Monitor audio processing pipeline for bottlenecks

**Frontend Issues**:
- Use browser dev tools for WebSocket message inspection
- Check microphone permissions and audio input
- Verify service worker registration for audio processing

**Integration Issues**:
- Test WebSocket endpoints individually
- Validate message format compatibility
- Check CORS configuration for cross-origin requests

### Logging and Monitoring
- Use structured logging for debugging and monitoring
- Monitor WebSocket connection stability
- Track audio processing performance and memory usage
