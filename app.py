from fastapi import FastAPI
from pydantic import BaseModel
from agent import Agent

app = FastAPI()
agent = Agent()

class Query(BaseModel):
    query: str

@app.post("/chat")
def chat(q: Query):
    """
    Main chat endpoint to process a user query.
    """
    return agent.chat(q.query)

@app.get("/")
def home():
    """
    Health check endpoint.
    """
    return {"status": "running", "model_loaded": bool(agent.model)}