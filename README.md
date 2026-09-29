# SupportPilot 🚀
> **AI-Powered Customer Support Platform with Ticket Resolution Agent**

**SupportPilot** is an intelligent AI-powered IT support platform designed to automate the complete support-ticket lifecycle — from ticket submission and classification to knowledge retrieval, AI-generated resolution, validation, automated email resolution, and Jira escalation.

🌐 **Live Application:** [https://supportpilot-xgmv.onrender.com](https://supportpilot-xgmv.onrender.com/)

---

## 🌟 Overview
Traditional IT support systems often require manual ticket classification, searching through knowledge bases, preparing troubleshooting instructions, and escalating unresolved issues.

SupportPilot combines **Machine Learning, Retrieval-Augmented Generation (RAG), Large Language Models, and Multi-Agent AI workflows** to automate these repetitive support operations.

### Core Workflow
```text
User
 │
 ▼
Submit Support Ticket
 │
 ▼
Ticket Analysis & Classification
 │
 ▼
Severity & Priority Assessment
 │
 ▼
Knowledge Base Retrieval
 │
 ▼
RAG Context Augmentation
 │
 ▼
AI Resolution Generation
 │
 ▼
Multi-Agent Validation
 │
 ├───────────────┐
 │               │
 ▼               ▼
Auto Resolve   Escalate
 │               │
 ▼               ▼
Email User     Jira Ticket
```

## 🌟 Milestones Achieved

### ✅ Milestone 1 — Automated Ticket Classification
SupportPilot's first milestone establishes the intelligent ticket-triage foundation.

**🤖 Machine Learning Classification**
* Built using Python and Scikit-learn.
* Automatically classifies incoming IT support tickets.
* Supported categories:
  * Network
  * VPN
  * Password
  * Software
  * Hardware
  * System
* Uses a hierarchical classification approach combining Word TF-IDF and Character TF-IDF features.
* Final untouched test-set performance:
  * Accuracy: 94.20%
  * Macro F1: 92.75%

**🎯 Intelligent Triage**
The platform additionally determines:
* Ticket severity
* Ticket priority
* Business impact
* Classification metadata

**🎫 Ticket Management**
Users can:
* Create support tickets
* Track submitted tickets
* View ticket details
* Monitor ticket status
* View AI-generated analysis

### 🧠 Milestone 2 — Retrieval-Augmented Generation (RAG)
Milestone 2 introduces knowledge-grounded AI resolution.

**📚 Knowledge Base**
* SupportPilot maintains a structured IT knowledge base containing historical troubleshooting information.
* Each knowledge article contains:
  * Article ID
  * Title
  * Category
  * Troubleshooting content
* The knowledge base is derived from the project's processed support-ticket data.

**🔎 Knowledge Retrieval**
The retrieval engine uses:
* TF-IDF vectorization
* Cosine similarity
* Category-aware retrieval
* Relevance scoring
* Configurable relevance threshold

The system retrieves the most relevant troubleshooting articles for each ticket.

**🔄 RAG Pipeline**
```text
Ticket ↓
Ticket Analysis ↓
Query Generation ↓
Knowledge Retrieval ↓
Relevant Articles ↓
Context Builder ↓
LLM ↓
Grounded Resolution
```

**🧩 LLM Integration**
SupportPilot uses OpenRouter for LLM-based resolution generation.
The LLM receives:
* Ticket information
* Ticket category
* Priority
* Retrieved knowledge-base context

The generated response is grounded in the retrieved knowledge rather than relying solely on general model knowledge.

### 🤖 Milestone 3 — Autonomous Multi-Agent System
Milestone 3 extends the RAG pipeline into a specialized multi-agent workflow.

**🧩 Multi-Agent Architecture**
1. **Diagnosis Agent**
   * Responsible for:
     * Understanding incoming tickets
     * Determining ticket category
     * Assessing severity
     * Determining priority
   * The existing trained SupportPilot classifier is used as the foundation for ticket diagnosis.
2. **Retrieval Agent**
   * Responsible for:
     * Searching the knowledge base
     * Retrieving relevant troubleshooting information
     * Providing grounded context to the resolution workflow
3. **Resolution Agent**
   * Responsible for:
     * Generating troubleshooting instructions
     * Producing contextual resolution recommendations
     * Using retrieved knowledge as the primary source
4. **Validation Agent**
   * Validates the generated resolution using:
     * Diagnosis confidence
     * Retrieval relevance
     * Resolution completeness
   * The validation framework combines these signals into an overall confidence score.
5. **Escalation Agent**
   * Determines whether the ticket can be automatically resolved or requires human intervention.

**Multi-Agent Workflow**
```text
┌──────────────────┐
│  Support Ticket  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Diagnosis Agent  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Retrieval Agent  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Resolution Agent │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Validation Agent │
└────────┬─────────┘
    ┌────┴────┐
    │         │
    ▼         ▼
AUTO-RESOLVE ESCALATE
    │         │
    ▼         ▼
  Email      Jira
```

**📧 Automated Email Resolution**
When a ticket satisfies the configured auto-resolution criteria:
* The resolution is generated.
* The generated troubleshooting instructions are validated.
* The resolution is prepared for delivery.
* The user receives the resolution through email.
* Email delivery is implemented using SMTP configuration.

**🎫 Jira Escalation**
Tickets requiring human intervention can be escalated to Jira.
The Jira integration supports:
* Jira project configuration
* Ticket creation
* Summary generation
* Description generation
* Priority mapping
* Jira issue tracking

This allows unresolved AI-supported tickets to continue through a human support workflow.

### 📊 Milestone 4 — Analytics & Cloud Deployment
Milestone 4 focuses on operational visibility and production deployment.

**📈 Analytics Dashboard**
SupportPilot provides analytics for the support workflow, including available operational metrics such as:
* AI resolution activity
* Ticket analytics
* Resolution statistics
* Resolution time
* Customer satisfaction metrics where tracked
* System availability information where tracked

All displayed metrics are intended to be derived from application data rather than hardcoded demonstration values.

**☁️ Cloud Architecture**
SupportPilot is designed for cloud deployment using:
* Render — Application hosting
* Supabase PostgreSQL — Production database
* Gunicorn — Production WSGI server
* Docker — Containerized deployment
* Environment variables — Secure configuration

**Production Architecture**
```text
┌──────────────┐
│   Browser    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│    Render    │
│   Hosting    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Flask +    │
│   Gunicorn   │
└──────┬───────┘
       │
┌────────────┼─────────────┐
│            │             │
▼            ▼             ▼
┌──────────┐ ┌───────────┐ ┌──────────┐
│ Supabase │ │ OpenRouter│ │   Jira   │
│PostgreSQL│ │    LLM    │ │   API    │
└──────────┘ └───────────┘ └──────────┘
       │
       ▼
┌──────────┐
│   SMTP   │
│  Email   │
└──────────┘
```

## 🌐 Live Application
🚀 **SupportPilot**
🔗 [https://supportpilot-xgmv.onrender.com](https://supportpilot-xgmv.onrender.com/)

The deployed application provides access to the SupportPilot ticket-management and AI-assisted support workflow.
External capabilities such as OpenRouter, SMTP, Jira, and Supabase depend on their corresponding production environment configuration.

## 📂 Project Structure
```text
SupportPilot/
│
├── app.py                     └── Main Flask application and API routing
├── database.py                └── Database abstraction layer
├── render.yaml                └── Render deployment configuration
├── requirements.txt           └── Python dependencies
├── .env                       └── Environment variables (DO NOT COMMIT)
│
├── agents/
│   ├── orchestrator.py        └── Coordinates the multi-agent workflow
│   ├── diagnosis_agent.py     └── Ticket diagnosis and classification
│   ├── retrieval_agent.py     └── Knowledge retrieval
│   ├── resolution_agent.py    └── AI resolution generation
│   ├── validation_agent.py    └── Resolution confidence validation
│   └── escalation_agent.py    └── Resolution and escalation handling
│
├── rag/
│   ├── retriever.py           └── TF-IDF and cosine-similarity retrieval
│   ├── context_builder.py     └── Builds LLM-ready retrieved context
│   └── llm_generator.py       └── OpenRouter LLM integration
│
├── services/
│   ├── email_service.py       └── SMTP email service
│   └── jira_service.py        └── Jira API integration
│
├── models/
│   ├── ticket_classifier.pkl  └── Trained ticket-classification model
│   └── vectorizer.pkl         └── Serialized vectorizer
│
├── data/
│   └── knowledge_base.json    └── Support knowledge base
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── analytics.html
│   ├── integrations.html
│   └── ...
│
└── assets/
    ├── css/
    │   └── style.css
    └── js/
        └── app.js
```

## 🛠️ Technology Stack
| Layer | Technology |
|---|---|
| Frontend | HTML5, CSS3, JavaScript |
| UI | Responsive SaaS-style interface |
| Backend | Python, Flask |
| Machine Learning | Scikit-learn |
| Feature Engineering | TF-IDF |
| Retrieval | TF-IDF + Cosine Similarity |
| Generative AI | OpenRouter |
| LLM | Configurable OpenRouter Model |
| Multi-Agent System | Python |
| Database | SQLite / PostgreSQL |
| Production Database | Supabase PostgreSQL |
| Email | SMTP |
| Issue Escalation | Jira REST API |
| Production Server | Gunicorn |
| Deployment | Render |
| Containerization | Docker |
| Configuration | python-dotenv |

## 🔐 Security
SupportPilot is designed with security considerations including:
* Secure password hashing
* Authenticated application routes
* Environment-based secrets
* Secure database configuration
* Server-side API credentials
* No API keys exposed to the frontend
* Protected authentication information
* Parameterized database operations
* Secure production configuration

**Never commit sensitive credentials**
* `.env`
* API keys
* SMTP passwords
* Jira API tokens
* JWT secrets
* Database credentials

Use environment variables for all sensitive configuration.

## ⚙️ Setup & Deployment

### 1. Clone the Repository
```bash
git clone <your-repository-url>
cd SupportPilot
```

### 2. Create Virtual Environment
**Windows**
```cmd
python -m venv venv
venv\Scripts\activate
```
**Linux / macOS**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the project root.
Example:
```env
# ==========================================
# DATABASE
# ==========================================
DATABASE_URL=postgresql://your_supabase_connection_string

# ==========================================
# AI / LLM
# ==========================================
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_MODEL=your_openrouter_model

# ==========================================
# EMAIL
# ==========================================
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_EMAIL=your_email@gmail.com
SMTP_PASSWORD=your_gmail_app_password

# ==========================================
# JIRA
# ==========================================
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your_jira_email
JIRA_API_TOKEN=your_jira_api_token
JIRA_PROJECT_KEY=YOUR_PROJECT_KEY
```
*Never commit real credentials to GitHub.*

### 🧪 Local Development
If `DATABASE_URL` is not configured, the application can use the local SQLite database where supported by the current implementation.
Run:
```bash
python app.py
```
Open:
`http://127.0.0.1:5000`

### ☁️ Production Deployment
SupportPilot is deployed using Render with a production PostgreSQL database.

**Deployment Flow**
```text
GitHub
 │
 ▼
Render
 ├── Docker
 ├── Gunicorn
 └── Flask
 │
 ▼
Supabase PostgreSQL
```

**Production Configuration**
Configure the required environment variables in the Render dashboard rather than committing them to the repository.

**Current Deployment**
[https://supportpilot-xgmv.onrender.com](https://supportpilot-xgmv.onrender.com/)

## 🔄 End-to-End Ticket Lifecycle
```text
┌─────────────────────────┐
│   User submits ticket   │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  Ticket Preprocessing   │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│    ML Classification    │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│   Severity & Priority   │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│   Knowledge Retrieval   │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  Context Augmentation   │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│     LLM Resolution      │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ Multi-Agent Validation  │
└────────────┬────────────┘
       ┌─────┴─────┐
       │           │
       ▼           ▼
┌────────────┐ ┌────────────┐
│Auto Resolve│ │  Escalate  │
└─────┬──────┘ └─────┬──────┘
       │             │
       ▼             ▼
┌────────────┐ ┌────────────┐
│   Email    │ │    Jira    │
└────────────┘ └────────────┘
```

## 🎯 Key Features
* **🎫 Ticket Management**
  * Create support tickets
  * Track ticket status
  * View ticket details
  * Manage user-specific tickets
  * AI-assisted ticket analysis
* **🧠 AI Classification**
  * Automated category prediction
  * Severity detection
  * Priority calculation
  * ML-powered ticket triage
* **🔎 Knowledge Retrieval**
  * Structured IT knowledge base
  * TF-IDF retrieval
  * Cosine similarity
  * Category-aware retrieval
  * Relevance scoring
* **🤖 AI Resolution**
  * RAG-based context generation
  * OpenRouter LLM integration
  * Knowledge-grounded troubleshooting
  * Structured resolution generation
* **🧩 Multi-Agent AI**
  * Diagnosis Agent
  * Retrieval Agent
  * Resolution Agent
  * Validation Agent
  * Escalation Agent
  * Central Orchestrator
* **📧 Automation**
  * Automated resolution emails
  * SMTP integration
  * Jira escalation
  * Human-in-the-loop support
* **📊 Analytics**
  * Ticket analytics
  * AI resolution statistics
  * Resolution performance
  * Operational insights
* **☁️ Cloud Ready**
  * Docker
  * Gunicorn
  * Render
  * Supabase PostgreSQL
  * Environment-based configuration

## 📌 Project Highlights
| Capability | Implementation |
|---|---|
| Ticket Classification | Hierarchical Machine Learning |
| Classification Accuracy | 94.20% |
| Macro F1 | 92.75% |
| Knowledge Retrieval | TF-IDF + Cosine Similarity |
| Generative AI | OpenRouter |
| Architecture | Multi-Agent |
| Database | SQLite / PostgreSQL |
| Cloud Database | Supabase |
| Hosting | Render |
| Email Automation | SMTP |
| Escalation | Jira |
| Backend | Flask |
| Production Server | Gunicorn |

### 🧪 Evaluation
The final Milestone 1 classifier was evaluated on an untouched stratified test set.
* Final Test Performance
  * Accuracy : 94.20%
  * Macro F1 : 92.75%

The model uses ticket subject and description for classification, while resolution text is excluded from classifier features.
The retrieval evaluation is performed separately using tickets that were excluded from the knowledge base to avoid self-retrieval leakage.

## 🚀 Future Enhancements
Potential future improvements include:
* Dense embedding-based semantic retrieval
* Vector database integration
* Enterprise knowledge-base connectors
* Advanced agent planning
* Tool-using AI agents
* Human feedback loops
* Continuous model evaluation
* Advanced observability
* Expanded analytics
* Additional enterprise integrations

## 👥 Project
**SupportPilot**
*AI-Powered Customer Support Platform with Ticket Resolution Agent*

SupportPilot combines:
`Machine Learning` + `RAG` + `LLMs` + `Multi-Agent AI` + `Automation` + `Cloud Deployment`
to create an intelligent and scalable IT support workflow.

## 🌐 Live Demo
🚀 **Try SupportPilot**
[https://supportpilot-xgmv.onrender.com](https://supportpilot-xgmv.onrender.com/)
