# API Reference

This document outlines the core REST API endpoints for the RAG SaaS Platform.

## Authentication
Unless specified otherwise, endpoints require an API Key.
**Header:** `X-Api-Key: <your_api_key>`

---

## 1. System

### Health Check
`GET /health`
Returns the status of the system.
**Response:**
```json
{
  "status": "ok",
  "version": "0.1.0"
}
```

---

## 2. Chat / RAG

### Ask Question
`POST /api/v1/chat`
Ask a natural language question. The system will retrieve relevant context and generate an AI answer.
**Request:**
```json
{
  "question": "What is our company's refund policy?",
  "conversation_id": "optional-uuid-here"
}
```
**Response:**
```json
{
  "answer": "According to the handbook, the company offers a 30-day refund policy..."
}
```

### Stream Answer (Future Implementation)
`POST /api/v1/chat/stream`
Streams the response chunks using Server-Sent Events (SSE).

---

## 3. Documents (Future Implementation)

### Upload Document
`POST /api/v1/documents/upload`
Uploads a file (PDF, TXT, DOCX), parses it, chunks it, and indexes it in the Vector Store.

### List Documents
`GET /api/v1/documents`
Lists all uploaded documents.

---

## 4. Search (Future Implementation)

### Semantic Search
`POST /api/v1/search/semantic`
Directly search the vector database for chunks related to a query.

---

## 5. Analytics (Future Implementation)

### Get Usage Token Costs
`GET /api/v1/usage/costs`
Returns aggregated token usage and cost estimations for the platform.
