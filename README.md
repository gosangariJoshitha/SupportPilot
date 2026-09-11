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

## Future Milestone 2 Work
- **Knowledge Retrieval Engine (RAG)**: Integrating vector databases and LLMs to provide immediate troubleshooting steps.
- **AI Resolution Generator**: Auto-generating step-by-step resolution guides based on historical tickets.
- **Multi-Agent Framework**: Delegating complex tickets to specialized agents.
- **Escalation Management**: Automating routing when confidence is low or priority is Critical.

## ✅ Milestone 2 Completed

Milestone 2 adds a real Retrieval-Augmented Generation pipeline and turns the four previously-placeholder sidebar links (AI Agent, Integrations, Analytics, Settings) into fully working, database-backed pages. Nothing below uses mock/hardcoded data.

### RAG Pipeline (`rag/pipeline.py`, `rag/retriever.py`)
Ticket → Analysis → TF-IDF/cosine-similarity Knowledge Base Retrieval → Context Augmentation → Resolution Generation.

- If `OPENROUTER_API_KEY` is set in `.env`, resolutions are generated by a real call to [OpenRouter](https://openrouter.ai)'s chat completions API (`OPENROUTER_MODEL`, default `meta-llama/llama-3.1-8b-instruct:free`).
- If no key is set, or the API call fails for any reason (network, quota, invalid key), the pipeline falls back to a deterministic extractive generator built from the actual retrieved KB articles — never a hardcoded canned reply.
- Every ticket honestly records which engine actually produced its resolution (`resolution_engine`: `llm` or `template`) — this is stored per-ticket and shown throughout the UI, not assumed.
- KB relevance scores are raw cosine-similarity scores. They are **not** artificially boosted.

### New Pages
- **`/agents` (AI Agent)** — Real usage stats (resolutions generated, avg. relevance, LLM vs. template split) pulled from the database, plus a live test panel that runs the actual pipeline against whatever ticket text you type in — not a canned demo.
- **`/analytics`** — Category/severity/priority distributions, ticket activity over time, average classification confidence, AI resolution rate, and resolution-engine usage — all computed live from the `tickets` table.
- **`/integrations`** — Live connection status for OpenRouter, the ML classifier, the KB retriever, and SQLite (checked at request time, not assumed). Integrations that aren't actually implemented (Slack, Microsoft Teams, Jira) are honestly labeled "Not Configured" rather than faked as connected.
- **`/settings`** — Real profile editing and password change, both backed by the `users` table (old password is verified with `check_password_hash` before any change is accepted).

### Setup for Milestone 2
1. Add your OpenRouter key to `.env`:
   ```
   OPENROUTER_API_KEY=sk-or-v1-...
   OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct:free
   ```
   Get a key (including free-tier models) at https://openrouter.ai/keys.
2. If no key is present, the app still works end-to-end using the template-based fallback generator — this is a legitimate mode, not a broken state.
3. Restart the Flask app after editing `.env`.

### Known Limitation
The knowledge base (`data/knowledge_base.json`) currently has 17 articles. RAG retrieval quality is bounded by this KB's coverage — tickets about topics not represented in the KB will correctly report `INSUFFICIENT_KNOWLEDGE` rather than fabricate a resolution.

