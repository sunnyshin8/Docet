# Docet Backend

Docet is a smart, self-updating API support assistant that automatically ingests documentation and provides RAG-powered chat capabilities for developers and support teams.

## Features

- **Automated Documentation Ingestion**: Supports OpenAPI/Swagger, Markdown, HTML, and other documentation formats
- **RAG-Powered Chat**: Uses Google Gemini with retrieval-augmented generation for accurate responses
- **Vector Search**: ChromaDB integration for semantic document search
- **Multi-Format Support**: Handles various documentation types and formats
- **Local Model Training**: Fine-tune local models on your documentation
- **Version-Aware Processing**: Detects and handles multiple API versions
- **RESTful API**: FastAPI-based backend with comprehensive endpoints

## Architecture

```
├── app/
│   ├── api/           # FastAPI routes and endpoints
│   ├── chat/          # Chat service and conversation handling
│   ├── connectors/    # Documentation source connectors
│   ├── ingestion/     # Document processing and chunking
│   ├── llm/           # Language model services (Gemini, local)
│   ├── models/        # Pydantic data models
│   ├── rag/           # Retrieval-augmented generation service
│   ├── storage/       # Local file storage service
│   ├── tools/         # LLM function calling tools
│   └── vector/        # Vector database integration
├── data/              # Local storage for documents and embeddings
└── tests/             # Unit and integration tests
```

## Quick Start

### Prerequisites

- Python 3.8+
- Google AI Studio API Key (for Gemini)
- Git

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd Docet/backend
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your Google AI Studio API key
```

5. Run the development server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Required
GOOGLE_AI_STUDIO_API_KEY=your_google_ai_studio_api_key_here

# Application Settings
DEBUG=true
HOST=127.0.0.1
PORT=8000

# Storage
LOCAL_STORAGE_PATH=./data
VECTOR_DB_PATH=./data/vector_db

# Embedding Settings
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# Security (for production)
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here
```

## API Usage

### Document Ingestion

Ingest documentation from various sources:

```bash
# Ingest OpenAPI/Swagger documentation
curl -X POST "http://localhost:8000/api/v1/ingestion/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://petstore.swagger.io/v2/swagger.json",
    "chatbot_id": "petstore-bot",
    "connector_type": "swagger"
  }'
```

### Chat Interface

Send messages and get AI-powered responses:

```bash
# Send a chat message
curl -X POST "http://localhost:8000/api/v1/chat/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How do I authenticate with the API?",
    "chatbot_id": "petstore-bot"
  }'
```

### Model Training

Train local models on ingested documentation:

```bash
# Start model training
curl -X POST "http://localhost:8000/api/v1/training/train" \
  -H "Content-Type: application/json" \
  -d '{
    "learning_rate": 5e-4,
    "num_epochs": 3,
    "batch_size": 4
  }'
```

## Supported Connectors

- **Swagger/OpenAPI**: Automatic detection and processing of API specifications
- **Markdown**: GitHub wikis, GitBook, and standalone Markdown files
- **HTML**: Generic web documentation and help pages
- **Fivetran**: Custom connector for data pipeline documentation

## LLM Services

### Google Gemini (Recommended)
- Uses Google AI Studio API
- Native function calling support
- Conversation history management
- Per-chatbot tool configuration

### Local Models
- Supports Qwen, Phi, T5, and other Hugging Face models
- LoRA fine-tuning capabilities
- GPU acceleration support
- Mock mode for development

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_ingestion.py
```

### Testing Individual Components

```bash
# Test Gemini service
python test_simple_gemini.py

# Test local LLM service
python test_llm_direct.py

# Test RAG system
python test_gemini_rag.py

# Test tool setup
python test_tool_setup.py
```

### Code Quality

The project uses:
- FastAPI for web framework
- Pydantic for data validation
- ChromaDB for vector storage
- Sentence Transformers for embeddings
- pytest for testing

## Project Structure Details

### Core Services

- **RAG Service**: Combines retrieval and generation for contextual responses
- **Vector Service**: Handles document embeddings and similarity search  
- **Ingestion Service**: Processes and chunks documents from various sources
- **Chat Service**: Manages conversations and session state

### Connectors

Each connector implements the `BaseConnector` interface:
- Version detection
- Document extraction
- Metadata preservation
- Error handling

### Tools System

Function calling tools for LLMs:
- Version information retrieval
- Mathematical calculations
- Document search and retrieval
- Custom business logic integration

## Deployment

### Production Considerations

1. **Security**: Set strong `SECRET_KEY` and `JWT_SECRET`
2. **Database**: Consider PostgreSQL for production storage
3. **Caching**: Implement Redis for session and response caching
4. **Monitoring**: Add logging and metrics collection
5. **Scaling**: Use gunicorn with multiple workers

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions and support:
- Create an issue in the GitHub repository
- Check the documentation in `/docs`
- Review the API documentation at `/docs` when running locally