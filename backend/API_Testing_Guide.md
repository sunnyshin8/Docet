# Docet API Testing Guide

This guide provides curl commands to test the Docet API with Swagger Petstore documentation ingestion and chatbot interaction.

## Prerequisites

- Docet backend server running on `http://localhost:8000`
- `jq` installed for JSON formatting (optional but recommended)

## Configuration

```bash
BASE_URL="http://localhost:8000/api/v1"
CHATBOT_ID="petstore-demo"
SWAGGER_URL="https://petstore.swagger.io/"
```

## API Testing Commands

### 1. Health Check

Verify the server is running:

```bash
curl -X GET "http://localhost:8000/health"
```

### 2. List Supported Documentation Sources

Check what documentation types Docet can ingest:

```bash
curl -X GET "$BASE_URL/ingestion/supported-sources" \
  -H "Content-Type: application/json" | jq
```

### 3. Analyze Documentation Source

Analyze the Swagger Petstore before ingesting:

```bash
curl -X POST "$BASE_URL/ingestion/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://petstore.swagger.io/"
  }' | jq
```

### 4. Ingest Documentation

Ingest the Swagger Petstore documentation into a chatbot:

```bash
curl -X POST "$BASE_URL/ingestion/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://petstore.swagger.io/",
    "chatbot_id": "petstore-demo",
    "force_reingestion": true
  }' | jq
```

### 5. Check Chatbot Statistics

Verify the ingestion was successful:

```bash
curl -X GET "$BASE_URL/ingestion/chatbots/petstore-demo/stats" | jq
```

### 6. Test Document Retrieval

Test the RAG retrieval system directly:

```bash
curl -X POST "$BASE_URL/ingestion/chatbots/petstore-demo/test-retrieval?query=pets" | jq
```

### 7. Chat with the Chatbot

Test various questions about the API:

#### Basic Endpoint Information

```bash
curl -X POST "$BASE_URL/chat/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the POST /pet endpoint for?",
    "chatbot_id": "petstore-demo"
  }' | jq
```

#### List All Pet Endpoints

```bash
curl -X POST "$BASE_URL/chat/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "List all pet-related endpoints in this API",
    "chatbot_id": "petstore-demo"
  }' | jq
```

#### API Usage Questions

```bash
curl -X POST "$BASE_URL/chat/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How do I add a new pet to the store?",
    "chatbot_id": "petstore-demo"
  }' | jq
```

#### Response Code Information

```bash
curl -X POST "$BASE_URL/chat/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What response codes does the pet API return?",
    "chatbot_id": "petstore-demo"
  }' | jq
```

#### Data Model Questions

```bash
curl -X POST "$BASE_URL/chat/message" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Tell me about the Pet data model structure",
    "chatbot_id": "petstore-demo"
  }' | jq
```

### 8. List All Chatbots

See all available chatbots:

```bash
curl -X GET "$BASE_URL/ingestion/chatbots" | jq
```

## Management Commands

### Delete a Chatbot

Remove a chatbot and all its data:

```bash
curl -X DELETE "$BASE_URL/ingestion/chatbots/petstore-demo"
```

## Expected Results

### Successful Ingestion Response

```json
{
  "chatbot_id": "petstore-demo",
  "url": "https://petstore.swagger.io/",
  "status": "success",
  "detected_type": "swagger_ui",
  "connector_used": "SwaggerConnector",
  "versions_processed": ["2"],
  "total_documents": 21,
  "metadata": {
    "source_title": "Documentation from https://petstore.swagger.io/",
    "connector": "SwaggerConnector"
  }
}
```

### Chat Response Format

```json
{
  "message": "The POST /pet endpoint is used to add a new pet to the store...",
  "session_id": "petstore-demo:abc123...",
  "sources": [
    {
      "title": "",
      "url": "",
      "similarity": 0.95
    }
  ],
  "metadata": {
    "chatbot_id": "petstore-demo",
    "context_used": true,
    "context_chunks_count": 3
  }
}
```

## Features Demonstrated

- **Auto-Detection**: Automatically detects Swagger UI documentation type
- **Version-Aware**: Processes API version 2 from the Swagger spec
- **RAG Integration**: Uses retrieved context to answer questions accurately
- **Source Attribution**: Provides source information for transparency
- **Gemini Integration**: Uses Gemini 2.5 Pro for intelligent responses
- **Tool Usage**: Chatbot can call tools like `search_documentation` for comprehensive answers

## Troubleshooting

### Gemini API Overload (503 Error)

If you see 503 errors, the Gemini API is temporarily overloaded. Wait a few minutes and retry.

### No Context Found

If `context_used` is false, try:
- More specific questions
- Questions that match the ingested content
- Check retrieval with the test-retrieval endpoint

### Server Not Running

Start the Docet backend:

```bash
cd backend
source venv/bin/activate
python -m app.main
```