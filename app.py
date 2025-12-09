# app.py

import streamlit as st
from search_engine import (
    interpret,
    fetch_by_category,
    fetch_by_subcategory,
    build_pages,
)

st.set_page_config(page_title="AI Semantic Search", layout="wide")

st.title("AI Semantic Search on Local Business Data")

query = st.text_input("Enter search query:")

# Initialize session state
if "pages" not in st.session_state:
    st.session_state.pages = []
if "page" not in st.session_state:
    st.session_state.page = 1
if "result" not in st.session_state:
    st.session_state.result = None
if "city" not in st.session_state:
    st.session_state.city = None


# ----------------- Search Action -----------------

if st.button("Search"):
    if query.strip():
        result, city = interpret(query)
        pages = build_pages(result, city)

        st.session_state.result = result
        st.session_state.city = city
        st.session_state.pages = pages
        st.session_state.page = 1
    else:
        st.warning("Please enter a query.")


# ----------------- Display Results -----------------

if st.session_state.pages and st.session_state.result:

    result = st.session_state.result
    city = st.session_state.city
    pages = st.session_state.pages
    page_idx = st.session_state.page - 1

    current_page = pages[page_idx]
    mode = current_page["mode"]
    value = current_page["value"]

    # Interpretation
    st.subheader("Semantic Interpretation")
    st.write("Corrected Query:", result["corrected_query"])
    st.write("Primary Category:", result["category"])
    st.write("Top Subcategory:", result["subcategory"])
    st.write("Detected City:", city or "None")
    st.write("Overall Confidence:", round(result["score"], 3))
    st.write("Category Score:", round(result["cat_score"], 3))
    st.write("Subcategory Score:", round(result["sub_score"], 3))

    # Current page info
    st.subheader("Current Page")
    st.write(
        f"Page {st.session_state.page}/{len(pages)} | Mode: {mode} | Value: {value}"
    )

    # Fetch data for current page
    if mode == "category":
        df, sql = fetch_by_category(value, city)
    else:
        df, sql = fetch_by_subcategory(value, city)

    st.subheader("Generated SQL")
    st.code(sql, language="sql")

    st.subheader("Results")

    if df.empty:
        st.info("No results found for this page.")
    else:
        for _, r in df.iterrows():
            st.markdown(
                f"""
                <div style='padding:12px;
                            border:1px solid #ccc;
                            margin-bottom:12px;
                            border-radius:8px;'>
                    <h4 style='margin-bottom:4px;'>{r.get('name','')}</h4>
                    <p style='margin:0;'><strong>Address:</strong> {r.get('address','')}</p>
                    <p style='margin:0;'><strong>Phone:</strong> {r.get('phone_number','')}</p>
                    <p style='margin:0;'><strong>Website:</strong> {r.get('website','')}</p>
                    <p style='margin:0;'><strong>Rating:</strong> {r.get('reviews_average','N/A')} 
                        ({r.get('reviews_count','0')} reviews)</p>
                    <p style='margin:0;'><strong>Category:</strong> {r.get('category','')} 
                        — {r.get('subcategory','')}</p>
                    <p style='margin:0;'><strong>Location:</strong> {r.get('city','')}, {r.get('state','')}</p>
                    <p style='margin:0;'><strong>Area:</strong> {r.get('area','')}</p>
                    <p style='margin:0;'><strong>Created At:</strong> {r.get('created_at','')}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Pagination controls
    col1, col2, col3 = st.columns([1, 2, 1])

    if col1.button("Previous") and st.session_state.page > 1:
        st.session_state.page -= 1
        st.rerun()

    col2.write(f"Page {st.session_state.page} / {len(pages)}")

    if (
        st.session_state.page < len(pages)
        and col3.button("Next")
    ):
        st.session_state.page += 1
        st.rerun()

elif query.strip():
    # User searched but no pages were produced
    if st.session_state.result is not None and not st.session_state.pages:
        st.warning("No relevant results found for this query in the database.")
