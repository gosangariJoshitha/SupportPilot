# SupportPilot 🚀

**SupportPilot** is an intelligent, multi-agent IT support platform. It automates ticket classification, retrieves historical solutions, and autonomously resolves or escalates IT support issues.

---

## 🌟 Milestones Achieved

### ✅ Milestone 1: Automated Ticket Classification
- **Core Engine**: A Machine Learning classifier (Scikit-learn) automatically categorizes incoming tickets (e.g., VPN, Hardware, Password).
- **Intelligent Triage**: Rule-based engines predict severity and calculate priority based on business impact.
- **Modern UI**: A responsive, glassmorphism-styled dashboard for submitting and managing tickets.

### ✅ Milestone 2: Retrieval-Augmented Generation (RAG)
- **Knowledge Retrieval**: Converts historical IT articles (`data/knowledge_base.json`) into vector embeddings.
- **Contextual Generation**: Uses LLMs (OpenRouter/Llama) to dynamically generate custom troubleshooting steps based on past resolutions.

### ✅ Milestone 3: Autonomous Multi-Agent System
- **Orchestration**: Multiple agents collaborate (Diagnosis, Retrieval, Resolution, Validation, Escalation).
- **Auto-Resolve**: If the AI is >70% confident, it resolves the ticket and automatically emails the user.
- **Escalate**: If confidence is low, it halts and automatically creates a Jira ticket for human intervention.

### ✅ Milestone 4: Analytics & Cloud Deployment ☁️
- **Analytics Dashboard**: Tracks AI Resolution Rates, Average Resolution Time, CSAT (Customer Satisfaction), and System Uptime.
- **PostgreSQL Ready**: The entire database layer (`database.py`) was abstracted to seamlessly support cloud PostgreSQL instead of just local SQLite.
- **Cloud Infrastructure**: Completely Docker/Gunicorn containerized, using Supabase (Database) and Render (Web Hosting).

---

## 📂 Full Project Structure

```text
SupportPilot/
│
├── app.py                      # Main Flask application and API routing
├── database.py                 # Abstracted DB layer (SQLite & PostgreSQL compatible)
├── render.yaml                 # Deployment blueprint for Render.com
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (DO NOT COMMIT)
│
├── agents/                     # 🤖 Multi-Agent Workflow
│   ├── orchestrator.py         # Manages the flow between agents
│   ├── diagnosis_agent.py      # Predicts category, severity, priority
│   ├── retrieval_agent.py      # Fetches Knowledge Base context
│   ├── resolution_agent.py     # Generates AI troubleshooting steps
│   ├── validation_agent.py     # Calculates confidence scores
│   └── escalation_agent.py     # Handles Auto-Resolve (Email) vs Escalate (Jira)
│
├── rag/                        # 🧠 Retrieval-Augmented Generation Pipeline
│   ├── retriever.py            # Vector search engine
│   ├── context_builder.py      # Formats retrieved context
│   └── llm_generator.py        # Communicates with OpenRouter
│
├── services/                   # 🔌 External Integrations
│   ├── email_service.py        # SMTP email dispatcher
│   └── jira_service.py         # Atlassian Jira API connector
│
├── models/                     # 📦 Pre-trained Machine Learning Files
│   ├── ticket_classifier.pkl   # Serialized ML model
│   └── vectorizer.pkl          # TF-IDF Vectorizer
│
├── data/
│   └── knowledge_base.json     # 100+ historical IT articles for RAG
│
├── templates/                  # 🌐 Frontend HTML
│   ├── base.html               # Master layout
│   ├── index.html              # Main Ticket Submission Dashboard
│   ├── analytics.html          # M4 Analytics Dashboard
│   └── integrations.html       # Config UI for Jira & Email
│
└── assets/                     # 🎨 Frontend Assets (CSS/JS)
    ├── css/style.css           # Glassmorphism styling
    └── js/app.js               # Frontend Interactivity
```

---

## 🛠️ Setup & Deployment

### 1. Environment Setup
Create a `.env` file in the root directory:
```env
# Database
DATABASE_URL=postgresql://your_supabase_url

# AI Services
OPENROUTER_API_KEY=your_openrouter_key

# Integrations
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_EMAIL=your_email@gmail.com
SMTP_PASSWORD=your_app_password

JIRA_URL=https://your_domain.atlassian.net
JIRA_EMAIL=your_jira_email
JIRA_API_TOKEN=your_jira_token
JIRA_PROJECT_KEY=KAN
```

### 2. Local Development (SQLite)
If `DATABASE_URL` is omitted, it defaults to a local SQLite database (`tickets.db`).
```bash
pip install -r requirements.txt
python app.py
```

### 3. Production Deployment (Render + Supabase)
1. **Database**: Create a PostgreSQL database on **Supabase**.
2. **Hosting**: Connect your GitHub repository to **Render**.
3. Add the `.env` variables in the Render dashboard.
4. Render will automatically use Gunicorn to run `app.py`.
