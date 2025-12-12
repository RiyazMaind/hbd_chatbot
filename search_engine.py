import numpy as np
import pandas as pd
from rapidfuzz import fuzz, process
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re

from utils import normalize
from db_config import get_connection

# Load DB and embedder once
CONN = get_connection()
CUR = CONN.cursor() if CONN else None
EMBEDDER = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


# -------------------- Load Labels --------------------

def load_labels(sql):
    """Fetches distinct labels and their embeddings from the database."""
    if not CUR:
        return [], np.array([])
    
    CUR.execute(sql)
    rows = CUR.fetchall()
    labels = [normalize(r[0]) for r in rows if r[0]]
    # Handle the case where no labels are found
    if not labels:
        return [], np.array([])
        
    embeds = EMBEDDER.encode(labels, convert_to_numpy=True)
    return labels, embeds


CATEGORY_LABELS, CAT_EMBEDS = load_labels(
    "SELECT DISTINCT category FROM google_maps_listings"
)

SUBCATEGORY_LABELS, SUB_EMBEDS = load_labels(
    "SELECT DISTINCT subcategory FROM google_maps_listings WHERE subcategory IS NOT NULL AND subcategory!=''"
)

if CUR:
    CUR.execute("SELECT DISTINCT city FROM google_maps_listings")
    CITIES = [normalize(r[0]) for r in CUR.fetchall() if r[0]]
else:
    CITIES = []

# -------------------- Fuzzy Word Correction --------------------

WORD_VOCAB = sorted(set(
    w for label in (CATEGORY_LABELS + SUBCATEGORY_LABELS + CITIES)
    for w in label.split()
))


def correct_word(w):
    """Corrects a single word using fuzzy matching against the vocabulary."""
    m = process.extractOne(w, WORD_VOCAB, scorer=fuzz.WRatio)
    if m and m[1] >= 90: # High threshold for precise correction
        return m[0]
    return w


def correct_query(q):
    """Corrects the whole query word by word."""
    q = normalize(q)
    tokens = q.split()
    return " ".join(correct_word(t) for t in tokens)


# -------------------- Semantic Interpretation --------------------

def detect_city(query: str):
    """Detects a city in the query using fuzzy matching."""
    q = normalize(query)
    best_city = None
    best_score = 0
    
    # Check for words that are highly similar to a city name
    for c in CITIES:
        score = fuzz.WRatio(c, q)
        if score >= 85 and score > best_score:
            best_city = c
            best_score = score
            
    # Remove the city name from the query if found to refine category search
    search_query = q
    if best_city:
        # Simple regex to remove the city name and surrounding punctuation/space
        pattern = re.compile(re.escape(best_city), re.IGNORECASE)
        query_without_city = pattern.sub('', q).strip()
        # Clean up remaining non-alphanumeric characters (like 'in')
        search_query = re.sub(r'\s+in\s+', ' ', query_without_city).strip()
        search_query = normalize(search_query)

    return best_city, search_query


def interpret(query: str):
    """Performs semantic interpretation of the corrected query."""
    if not CAT_EMBEDS.size:
        return {
            "corrected": query, "category": None, "subcategory": None, 
            "city": None, "score": 0.0
        }
        
    # 1. City Detection and Query Refinement
    city, search_query = detect_city(query)
    
    # 2. Query Correction and Embedding for Category/Subcategory
    q = correct_query(search_query)
    q_vec = EMBEDDER.encode([q], convert_to_numpy=True)

    # Category similarity
    cat_sim = cosine_similarity(CAT_EMBEDS, q_vec).reshape(-1)
    best_cat = CATEGORY_LABELS[int(np.argmax(cat_sim))]
    cat_score = float(np.max(cat_sim))

    # Subcategory similarity (if available)
    best_sub, sub_score = None, 0.0
    if SUB_EMBEDS.size:
        sub_sim = cosine_similarity(SUB_EMBEDS, q_vec).reshape(-1)
        best_sub = SUBCATEGORY_LABELS[int(np.argmax(sub_sim))]
        sub_score = float(np.max(sub_sim))

    # Weighted final score for business intent
    score = 0.7 * cat_score + 0.3 * sub_score

    return {
        "corrected": q,
        "category": best_cat,
        "subcategory": best_sub,
        "city": city,
        "score": score,
    }


# -------------------- SQL Fetch --------------------

def fetch(category: str, city: str | None, limit=5):
    """Fetches top listings for a given category and optional city."""
    if not CUR:
        return pd.DataFrame(), ""
        
    category = normalize(category)
    city_normalized = normalize(city) if city else None
    
    # Use parameters to prevent SQL Injection
    params = [category]
    
    sql = """
    SELECT *,
      (reviews_average * LOG(reviews_count + 1)) AS score
    FROM google_maps_listings
    WHERE LOWER(category) = %s
    """
    if city_normalized:
        sql += " AND LOWER(city) = %s"
        params.append(city_normalized)

    sql += " ORDER BY score DESC LIMIT 50"

    try:
        CUR.execute(sql, params)
        rows = CUR.fetchall()
        cols = [c[0] for c in CUR.description]
    except Exception as err:
        print(f"SQL Error: {err}")
        return pd.DataFrame(), ""

    df = pd.DataFrame(rows, columns=cols)
    # Filter for quality and uniqueness
    df = df[df['reviews_count'] > 5] # Only show businesses with a few reviews
    df = df.drop_duplicates(subset=["name", "address"], keep="first")

    return df.head(limit), sql