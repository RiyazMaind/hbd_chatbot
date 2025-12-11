# Local Business Assistant (LLM + Semantic Search + MySQL)

This project is an intelligent assistant that understands natural language queries and returns accurate business results from a MySQL database. It runs entirely offline using a local LLM (Phi-3 Mini GGUF) and includes semantic search, fuzzy correction, city detection, and a Streamlit chat interface.

The system automatically decides whether a query needs:

1. A normal LLM explanation (example: "What is SEO")
2. A business lookup in MySQL (example: "best biryani in chirala")

The system does not rely on keyword rules. Instead, it uses:

- A local LLM classifier
- Semantic embeddings for categories and subcategories
- Fuzzy matching for city detection
- SQL scoring based on reviews ranking

---

## Features

### Natural Language Understanding

- Understands queries written in casual style
- Automatically detects user intent (definition vs business search)
- Corrects spelling mistakes before processing

### Semantic Search

- Embedding-based similarity detection for categories and subcategories
- Weighted semantic scoring to determine best business match

### Local LLM

- Uses Phi-3 Mini 4K Instruct (GGUF)
- Fully CPU compatible
- No internet required

### Database Integration

- MySQL business listings table
- SQL ranking using review-based scoring
- Top 5 business results returned for each query

### Streamlit Chat UI

- User-friendly chat interface
- Business cards with ratings, address, and category
- History preserved in session

---

## Project Structure

```
ChatBot/
    agent.py
    app.py
    streamlit_app.py
    search_engine.py
    tools.py
    db_config.py
    utils.py
    requirements.txt
    .gitignore
    models/
        phi-3-mini-4k-instruct-q4.gguf
```

---

## How It Works

### 1. Intent Detection

Every query is classified using a local LLM:

- If the intent is to find a business, the system switches to SQL mode.
- If the intent is educational, the system generates a short explanation.

### 2. Semantic Interpretation

The query is normalized and encoded using a sentence transformer model.
The system identifies:

- Best category
- Best subcategory
- City
- Confidence score

### 3. SQL Execution

For business queries, SQL is generated dynamically:

- Filters based on category
- Filters by city if detected
- Ranks results using `(rating * log(reviews))`
- Returns top 5 businesses

### 4. Streamlit UI

The interface displays:

- User queries
- Assistant replies
- Business cards
- Search history

---

## Requirements

Install dependencies:

```
pip install -r requirements.txt
```

Required software:

- Python 3.10 or newer
- MySQL server
- SentenceTransformers
- GPT4All
- Streamlit
- FastAPI + Uvicorn

Place the LLM model inside:

```
models/phi-3-mini-4k-instruct-q4.gguf
```

---

## Environment Variables

Create a `.env` file:

```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=google_maps
```

Never upload `.env` to GitHub.

---

## Running the Backend (FastAPI)

```
uvicorn app:app --reload
```

API will run at:

```
http://127.0.0.1:8000/chat
```

---

## Running the Streamlit App

```
streamlit run streamlit_app.py
```

The interface opens automatically.

---

## Database Structure

The SQL engine expects a table:

```
google_maps_listings
```

With fields including:

- id
- name
- address
- phone_number
- website
- reviews_count
- reviews_average
- category
- subcategory
- city
- state
- area
- created_at

---

## Notes

- This system does not require any external API or cloud inference.
- All processing is offline.
- The system is optimized for speed and relevance on CPU.
