# Voicebot with RAG

## Overview

This project implements a real-time Voice-based chatbot using Retrieval-Augmented Generation (RAG) architecture with streaming audio output. It was developed as part of the "Generative AI for Human Computer Interaction" lecture, combining voice interaction capabilities with advanced language models and information retrieval.

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

- Python 3.9.6
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

## Usage

### Running the Main Application

Run the main application for local audio playback:
```bash
python -m backend.main
```

### Using the API Endpoint

The project includes a FastAPI server that provides an audio streaming endpoint for frontend applications.

1. Start the API server:
   ```bash
   python -m backend.run_api
   ```

2. The API will be available at `http://localhost:8000` with the following endpoints:
   - `GET /` - Health check endpoint
   - `GET /api/audio?prompt=your_question_here` - Audio streaming endpoint

3. Connecting from a frontend:
   ```javascript
   // Example JavaScript code to connect to the audio stream
   async function playAudioFromAPI(prompt) {
     try {
       const response = await fetch(`http://localhost:8000/api/audio?prompt=${encodeURIComponent(prompt)}`);

       if (!response.ok) {
         throw new Error(`HTTP error! status: ${response.status}`);
       }

       // Get the audio context
       const audioContext = new (window.AudioContext || window.webkitAudioContext)();

       // Get the response as an array buffer
       const arrayBuffer = await response.arrayBuffer();

       // Convert the array buffer to an audio buffer
       const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);

       // Create a source node
       const source = audioContext.createBufferSource();
       source.buffer = audioBuffer;

       // Connect the source to the destination (speakers)
       source.connect(audioContext.destination);

       // Start playing
       source.start();
     } catch (error) {
       console.error('Error playing audio:', error);
     }
   }
   ```

   Note: For streaming PCM audio, you may need a more advanced implementation that processes chunks as they arrive.
