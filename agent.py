# agent.py
from gpt4all import GPT4All
from tools import semantic_tool, sql_tool

MODEL_NAME = "phi-3-mini-4k-instruct-q4.gguf"
MODEL_PATH = "models"

SEMANTIC_THRESHOLD = 0.60

DEFINITION_KEYWORDS = [
    "what is", "explain", "meaning of", "define",
    "how does", "what are"
]


class Agent:
    def __init__(self):
        print("Loading model on CPU...")
        self.model = GPT4All(
            model_name=MODEL_NAME,
            model_path=MODEL_PATH,
            allow_download=False,
            device="cpu"
        )

    # ---------------- LLM classifier ----------------
    def classify_intent(self, query: str) -> bool:
        prompt = f"""
Answer "yes" or "no" only.
Is the user trying to find a business, shop, service or local place?

Query: "{query}"
"""
        out = self.model.generate(prompt, max_tokens=3)
        return "yes" in out.lower()

    def is_definition_query(self, q: str):
        q = q.lower()
        return any(q.startswith(k) for k in DEFINITION_KEYWORDS)

    # ---------------- LLM short explanation ----------------
    def explain(self, query: str):
        prompt = f"""
Explain '{query}' in very simple words.
Use plain English, no technical terms.
Keep it short and clear.
"""
        return self.model.generate(prompt, max_tokens=90).strip()

    # ---------------- Main Chat Logic ----------------
    def chat(self, query: str):
        sem = semantic_tool(query)
        category = sem["category"]
        city = sem["city"]
        score = sem["score"]

        llm_says_business = self.classify_intent(query)
        business_intent = llm_says_business and score >= SEMANTIC_THRESHOLD
        definition_intent = self.is_definition_query(query)

        # Definition only
        if definition_intent and not business_intent:
            return {
                "type": "text",
                "answer": self.explain(query)
            }

        # Business only
        if business_intent and not definition_intent:
            data = sql_tool(category, city)
            return {
                "type": "sql",
                "category": category,
                "city": city,
                "results": data["data"]
            }

        # Mixed — choose dominant
        if definition_intent and business_intent:
            if definition_intent:
                return {
                    "type": "text",
                    "answer": self.explain(query)
                }
            else:
                data = sql_tool(category, city)
                return {
                    "type": "sql",
                    "category": category,
                    "city": city,
                    "results": data["data"]
                }

        # Fallback
        return {
            "type": "text",
            "answer": "I could not understand your request."
        }
