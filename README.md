# Azure Test Case Generator with Agent Framework

An intelligent AI-powered test case generation system built with Azure AI Agent Framework that automatically analyzes requirement documents and generates comprehensive test artifacts including Epics, Features, Use Cases, and Test Cases.

## 🌟 Features

- **Multi-Agent Architecture**: Leverages Azure AI Agent Framework with specialized agents for different tasks
- **Document Analysis**: Automatically parses PDF and DOCX requirement documents
- **Interactive Requirement Review**: AI-powered chat interface for clarifying requirements
- **Hierarchical Test Artifact Generation**: Creates structured test hierarchies (Epics → Features → Use Cases → Test Cases)
- **Jira Integration**: Automatically pushes generated artifacts to Jira via MCP Server
- **Real-time Collaboration**: Interactive enhancement and migration capabilities
- **Export Options**: Export artifacts to Excel and XML formats
- **Analytics Dashboard**: Track project progress and test coverage metrics

## 🏗️ Architecture

### Tech Stack

**Backend:**
- FastAPI (Python) - RESTful API server
- Azure AI Agent Framework - Multi-agent orchestration
- Azure OpenAI - GPT-4 powered agents
- Azure Cosmos DB - Document storage
- Azure Blob Storage - File storage
- MCP (Model Context Protocol) Servers - External integrations

**Frontend:**
- React + TypeScript
- Vite - Build tool
- Zustand - State management
- React Hot Toast - Notifications
- React Dropzone - File uploads

**MCP Servers:**
- Jira MCP Server - Jira integration
- Cosmos MCP Server - Database operations

## 📋 Prerequisites

- **Python 3.11+**
- **Node.js 18+** and npm
- **Azure Account** with:
  - Azure OpenAI Service (GPT-4 deployment)
  - Azure Cosmos DB account
  - Azure Blob Storage account
- **Git**
- **Jira Account** (optional, for Jira integration)

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/sureshsoft09/Azure-Testcasegenerator-AgentFramework.git
cd Azure-Testcasegenerator-AgentFramework
```

### 2. Backend Setup

#### Install Python Dependencies

```bash
cd Backend
python -m venv .venv
.venv\Scripts\activate  # On Windows
# or
source .venv/bin/activate  # On Linux/Mac

pip install -r requirements.txt
```

#### Configure Environment Variables

Create a `.env` file in the `Backend` directory:

```env
# Azure Storage
AZURE_STORAGE_CONNECTION_STRING="your_storage_connection_string"
AZURE_STORAGE_CONTAINER_NAME="testcasegenerator-files"

# Azure Cosmos DB
COSMOS_DB_URL="https://your-cosmosdb.documents.azure.com:443/"
COSMOS_DB_KEY="your_cosmos_key"
COSMOS_DB_NAME="ai-test-generator"
COSMOS_PROJECTS_CONTAINER="projects"
COSMOS_ARTIFACTS_CONTAINER="artifacts"
COSMOS_SESSIONS_CONTAINER="sessions"

# Azure OpenAI
AZURE_OPENAI_ENDPOINT="https://your-openai.openai.azure.com"
AZURE_OPENAI_API_KEY="your_openai_key"
AZURE_OPENAI_DEPLOYMENT="gpt-4.1"
AZURE_OPENAI_API_VERSION="2024-12-01-preview"

AZURE_AI_PROJECT_ENDPOINT="https://your-agent-resource.services.ai.azure.com/api/projects/your-project"
AZURE_AI_MODEL_DEPLOYMENT_NAME="gpt-4.1"

# MCP Servers
JIRA_MCP_SERVER_URL="http://localhost:8002/mcp"
COSMOS_MCP_SERVER_URL="http://localhost:3101/sse"

# App Settings
APP_ENV=development
CORS_ORIGINS=["http://localhost:3000"]
```

#### Start Backend Server

```bash
cd Backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The backend API will be available at `http://localhost:8000`

### 3. Frontend Setup

#### Install Node Dependencies

```bash
cd Frontend
npm install
```

#### Start Frontend Development Server

```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

### 4. MCP Servers Setup (Optional)

#### Jira MCP Server

```bash
cd "MCP Servers/Jira MCP Server"

# Create .env file
cp .env.template .env

# Edit .env with your Jira credentials:
# JIRA_SERVER="https://your-domain.atlassian.net"
# JIRA_EMAIL="your-email@example.com"
# JIRA_API_TOKEN="your_jira_api_token"

# Install dependencies and run
pip install -r requirements.txt
python server.py
```

## 📁 Project Structure

```
├── Backend/
│   ├── api/
│   │   └── routes/          # API endpoints
│   │       ├── dashboard.py
│   │       ├── generate.py
│   │       ├── enhance.py
│   │       ├── migrate.py
│   │       └── analytics.py
│   ├── app_agents/          # AI Agents
│   │   ├── agent_orchestrator.py
│   │   ├── master_agent.py
│   │   ├── reqreviewer_agent.py
│   │   ├── testcasegenerator_agent.py
│   │   ├── enhance_agent.py
│   │   └── migration_agent.py
│   ├── core/                # Core utilities
│   │   ├── config.py
│   │   ├── cosmos_client.py
│   │   └── blob_storage.py
│   ├── models/              # Data models
│   │   └── schemas.py
│   ├── services/            # Business logic
│   │   ├── agent_service.py
│   │   ├── cosmos_service.py
│   │   ├── document_parser.py
│   │   └── export_service.py
│   ├── main.py              # FastAPI application
│   └── requirements.txt
│
├── Frontend/
│   ├── src/
│   │   ├── api/             # API client
│   │   ├── components/      # React components
│   │   ├── pages/           # Page components
│   │   │   ├── Dashboard/
│   │   │   ├── Generate/
│   │   │   ├── Enhance/
│   │   │   ├── Migrate/
│   │   │   └── Analytics/
│   │   ├── store/           # State management
│   │   └── types/           # TypeScript types
│   ├── package.json
│   └── vite.config.ts
│
└── MCP Servers/
    └── Jira MCP Server/     # Jira integration
        ├── server.py
        ├── jira_client.py
        └── requirements.txt
```

## 🎯 Usage

### 1. Generate Test Cases

1. **Create Project**: Navigate to "Generate" and create a new project with Jira details
2. **Upload Requirements**: Drag & drop PDF/DOCX requirement documents
3. **Review & Chat**: AI agent reviews requirements and asks clarifying questions
4. **Generate**: Click to generate comprehensive test artifacts
5. **View Results**: Browse generated Epics, Features, Use Cases, and Test Cases

### 2. Dashboard

- View all projects and their test artifacts
- Export artifacts to Excel or XML
- Track project statistics

### 3. Enhance Test Cases

- Select any artifact (Epic, Feature, Use Case, or Test Case)
- Chat with AI to refine and improve
- Apply enhancements in real-time

### 4. Migrate to Jira

- Bulk migrate test artifacts to Jira
- Configure Jira project mapping
- Track migration status

### 5. Analytics

- View heat maps and coverage metrics
- Track test case distribution
- Monitor project progress

## 🔌 API Endpoints

### Dashboard
- `GET /api/dashboard/projects` - Get all projects
- `GET /api/dashboard/projects/{project_id}/artifacts` - Get project artifacts
- `GET /api/dashboard/projects/{project_id}/export/excel` - Export to Excel
- `GET /api/dashboard/projects/{project_id}/export/xml` - Export to XML

### Generate
- `POST /api/generate/projects` - Create new project
- `POST /api/generate/projects/{project_id}/upload` - Upload requirement files
- `POST /api/generate/projects/{project_id}/review` - Review requirements
- `POST /api/generate/projects/{project_id}/review/chat` - Chat during review
- `POST /api/generate/projects/{project_id}/generate` - Generate test cases

### Enhance
- `POST /api/enhance/chat` - Chat to enhance artifacts
- `POST /api/enhance/apply` - Apply enhancements

### Migrate
- `POST /api/migrate/push-to-jira` - Migrate artifacts to Jira

### Analytics
- `GET /api/analytics/projects/{project_id}/metrics` - Get project metrics

## 🔧 Configuration

### Azure AI Agent Framework

The system uses Azure AI Foundry agents defined in the Azure portal. Update the following in `.env`:

```env
AZURE_AI_PROJECT_ENDPOINT="your_agent_project_endpoint"
AZURE_AI_MODEL_DEPLOYMENT_NAME="your_gpt4_deployment"
```

### Agent Orchestration

Agents are orchestrated through the `AgentOrchestrator` class which manages:
- **Master Agent**: Routes requests to specialized agents
- **Requirement Reviewer**: Analyzes and clarifies requirements
- **Test Case Generator**: Creates test artifacts
- **Enhancement Agent**: Refines existing artifacts
- **Migration Agent**: Handles Jira integration

## 🐛 Troubleshooting

### Backend Issues

**Connection Refused Error:**
```bash
# Ensure backend is running on port 8000
netstat -ano | findstr :8000
```

**Cosmos DB Errors:**
- Verify Cosmos DB connection string and key
- Ensure containers (projects, artifacts, sessions) are created

**Azure OpenAI Rate Limits:**
- Check your Azure OpenAI quota
- Implement retry logic if needed

### Frontend Issues

**API Call Failures:**
- Check that backend is running on `http://localhost:8000`
- Verify Vite proxy configuration in `vite.config.ts`

**Build Errors:**
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is proprietary software. All rights reserved.

## 👥 Authors

- **Suresh Chermadurai** - Initial work

## 🙏 Acknowledgments

- Azure AI Team for the Agent Framework
- Microsoft for Azure services
- The open-source community

## 📞 Support

For issues and questions:
- Open an issue on GitHub
- Contact: sureshsoft09@github.com

---

**Built with ❤️ using Azure AI Agent Framework**
