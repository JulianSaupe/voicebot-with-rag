# Voicebot with RAG

## Overview

This project implements a Voice-based chatbot using Retrieval-Augmented Generation (RAG) architecture. It was developed
as part of the "Generative AI for Human Computer Interaction" lecture, combining voice interaction capabilities with
advanced language models and information retrieval.

## Project Description

The Voicebot with RAG system enhances traditional chatbot interactions by incorporating voice interface and leveraging
RAG architecture to provide more accurate and context-aware responses. This approach combines the benefits of both
retrieval-based and generative AI methods.

## Setup and Requirements

The project uses Python 3.9.6 and requires a Python virtual environment for proper dependency management.

### Prerequisites

- Python 3.9.6
- Virtual Environment

### Installation

1. Clone the repository:
   ```bash
   git clone git@git.rz.uni-augsburg.de:saupejul/voicebot-with-rag.git
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   ```

3. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```
   
4. Setup Postgres:

   Create a `.env` file in the root directory:
   ```
   # Postgres
   POSTGRES_DB={database}
   POSTGRES_USER={user}
   POSTGRES_PASSWORD={password}
   POSTGRES_HOST={host}
   POSTGRES_PORT=5050
   ```
   
5. Setup Gemini:

   In the `.env` file add your Gemini api key:
   ```
   # Gemini
   GEMINI_API_KEY={API KEY}
   ```
