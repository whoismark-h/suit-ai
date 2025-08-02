# Technical Specifications - Suit-AI Legal Assistant

## System Overview

Suit-AI is an AI-powered legal assistant that automates legal research, document analysis, and legal writing through web scraping, RAG (Retrieval-Augmented Generation), and workflow automation.

## Architecture Overview

## Technology Stack

### Current MVP Stack
- **Language**: Python
- **Web Scraping**: Crawl4AI with authentication support
- **Dependencies**: Minimal Python packages for crawling
- **Automation**: n8n workflows
- **API Server**: FastAPI 
- **Database**: Supabase

### Frontend
- **Framework**: Next.js 14+ (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui
- **State Management**: Zustand
- **Data Fetching**: TanStack Query
- **Authentication**: NextAuth.js

### Infrastructure
- **Containerization**: Docker
- **Development**: Docker Compose
- **API Documentation**: FastAPI automatic OpenAPI/Swagger
- **Environment Management**: python-dotenv, Next.js env

## System Components

### Current MVP Component
**Authorized Web Crawler**
- Python script using Crawl4AI
- Session-based authentication
- Legal database scraping (e.g., Qanoniah)
- Data extraction and storage

### Future Components (Not in MVP)
- n8n workflow automation
- API endpoints
- Database integration
- Frontend application

## Folder Structure

### Current MVP Structure
```
suits-ai/
├── backend/
├── data/                  # Scraped data storage
├── logs/                  # Crawler logs
├── README.md
├── frontend/
├── workflows/
```


## Implementation Details

### Crawling Script Features
- **Authentication**: Session management for legal databases
- **Data Extraction**: Structured extraction of legal contentlure recovery
- **Logging**: Detailed crawling logs
- **Configuration**: Environment-based settings

## MVP Data Flow

1. **Script Execution** → Python crawler starts
2. **Authentication** → Login to legal database
3. **Data Scraping** → Extract legal content
4. **Data Storage** → Save to local files/database
5. **Logging** → Record success/failures
