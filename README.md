# Voicebot with RAG

## Overview

This project implements a real-time Voice-based chatbot using Retrieval-Augmented Generation (RAG) architecture with
streaming audio output. It was developed as part of the "Generative AI for Human Computer Interaction" lecture,
combining voice interaction capabilities with advanced language models and information retrieval.

## Project Description

The Voicebot with RAG system enhances traditional chatbot interactions by incorporating:

- **Real-time streaming audio output** - Audio playback starts immediately as the LLM generates text
- **RAG architecture** - Retrieval-Augmented Generation for context-aware responses
- **Asynchronous pipeline** - Streaming text-to-speech conversion for low-latency interaction
- **Google Cloud Text-to-Speech** - High-quality German voice synthesis
- **PostgreSQL vector database** - Efficient similarity search for contextual information

## Features

- **Streaming TTS**: Audio begins playing while the LLM is still generating text
- **Word-boundary aware**: Ensures natural speech by avoiding word splitting
- **Console output**: Real-time display of the AI's response text
- **Async processing**: Non-blocking pipeline for responsive interaction
- **German language support**: Optimized for German text-to-speech

## Architecture

The system uses a three-stage async pipeline:

1. **RAG Stage**: Retrieves relevant context from vector database
2. **LLM Stage**: Generates streaming text responses using Google Gemini
3. **TTS Stage**: Converts text to audio in real-time with Google Cloud TTS

## Setup and Requirements

The project uses Python 3.9.6 and requires a Python virtual environment for proper dependency management.

### Prerequisites

- Python 3.10
- Virtual Environment
- PostgreSQL database
- Google Cloud account with TTS API enabled
- Google Gemini API access

### Installation

1. Clone the repository:
   ```bash
   git clone git@git.rz.uni-augsburg.de:saupejul/voicebot-with-rag.git
   cd voicebot-with-rag
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Setup PostgreSQL:
   Create a `.env` file in the root directory:
   ```
   # PostgreSQL
   POSTGRES_DB={database}
   POSTGRES_USER={user}
   POSTGRES_PASSWORD={password}
   POSTGRES_HOST={host}
   POSTGRES_PORT=5432
   ```

5. Setup Google Services:
   In the `.env` file add your API keys and credentials:
   ```
   # Google Gemini
   GEMINI_API_KEY={your_gemini_api_key}

   # Google Cloud TTS
   GOOGLE_APPLICATION_CREDENTIALS={path/to/your/credentials.json}
   ```

### Google Cloud Setup

1. Create a Google Cloud project
2. Enable the Text-to-Speech API
3. Create a service account and download the JSON credentials
4. Set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable

## Development with Tilt

[Tilt](https://tilt.dev/) provides an automated development environment that orchestrates all services with a single
command. This is the recommended way to run the project for development.

### Prerequisites for Tilt

- [Tilt](https://tilt.dev/) installed on your system
- [Docker](https://www.docker.com/) and Docker Compose
- [Node.js](https://nodejs.org/) and npm (for frontend)
- Python 3.10 with pip
- All environment variables configured in `.env` file (see manual setup section above)

### Tilt Installation

Install Tilt following the [official installation guide](https://docs.tilt.dev/install.html):

**macOS:**

```bash
curl -fsSL https://raw.githubusercontent.com/tilt-dev/tilt/master/scripts/install.sh | bash
```

**Windows:**

```bash
iex ((new-object net.webclient).downloadstring('https://raw.githubusercontent.com/tilt-dev/tilt/master/scripts/install.ps1'))
```

**Linux:**

```bash
curl -fsSL https://raw.githubusercontent.com/tilt-dev/tilt/master/scripts/install.sh | bash
```

### Running the Development Environment

1. **Start all services:**
   ```bash
   tilt up
   ```
   This command will:
    - Start the PostgreSQL database with pgvector extension
    - Launch the backend API server with hot reload
    - Start the frontend development server with hot reload
    - Set up proper service dependencies

2. **Access the Tilt UI:**
   Open your browser to `http://localhost:10350` to view the Tilt dashboard, which provides:
    - Real-time logs for all services
    - Service status and health checks
    - Resource management and controls
    - Quick access links to your applications

3. **Access your applications:**
    - **Frontend:** http://localhost:5173
    - **Backend API:** http://localhost:8000
    - **PostgreSQL:** localhost:5050

4. **Stop all services:**
   ```bash
   tilt down
   ```

## Usage

### Using the API Endpoint

The project includes a FastAPI server that provides an audio streaming endpoint for frontend applications.

1. Start the API server:
   ```bash
   python -m backend.run_api
   ```

2. The API will be available at `http://localhost:8000` with the following endpoints:
    - `GET /` - Health check endpoint
    - `GET /api/audio?prompt=your_question_here` - Audio streaming endpoint

### Frontend Setup

The project includes a Svelte-based frontend for interacting with the voicebot API.

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Configure the API URL:

   The frontend uses environment variables to configure the API URL. By default, it connects to `http://localhost:8000`,
   but you can customize this for different environments.

   Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

   Edit the `.env` file to set your API URL:
   ```
   VITE_API_BASE_URL=http://your-api-url
   ```

   For different environments, you can create:
    - `.env.development` - Used during development
    - `.env.production` - Used for production builds

4. Start the development server:
   ```bash
   npm run dev
   ```

5. Build for production:
   ```bash
   npm run build
   ```
