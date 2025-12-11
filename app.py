# app.py
from fastapi import FastAPI
from pydantic import BaseModel
from agent import Agent

app = FastAPI()
agent = Agent()

class Query(BaseModel):
    query: str

@app.post("/chat")
def chat(q: Query):
    return agent.chat(q.query)

@app.get("/")
def home():
    return {"status": "running"}
