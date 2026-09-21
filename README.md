# SupportPilot - AI Ticket Resolution Agent

## Project Overview
SupportPilot is an AI-powered platform designed to automate IT support-ticket processing, troubleshooting, and resolution workflows. By automatically classifying tickets and predicting severity and priority, it aims to reduce response times and increase operational efficiency.

## Problem Statement
Handling a large volume of repetitive IT support tickets (e.g., password resets, VPN access issues, Wi-Fi connectivity) manually increases operational costs, delays responses, and impacts employee productivity. 

## ✅ Milestone 1 Completed
The goal of Milestone 1 was to build a functional end-to-end MVP. This has been successfully achieved:
1. Accept an IT support ticket through a web form.
2. Store the ticket securely in a database.
3. Automatically identify the problem category using AI.
4. Predict the issue's severity based on keywords.
5. Calculate priority using both severity and business impact.
6. Display classification results on an intuitive dashboard.

## Architecture
- **Ticket Intake**: HTML/Bootstrap web form
- **Ingestion & Processing**: Python/Flask Backend
- **Text Preprocessing**: Lowercase, tokenization, TF-IDF
- **Classification Engine**: Best performing Scikit-learn model automatically selected after benchmarking
- **Persistence**: SQLite database
- **UI & Dashboard**: Custom Glassmorphism UI 

## Technology Stack
- **Backend Framework**: Flask
- **Machine Learning**: Scikit-learn, Pandas, Joblib
- **Database**: SQLite
- **Frontend**: HTML5, Vanilla CSS, Bootstrap 5.3

## Project Structure
```
SupportPilot/
│
├── app.py                      # Flask application and routing
├── train_model.py              # ML benchmarking and training script
├── classifier.py               # AI classification interface wrapper
├── severity.py                 # Rule-based severity prediction logic
├── priority.py                 # Priority calculation based on severity & impact
├── database.py                 # SQLite database initialization and operations
├── requirements.txt            # Python dependencies
│
├── models/
│   ├── ticket_classifier.pkl   # Serialized best ML model
│   └── vectorizer.pkl          # Serialized TF-IDF vectorizer
│
├── frontend/                   # (Formerly templates/)
│   ├── index.html              # Main ticket form and dashboard
│   ├── my_tickets.html         # User's ticket list
│   └── ticket_result.html      # Classification results view
│
├── assets/                     # (Formerly static/)
│   ├── css/
│   │   └── style.css           # Custom styling (Glassmorphism & animations)
│   └── js/
│       └── app.js              # Frontend interactivity
│
└── tickets.db                  # Local SQLite database
```

## Dataset Explanation
**CRITICAL NOTE**: The current training dataset is embedded directly within `train_model.py`. 
- **Size**: 360 tickets.
- **Categories**: 6 (Network, VPN, Password, Software, Hardware, System).
- **Distribution**: 60 tickets per category.

No external, synthetic, or generated data was introduced. The models are benchmarked exclusively on this existing dictionary dataset as strictly requested.

## ML Models Tested
During training, multiple models are evaluated fairly using a `test_size=0.15` and a stratified train-test split:
- Logistic Regression
- Linear SVC (Calibrated for probability extraction)
- Multinomial Naive Bayes
- Complement Naive Bayes
- SGD Classifier (Log loss)

## Model-Selection Methodology
The pipeline automatically selects the best classifier based on:
1. **Primary Metric**: Macro F1 Score
2. **Secondary Metric**: Accuracy (if tied)
3. **Tertiary Metric**: Weighted F1 (if still tied)

## Training Instructions
To benchmark models and save the best performing one:
```bash
python train_model.py
```
This script will output the benchmarking table to the console, save the best model and vectorizer to the `models/` folder, and generate reports in the `evaluation/` folder.

## Application Startup
Run the Flask server:
```bash
python app.py
```
Then navigate to `http://127.0.0.1:5000` in your web browser.

## API Endpoints

### 1. Submit a Ticket (JSON)
- **POST** `/api/tickets`
- **Request Body**:
```json
{
  "employee_name": "Arun",
  "email": "arun@company.com",
  "title": "VPN not working",
  "description": "Unable to connect to company VPN",
  "department": "Sales",
  "business_impact": "High"
}
```
- **Response**:
```json
{
  "ticket_id": 1,
  "category": "VPN",
  "confidence": 0.94,
  "severity": "High",
  "priority": "P2",
  "status": "Open",
  "model_name": "Logistic Regression"
}
```

### 2. Get All Tickets
- **GET** `/api/tickets`

### 3. Get Single Ticket
- **GET** `/api/tickets/<ticket_id>`

### 4. Get Model Info
- **GET** `/api/model-info`

### 5. Health Check
- **GET** `/api/health`

## Evaluation Methodology
Models are evaluated on a 15% holdout test set (54 tickets). We measure Accuracy, Precision, Recall, Macro F1, Weighted F1, and training time. See `evaluation/model_comparison.csv` for the exact metrics achieved on the actual data.

## Limitations
- **Dataset Size**: The current dataset contains only 360 examples. High accuracy may reflect the dataset's simplicity rather than generalizability to real-world noise.
- **Rule-based Severity**: Severity and priority rely on simple keyword matching rather than ML inference.
- **Simple Preprocessing**: No lemmatization or advanced NLP pipelines (e.g., SpaCy/NLTK) were applied in this MVP version.


## ✅ Milestone 2 Completed

Milestone 2 adds a real Retrieval-Augmented Generation (RAG) pipeline to dynamically retrieve historical IT solutions and generate highly contextual resolution steps using AI.

### RAG Pipeline (
ag/)
- **Ticket Analyzer**: Parses ticket descriptions and generates enriched search queries.
- **Knowledge Base Retriever**: Performs vector/cosine-similarity searches against the 100+ article database (data/knowledge_base.json).
- **Context Builder**: Formats the most relevant historical knowledge base articles.
- **LLM Generator**: Calls OpenRouter (e.g., Llama 3) strictly formatted as JSON to generate the final troubleshooting steps.

## ✅ Milestone 3 Completed

Milestone 3 implements the **Multi-Agent Resolution Workflow**, upgrading SupportPilot from a passive AI assistant into an autonomous AI agent capable of resolving tickets or escalating to human agents.

### Multi-Agent Architecture (gents/)
- **Diagnosis Agent (M1)**: Reuses the foundational M1 classifier to assess category, severity, and priority.
- **Retrieval Agent (M2)**: Searches the knowledge base to locate relevant articles.
- **Resolution Agent (M3)**: Synthesizes actionable troubleshooting steps using OpenRouter LLMs.
- **Validation Agent (M3)**: Evaluates the system's confidence before taking action. Uses a strict **40/40/20 formula**:
  - (Diagnosis Confidence * 0.40) + (Retrieval Score * 0.40) + (Resolution Steps Quality * 0.20)
- **Escalation Agent (M3)**: Executes the final decision:
  - **>= 70% Confidence**: AUTO_RESOLVE. Sends an automated resolution via Email/SMTP.
  - **< 70% Confidence**: ESCALATE. Automatically files a Jira ticket (e.g., KAN-10) for human intervention.

### Integrations (services/)
- **Jira API Integration**: Fully implemented. When the Orchestrator decides to escalate, a real Jira ticket is created in the connected workspace, and the ID is tied back to the SupportPilot ticket.
- **Email/SMTP Integration**: Fully implemented. Auto-resolved tickets trigger a beautifully formatted HTML email containing the generated troubleshooting steps sent directly to the employee.

### Setup Instructions
1. Copy .env.example to .env.
2. Configure the following keys:
   - OPENROUTER_API_KEY (Required for AI generation)
   - JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN, JIRA_PROJECT_KEY (Required for Escalation)
   - SMTP_SERVER, SMTP_PORT, SMTP_EMAIL, SMTP_PASSWORD (Required for Auto-Resolve)
3. Restart the Flask app to load new environment variables.
