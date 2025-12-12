# search_engine.py
import numpy as np
import pandas as pd
from rapidfuzz import fuzz, process
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from utils import normalize
from db_config import get_connection

# Load DB
conn = get_connection()
cur = conn.cursor()

# Load embedder
embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


# -------------------- Load Labels --------------------

def load_labels(sql):
    cur.execute(sql)
    rows = cur.fetchall()
    labels = [normalize(r[0]) for r in rows if r[0]]
    embeds = embedder.encode(labels, convert_to_numpy=True)
    return labels, embeds


CATEGORY_LABELS, CAT_EMBEDS = load_labels(
    "SELECT DISTINCT category FROM google_maps_listings"
)

SUBCATEGORY_LABELS, SUB_EMBEDS = load_labels(
    "SELECT DISTINCT subcategory FROM google_maps_listings WHERE subcategory IS NOT NULL AND subcategory!=''"
)

cur.execute("SELECT DISTINCT city FROM google_maps_listings")
CITIES = [normalize(r[0]) for r in cur.fetchall() if r[0]]

# -------------------- Fuzzy Word Correction --------------------

WORD_VOCAB = sorted(set(
    w for label in (CATEGORY_LABELS + SUBCATEGORY_LABELS + CITIES)
    for w in label.split()
))


def correct_word(w):
    m = process.extractOne(w, WORD_VOCAB, scorer=fuzz.WRatio)
    if m and m[1] >= 80:
        return m[0]
    return w


def correct_query(q):
    q = normalize(q)
    tokens = q.split()
    return " ".join(correct_word(t) for t in tokens)


# -------------------- Semantic Interpretation --------------------

def interpret(query: str):
    q = correct_query(query)
    q_vec = embedder.encode([q], convert_to_numpy=True)

    # Category similarity
    cat_sim = cosine_similarity(CAT_EMBEDS, q_vec).reshape(-1)
    best_cat = CATEGORY_LABELS[int(np.argmax(cat_sim))]
    cat_score = float(np.max(cat_sim))

    # Subcategory similarity
    if len(SUBCATEGORY_LABELS):
        sub_sim = cosine_similarity(SUB_EMBEDS, q_vec).reshape(-1)
        best_sub = SUBCATEGORY_LABELS[int(np.argmax(sub_sim))]
        sub_score = float(np.max(sub_sim))
    else:
        best_sub, sub_score = "", 0

    # Weighted final
    score = 0.7 * cat_score + 0.3 * sub_score

    # City detection
    city = None
    for c in CITIES:
        if fuzz.WRatio(c, q) >= 85:
            city = c
            break

    return {
        "corrected": q,
        "category": best_cat,
        "subcategory": best_sub,
        "city": city,
        "score": score,
    }


# -------------------- SQL Fetch --------------------

def fetch(category: str, city: str | None, limit=5):
    category = normalize(category)

    sql = f"""
    SELECT *,
      (reviews_average * LOG(reviews_count + 1)) AS score
    FROM google_maps_listings
    WHERE LOWER(category) = '{category}'
    """
    if city:
        sql += f" AND LOWER(city) = '{city}'"

    sql += " ORDER BY score DESC LIMIT 50"

    cur.execute(sql)
    rows = cur.fetchall()
    cols = [c[0] for c in cur.description]

    df = pd.DataFrame(rows, columns=cols)
    df = df.drop_duplicates(subset=["name", "address"], keep="first")

    return df.head(limit), sql
