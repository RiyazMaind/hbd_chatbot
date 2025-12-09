# search_engine.py

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from rapidfuzz import process, fuzz

from utils import normalize
from db_config import get_connection

# ------------------ DB & Model Setup ------------------

connection = get_connection()
cursor = connection.cursor()

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
embedder = SentenceTransformer(MODEL_NAME)


# ------------------ Load Vocab From DB ------------------

def load_categories():
    cursor.execute("SELECT DISTINCT category FROM google_maps_listings")
    rows = cursor.fetchall()
    labels = [normalize(r[0]) for r in rows if r[0]]
    return labels, embedder.encode(labels, convert_to_numpy=True)


def load_subcategories():
    cursor.execute("""
        SELECT DISTINCT subcategory 
        FROM google_maps_listings 
        WHERE subcategory IS NOT NULL AND subcategory != ''
    """)
    rows = cursor.fetchall()
    labels = [normalize(r[0]) for r in rows if r[0]]
    return labels, embedder.encode(labels, convert_to_numpy=True)


def load_cities():
    cursor.execute("SELECT DISTINCT city FROM google_maps_listings")
    rows = cursor.fetchall()
    return [normalize(r[0]) for r in rows if r[0]]


CATEGORY_LABELS, CAT_EMBEDS = load_categories()
SUBCATEGORY_LABELS, SUB_EMBEDS = load_subcategories()
CITIES = load_cities()

# word-level vocabulary for fuzzy correction
WORD_VOCAB = sorted(
    set(
        w
        for label in (CATEGORY_LABELS + SUBCATEGORY_LABELS + CITIES)
        for w in label.split()
        if w
    )
)


# ------------------ Fuzzy Spell Correction ------------------

def correct_word(word: str) -> str:
    """
    Fuzzy-correct a single word using WORD_VOCAB.
    """
    if not word:
        return word
    match = process.extractOne(word, WORD_VOCAB, scorer=fuzz.WRatio)
    if match and match[1] >= 80:
        return match[0]
    return word


def correct_query(query: str) -> str:
    """
    Tokenize query and fuzzy-correct each token using vocab words.
    """
    norm = normalize(query)
    tokens = norm.split()
    corrected_tokens = [correct_word(t) for t in tokens]
    return " ".join(corrected_tokens)


# ------------------ Semantic Interpretation ------------------

def interpret(query: str):
    """
    Interpret user query:
      - Correct spelling
      - Find best category & subcategory by similarity
      - Find similar categories for later pages
      - Fuzzy detect city
    Returns:
      result: {
        "category": <str>,
        "subcategory": <str>,
        "similar": [<str>, ...],
        "score": float,
        "cat_score": float,
        "sub_score": float,
        "corrected_query": <str>
      }
      city: <str or None>
    """
    corrected = correct_query(query)
    q = corrected
    q_vec = embedder.encode([q], convert_to_numpy=True)

    # 1) Category similarity
    cat_sims = cosine_similarity(CAT_EMBEDS, q_vec).reshape(-1)
    cat_sorted_idx = np.argsort(-cat_sims)
    best_cat_idx = cat_sorted_idx[0]
    best_cat = CATEGORY_LABELS[best_cat_idx]
    best_cat_score = float(cat_sims[best_cat_idx])

    # 2) Subcategory similarity
    if len(SUBCATEGORY_LABELS) > 0:
        sub_sims = cosine_similarity(SUB_EMBEDS, q_vec).reshape(-1)
        sub_sorted_idx = np.argsort(-sub_sims)
        best_sub_idx = sub_sorted_idx[0]
        best_sub = SUBCATEGORY_LABELS[best_sub_idx]
        best_sub_score = float(sub_sims[best_sub_idx])
    else:
        best_sub = ""
        best_sub_score = 0.0

    # 3) Combined score
    final_score = best_cat_score * 0.6 + best_sub_score * 0.4

    # 4) Similar categories (for later pages)
    similar_categories = [
        CATEGORY_LABELS[i]
        for i in cat_sorted_idx[1:6]  # top 5 similar after primary
    ]

    # 5) City detection (fuzzy)
    city = None
    for c in CITIES:
        if fuzz.WRatio(c, q) >= 85:
            city = c
            break

    result = {
        "category": best_cat,
        "subcategory": best_sub,
        "similar": similar_categories,
        "score": float(final_score),
        "cat_score": best_cat_score,
        "sub_score": best_sub_score,
        "corrected_query": corrected,
    }
    return result, city


# ------------------ DB Fetch Helpers ------------------

def fetch_by_category(cat: str, city: str | None):
    cat = normalize(cat)
    sql = f"""
    SELECT *,
       (reviews_average * LOG(reviews_count + 1)) AS score
    FROM google_maps_listings
    WHERE LOWER(category) = '{cat}'
    """
    if city:
        sql += f" AND LOWER(city) = '{city}'"
    sql += " ORDER BY score DESC LIMIT 20"  # fetch more, dedupe later

    cursor.execute(sql)
    rows = cursor.fetchall()
    cols = [c[0] for c in cursor.description]
    df = pd.DataFrame(rows, columns=cols)
    if not df.empty:
        df = df.drop_duplicates(subset=["name", "address"], keep="first")
    return df.head(5), sql  # return max 5 rows


def fetch_by_subcategory(sub: str, city: str | None):
    sub = normalize(sub)
    if not sub:
        return pd.DataFrame(), ""

    sql = f"""
    SELECT *,
       (reviews_average * LOG(reviews_count + 1)) AS score
    FROM google_maps_listings
    WHERE LOWER(subcategory) = '{sub}'
    """
    if city:
        sql += f" AND LOWER(city) = '{city}'"
    sql += " ORDER BY score DESC LIMIT 20"

    cursor.execute(sql)
    rows = cursor.fetchall()
    if not rows:
        return pd.DataFrame(), sql
    cols = [c[0] for c in cursor.description]
    df = pd.DataFrame(rows, columns=cols)
    df = df.drop_duplicates(subset=["name", "address"], keep="first")
    return df.head(5), sql


# ------------------ Build Paginated Pages ------------------

def build_pages(result: dict, city: str | None):
    """
    Build list of page definitions:
      - Page 1: primary category
      - Page 2: primary subcategory
      - Page 3+: similar categories
    Skip pages that produce no data.
    """
    pages = []

    primary_cat = result["category"]
    primary_sub = result["subcategory"]
    similar = result["similar"]

    # candidate pages
    candidates = []

    # Page 1: Category
    candidates.append({"mode": "category", "value": primary_cat})

    # Page 2: Subcategory (if any)
    if primary_sub:
        candidates.append({"mode": "subcategory", "value": primary_sub})

    # Page 3+: Similar categories
    for s in similar:
        candidates.append({"mode": "category", "value": s})

    # now filter out pages that have no results
    final_pages = []
    for p in candidates:
        if p["mode"] == "category":
            df, _ = fetch_by_category(p["value"], city)
        else:
            df, _ = fetch_by_subcategory(p["value"], city)

        if not df.empty:
            final_pages.append(p)

    return final_pages
