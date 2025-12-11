# streamlit_app.py
import streamlit as st
import requests

st.set_page_config(page_title="Local Business Assistant", layout="wide")

API = "http://127.0.0.1:8000/chat"

if "history" not in st.session_state:
    st.session_state.history = []

st.title("Local Business Assistant")


def render_business(results):
    for r in results:
        st.markdown("---")
        st.markdown(f"### {r['name']}")
        st.caption(r.get("address", ""))
        st.caption(f"{r['city']}, {r['state']}")
        st.write(f"Category: {r['category']}")
        st.write(f"Subcategory: {r['subcategory']}")
        st.write(f"Rating: {r['reviews_average']} ({r['reviews_count']} reviews)")


def chat_send(q):
    res = requests.post(API, json={"query": q}).json()
    st.session_state.history.append(("user", q))
    st.session_state.history.append(("bot", res))


for role, msg in st.session_state.history:
    if role == "user":
        st.chat_message("user").write(msg)
    else:
        if msg["type"] == "text":
            st.chat_message("assistant").write(msg["answer"])
        else:
            st.chat_message("assistant").write(
                f"Top results for {msg['category']} in {msg['city']}:"
            )
            render_business(msg["results"])

query = st.chat_input("Ask anything...")
if query:
    chat_send(query)
    st.experimental_rerun()
