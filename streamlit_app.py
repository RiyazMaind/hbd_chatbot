import streamlit as st
import requests

# Use a more descriptive title
st.set_page_config(page_title="HBD Local Business Assistant", layout="wide")

# Ensure API is accessible; change if your FastAPI is hosted elsewhere
API = "http://127.0.0.1:8000/chat" 

if "history" not in st.session_state:
    st.session_state.history = []

st.title("HBD Local Business Assistant")
st.markdown("Ask for local businesses (e.g., *Ayurvedic hospitals in Chirala*) or general info/definitions (e.g., *What is Ayurveda?*)")


def render_business(results):
    """Renders the business results list in the Streamlit chat."""
    for r in results:
        st.markdown("---")
        st.markdown(f"### {r.get('name', 'N/A')}")
        st.caption(r.get("address", ""))
        st.caption(f"{r.get('city', 'N/A')}, {r.get('state', 'N/A')}")
        st.write(f"**Category:** {r.get('category', 'N/A')}")
        if r.get('subcategory'):
            st.write(f"**Subcategory:** {r['subcategory']}")
        st.write(f"**Rating:** {r.get('reviews_average', 'N/A')} ({r.get('reviews_count', 0)} reviews)")


def chat_send(q):
    """Sends the query to the FastAPI backend and updates history."""
    try:
        res = requests.post(API, json={"query": q}).json()
        st.session_state.history.append(("user", q))
        st.session_state.history.append(("bot", res))
    except requests.exceptions.ConnectionError:
        error_msg = {
            "type": "text",
            "answer": "Connection Error: Could not connect to the FastAPI backend. Please ensure the server is running."
        }
        st.session_state.history.append(("user", q))
        st.session_state.history.append(("bot", error_msg))


# Display chat history
for role, msg in st.session_state.history:
    if role == "user":
        st.chat_message("user").write(msg)
    else:
        # Bot's response
        with st.chat_message("assistant"):
            if msg["type"] == "text":
                st.write(msg["answer"])
            elif msg["type"] == "sql":
                results = msg["results"]
                category = msg.get('category', 'businesses')
                city = msg.get('city', 'the area')
                
                if results:
                    st.write(f"Top results for **{category}** in **{city}**:")
                    render_business(results)
                else:
                    # This branch is technically covered by the agent's logic now, but kept as a safeguard
                    st.write(f"I found a category (**{category}**) and city (**{city}**), but there were no listings in the database matching your request.")
            else:
                st.write("An unknown response type was received.")


# User input handling
query = st.chat_input("Ask anything...")
if query:
    chat_send(query)
    st.rerun()