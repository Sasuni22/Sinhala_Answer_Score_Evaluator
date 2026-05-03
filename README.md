# SinhalaScore AI 🎯
## Offline Intelligent Sinhala Open-Ended Answer Scorer
### Ancient Sri Lanka — Anuradhapura Period | NLP CW-II

---

## 📁 Project Structure

```
sinhalascore/
├── app.py                          # Main Streamlit application
├── setup.py                        # One-time setup script
├── requirements.txt                # Python dependencies
├── .streamlit/
│   └── config.toml                 # Streamlit dark theme config
│
├── data/
│   ├── questions.py                # 5 Questions + Marking Guides (Sinhala)
│   ├── chroma_db/                  # ChromaDB vector store (auto-generated)
│   └── knowledge_base/             # RAG source documents
│       ├── water_management.txt    # Irrigation & reservoirs
│       ├── buddhism.txt            # Buddhist civilization
│       ├── administration.txt      # Kings & administration
│       ├── trade_relations.txt     # Foreign trade
│       └── defense.txt             # Military & defense
│
├── ontology/
│   └── anuradhapura_ontology.py    # OWL ontology (RDFLib)
│
├── rag/
│   └── retriever.py                # ChromaDB + SentenceTransformers RAG
│
├── agents/
│   ├── agents.py                   # 4 Agent classes
│   └── pipeline.py                 # Agent orchestrator
│
└── utils/
    └── helpers.py                  # Grade/color/format utilities
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- [Ollama](https://ollama.ai) installed and running

### 1. Install Dependencies
```bash
cd sinhalascore
pip install -r requirements.txt
```

### 2. Pull Ollama Model (Offline)
```bash
ollama pull llama3.2:3b
```
> Use `llama3.2:3b` (fast, good multilingual), or `mistral:7b` for better quality.

### 3. Build Knowledge Base
```bash
python setup.py
```

### 4. Launch the App
```bash
streamlit run app.py
```

---

## 🏗️ System Architecture

```
Student Answer
      │
      ▼
[RAG Retriever] ──────────────► ChromaDB + SentenceTransformers
      │                         (paraphrase-multilingual-MiniLM)
      ▼
[Ontology Extractor] ─────────► RDFLib OWL Graph
      │                         (Kings, Stupas, Reservoirs, etc.)
      ▼
[Coverage Checker Agent] ─────► Checks which criteria are covered
      │
      ▼
[Scorer Agent] ───────────────► Assigns marks per criterion
      │
      ▼
[Explanation Agent] ──────────► Generates Sinhala+English feedback
      │
      ▼
[Consistency Checker] ────────► Validates total score is correct
      │
      ▼
    Score /20 + Breakdown + Explanation
```

---

## 📋 Question Scope: Ancient Sri Lanka (Anuradhapura Period)

| ID | Topic | Max Marks |
|----|-------|-----------|
| Q1 | Water Management Systems | 20 |
| Q2 | Buddhist Civilization | 20 |
| Q3 | Administration & Kings | 20 |
| Q4 | Foreign Relations & Trade | 20 |
| Q5 | Defense & Sovereignty | 20 |

---

## 🤖 Agent Responsibilities

| Agent | Responsibility |
|-------|----------------|
| **CoverageCheckerAgent** | Determines which marking criteria the student addressed |
| **ScorerAgent** | Assigns marks per criterion using LLM + RAG + ontology evidence |
| **ExplanationAgent** | Writes explainable, evidence-based feedback in Sinhala + English |
| **ConsistencyCheckerAgent** | Validates score total matches breakdown; applies fallback if needed |

---

## 🔧 Configuration

In `settings` page you can:
- Switch between Ollama models
- Rebuild the knowledge base vector index
- View ontology statistics
- Clear evaluation history

---

## 📝 Notes

- **Fully Offline**: No internet required during evaluation
- **Fallback Mode**: If Ollama is unavailable, keyword-based scoring is used
- **Sinhala Unicode**: All Sinhala text uses UTF-8 / Unicode
- **RAG Model**: `paraphrase-multilingual-MiniLM-L12-v2` (downloads once, then offline)
