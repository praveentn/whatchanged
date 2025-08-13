# DocuReview Pro

> **Enterprise Document Version Management & Analysis System**

A sophisticated AI-powered platform for document analysis, version comparison, and content management. Built with FastAPI, React, and Azure OpenAI for enterprise-grade document workflows.

![DocuReview Pro Dashboard](docs/images/dashboard-preview.png)

## 🌟 Features

### 📄 **Document Management**
- **Automatic Versioning**: Intelligent document version control with change tracking
- **AI-Powered Analysis**: Content structure analysis, intent detection, and entity extraction
- **Semantic Search**: Advanced search capabilities using sentence transformers and FAISS
- **Bulk Operations**: Upload and process multiple documents efficiently

### 🔍 **Advanced Comparison**
- **Multi-Level Diffing**: Character, word, sentence, and paragraph-level comparisons
- **Semantic Analysis**: Meaning-based change detection using embeddings
- **Configurable Algorithms**: Choose between syntactic, semantic, or hybrid comparison methods
- **Visual Diff Viewer**: Side-by-side and unified diff views with customizable highlighting

### 🤖 **AI Integration**
- **Azure OpenAI**: Leverages GPT models for content analysis and summarization
- **Intent Classification**: Automatically categorizes content by purpose (requirements, design, risks, etc.)
- **Change Summarization**: AI-generated summaries of document modifications
- **Entity Recognition**: Extract and track relationships between document elements

### 🎨 **Enterprise UI/UX**
- **Professional Design**: Clean, modern interface optimized for business workflows
- **Responsive Layout**: Works seamlessly on desktop, tablet, and mobile devices
- **Real-time Updates**: Live status updates and progress tracking
- **Accessibility**: WCAG 2.1 compliant design with keyboard navigation

### 🛠️ **Administration**
- **SQL Executor**: Direct database access with query history and result export
- **System Monitoring**: Real-time performance metrics and health checks
- **Audit Logging**: Comprehensive activity tracking and compliance features
- **Maintenance Tools**: Automated cleanup, backup, and optimization utilities

## 🚀 Quick Start

### Prerequisites

- **Python 3.9+** with pip
- **Node.js 18+** with npm
- **Azure OpenAI** account with API access
- **Git** for version control

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/docureview-pro.git
cd docureview-pro
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd app

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
```

### 3. Configure Environment

Edit `.env` file with your Azure OpenAI credentials:

```bash
# Required: Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT=gpt-4-turbo
```

### 4. Initialize Database

```bash
# Run database initialization
python -c "from database import init_database; init_database()"
```

### 5. Start Backend Server

```bash
# Using the startup script (recommended)
python start.py

# Or using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8555
```

### 6. Frontend Setup

```bash
# Open new terminal and navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 7. Access the Application

- **Web Interface**: http://localhost:3000
- **API Documentation**: http://localhost:8555/api/docs
- **Admin Panel**: http://localhost:3000/admin

## 📖 Detailed Setup

### Backend Configuration

#### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI service endpoint | - | ✅ |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key | - | ✅ |
| `AZURE_OPENAI_DEPLOYMENT` | Model deployment name | gpt-4-turbo | ✅ |
| `CHUNK_SIZE` | Text chunk size for processing | 800 | ❌ |
| `SIMILARITY_THRESHOLD` | Semantic similarity threshold | 0.7 | ❌ |
| `UPLOAD_FOLDER` | File upload directory | uploads | ❌ |

#### Database Schema

The application uses SQLite by default with the following main tables:

- **documents**: Document metadata and versions
- **chunks**: Text chunks with AI analysis
- **comparisons**: Cached comparison results
- **vector_indexes**: FAISS index metadata
- **audit_logs**: System activity tracking

### Frontend Configuration

#### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | Backend API base URL | http://localhost:8555/api |
| `VITE_APP_TITLE` | Application title | DocuReview Pro |

#### Build Configuration

```bash
# Development build
npm run dev

# Production build
npm run build

# Preview production build
npm run preview

# Type checking
npm run type-check

# Linting
npm run lint
```

## 🔧 API Reference

### Document Management

#### Upload Document
```http
POST /api/documents/upload
Content-Type: multipart/form-data

file: document.txt
title: "API Documentation"
author: "John Doe"
domain: "technical"
tags: "api,documentation"
auto_analyze: true
```

#### List Documents
```http
GET /api/documents?limit=20&offset=0&search=api&domain=technical
```

#### Get Document Analysis
```http
GET /api/documents/{id}/analysis
```

### Document Comparison

#### Compare Documents
```http
POST /api/comparison/compare
Content-Type: application/json

{
  "document_a_id": 123,
  "document_b_id": 124,
  "granularity": "word",
  "algorithm": "hybrid",
  "similarity_threshold": 0.8
}
```

#### Compare by Slug and Version
```http
POST /api/comparison/compare-by-slug
Content-Type: application/json

{
  "document_slug": "api-documentation",
  "version_a": 1,
  "version_b": 2,
  "granularity": "sentence",
  "algorithm": "semantic"
}
```

### Search

#### Semantic Search
```http
POST /api/search/semantic
Content-Type: application/json

{
  "query": "user authentication requirements",
  "document_slug": "api-docs",
  "top_k": 10,
  "similarity_threshold": 0.7
}
```

### Admin Operations

#### Execute SQL
```http
POST /api/admin/sql/execute
Content-Type: application/json

{
  "query": "SELECT * FROM documents WHERE status = 'indexed' LIMIT 10",
  "limit_results": true
}
```

#### System Statistics
```http
GET /api/admin/stats/system
```

## 🏗️ Architecture

### Backend Architecture

```
app/
├── main.py                 # FastAPI application entry point
├── config.py              # Configuration management
├── database.py            # Database models and operations
├── dependencies.py        # Dependency injection
├── services/              # Business logic services
│   ├── llm_service.py     # Azure OpenAI integration
│   ├── embedding_service.py # Embeddings and FAISS
│   ├── document_service.py # Document management
│   ├── analysis_service.py # AI analysis
│   └── comparison_service.py # Document comparison
├── routers/               # API route handlers
│   ├── documents.py       # Document endpoints
│   ├── comparison.py      # Comparison endpoints
│   ├── search.py         # Search endpoints
│   └── admin.py          # Admin endpoints
├── utils/                 # Utility functions
│   ├── chunking.py       # Text chunking
│   ├── text_processing.py # Text normalization
│   └── diff_engine.py    # Advanced diff algorithms
└── models/               # Pydantic models
    ├── document.py       # Document schemas
    └── comparison.py     # Comparison schemas
```

### Frontend Architecture

```
frontend/src/
├── App.tsx               # Main React application
├── components/           # Reusable UI components
│   ├── Layout.tsx        # Main layout wrapper
│   ├── Sidebar.tsx       # Navigation sidebar
│   ├── Header.tsx        # Application header
│   └── UtilityComponents.tsx # Common UI elements
├── pages/                # Page components
│   ├── Dashboard.tsx     # Main dashboard
│   ├── DocumentList.tsx  # Document listing
│   ├── DocumentComparison.tsx # Comparison interface
│   └── AdminPanel.tsx    # Admin interface
├── services/             # API and external services
│   └── api.ts           # HTTP client configuration
├── hooks/                # Custom React hooks
├── utils/                # Utility functions
└── types/                # TypeScript type definitions
```

### Technology Stack

#### Backend
- **FastAPI**: Modern Python web framework with automatic API documentation
- **SQLAlchemy**: Python SQL toolkit and ORM
- **SQLite**: Lightweight, serverless database (easily replaceable with PostgreSQL)
- **Azure OpenAI**: Large language models for content analysis
- **Sentence Transformers**: Embeddings for semantic similarity
- **FAISS**: Efficient similarity search and clustering
- **Pydantic**: Data validation using Python type annotations

#### Frontend
- **React 18**: Modern React with hooks and concurrent features
- **TypeScript**: Type-safe JavaScript development
- **Vite**: Fast build tool and development server
- **Tailwind CSS**: Utility-first CSS framework
- **TanStack Query**: Powerful data synchronization for React
- **React Router**: Declarative routing for React applications
- **Axios**: Promise-based HTTP client
- **Lucide React**: Beautiful and customizable icons

## 🚀 Deployment

### Production Environment

#### Backend Deployment

1. **Environment Setup**
```bash
# Create production environment file
cp .env.example .env.production

# Configure for production
export DEBUG=false
export HOST=0.0.0.0
export PORT=8555
```

2. **Database Migration**
```bash
# For PostgreSQL in production
export DATABASE_URL=postgresql://user:pass@localhost/docureview_pro
python -c "from database import init_database; init_database()"
```

3. **Start Production Server**
```bash
# Using Gunicorn (recommended)
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8555

# Or using uvicorn
uvicorn main:app --host 0.0.0.0 --port 8555 --workers 4
```

#### Frontend Deployment

1. **Build for Production**
```bash
cd frontend
npm run build
```

2. **Serve Static Files**
```bash
# Using nginx (recommended)
# Copy dist/ contents to nginx web root

# Or using a simple HTTP server
npx serve dist -p 3000
```

### Docker Deployment

#### Backend Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8555

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8555"]
```

#### Frontend Dockerfile
```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
```

#### Docker Compose
```yaml
version: '3.8'
services:
  backend:
    build: ./app
    ports:
      - "8555:8555"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/docureview
    depends_on:
      - db
    
  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
    
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=docureview
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## 🔧 Development

### Setting Up Development Environment

1. **Install Development Dependencies**
```bash
# Backend
pip install -r requirements-dev.txt

# Frontend
npm install --include=dev
```

2. **Pre-commit Hooks**
```bash
# Install pre-commit
pip install pre-commit
pre-commit install

# Run manually
pre-commit run --all-files
```

3. **Testing**
```bash
# Backend tests
pytest tests/ -v --cov=app

# Frontend tests
npm run test
npm run test:ui
```

### Code Quality

#### Backend
- **Black**: Code formatting
- **Flake8**: Linting
- **MyPy**: Type checking
- **Pytest**: Testing framework

#### Frontend
- **ESLint**: JavaScript/TypeScript linting
- **Prettier**: Code formatting
- **TypeScript**: Type checking
- **Vitest**: Testing framework

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## 📊 Performance

### Benchmarks

- **Document Analysis**: ~2-5 seconds per document (depending on size)
- **Comparison Generation**: ~500ms-2s for typical documents
- **Search Response**: <100ms for semantic search
- **API Response Times**: <200ms average for CRUD operations

### Optimization Tips

1. **Batch Processing**: Use bulk upload for multiple documents
2. **Caching**: Comparison results are automatically cached
3. **Indexing**: Ensure proper database indexing for large datasets
4. **Memory Management**: Monitor memory usage with large document sets

## 🐛 Troubleshooting

### Common Issues

#### "ModuleNotFoundError" when starting backend
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

#### Azure OpenAI connection errors
```bash
# Verify environment variables
echo $AZURE_OPENAI_ENDPOINT
echo $AZURE_OPENAI_API_KEY

# Test connection
python -c "from services.llm_service import LLMService; print('Connection OK')"
```

#### Frontend build errors
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
npm run dev
```

#### Database issues
```bash
# Reset database
rm docureview_pro.db
python -c "from database import init_database; init_database()"
```

### Logging

Enable debug logging:
```bash
# Backend
export LOG_LEVEL=DEBUG

# Check logs
tail -f logs/app.log
```

## 📈 Monitoring

### Health Checks

- **Application Health**: `/health`
- **API Documentation**: `/api/docs`
- **System Stats**: `/api/admin/stats/system`

### Metrics

The application tracks:
- Document upload and analysis rates
- Comparison generation performance
- Search query performance
- System resource usage
- User activity patterns

## 🤝 Support

### Documentation
- [API Reference](docs/api.md)
- [User Guide](docs/user-guide.md)
- [Admin Guide](docs/admin-guide.md)
- [Developer Guide](docs/developer-guide.md)

### Community
- [Issues](https://github.com/your-org/docureview-pro/issues)
- [Discussions](https://github.com/your-org/docureview-pro/discussions)
- [Contributing](CONTRIBUTING.md)

### Commercial Support
For enterprise support, training, and custom development:
- Email: support@docureview-pro.com
- Website: https://docureview-pro.com

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Azure OpenAI** for providing state-of-the-art language models
- **Hugging Face** for the sentence transformers library
- **FastAPI** community for the excellent web framework
- **React** team for the powerful frontend library
- **Tailwind CSS** for the utility-first CSS framework

---

**DocuReview Pro** - Transforming document management with AI-powered analysis and comparison.

Built with ❤️ for enterprise document workflows.