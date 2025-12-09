## Project Overview

This project provides an AI-driven semantic search interface for a local business database. The system converts natural language queries into structured search against a MySQL database.

Example queries:

- best seo service in chirala
- biryani restaurants in chirala
- cheap hostel near me
- seo agency chiral

The system understands user intent even with spelling mistakes and partial text. It extracts relevant business categories, subcategories and city names, and generates SQL queries dynamically.

The application uses:

- Sentence Transformers for semantic similarity
- RapidFuzz for spelling correction
- Streamlit for the user interface
- MySQL for structured data storage

---

## Features

1. Semantic understanding of user queries
   The model identifies the closest matching category and subcategory from the database.

2. Spelling correction
   Misspelled words like "sercvice" or "chiral" are corrected using fuzzy matching.

3. City detection
   Cities present in user input are recognized using fuzzy similarity.

4. Automatic SQL generation
   SQL queries are formed based on detected category, subcategory and city.

5. Pagination
   Page 1 shows main category results.
   Page 2 shows subcategory results.
   Following pages show results from similar categories.

6. Duplicate removal
   Duplicate business records are removed using name and address.

7. Full business card view
   Business entries show name, address, phone number, website, ratings, reviews, category, subcategory, location and creation date.

8. CPU friendly
   Works locally without GPU.

---

## Project Structure

```
semantic_search/
│
├── app.py                  Streamlit UI
├── search_engine.py        Semantic logic and SQL generation
├── utils.py                Text normalization utilities
├── db_config.py            MySQL connection setup
├── requirements.txt        Python package list
```

---

## Requirements

Python 3.9 or above is recommended.

Install dependencies:

```
pip install -r requirements.txt
```

The project uses the following libraries:

- sentence-transformers
- rapidfuzz
- pandas
- numpy
- scikit-learn
- mysql-connector-python
- streamlit

---

## Database Setup

Create a MySQL database named `maps_scraper_db` and a table named `google_maps_listings`.

Required columns:

```
id
name
address
website
phone_number
reviews_count
reviews_average
category
subcategory
city
state
area
created_at
```

Import your data into this table.

Update the database credentials in `db_config.py`.

```
host="localhost"
user="root"
password="YOUR_PASSWORD"
database="maps_scraper_db"
```

---

## How It Works

1. User enters a query in natural language.
2. Text is normalized and corrected using fuzzy matching.
3. The model embeds the query and compares it with known categories and subcategories stored in the database.
4. Based on similarity scores, it selects the primary category and subcategory.
5. A SQL query is generated using these terms, including city if detected.
6. Results are fetched, sorted and displayed with pagination.
7. Similar categories are used for further pages when available.

---

## Running the Application

Start the Streamlit app:

```
streamlit run app.py
```

This opens the user interface in your web browser.
Enter queries in the search box to fetch results.

---

## Notes

- The system relies on the quality of category and subcategory values present in the database.
- Spelling correction depends on existing category, subcategory and city names.
- For best results, ensure consistency in category naming in the database.
