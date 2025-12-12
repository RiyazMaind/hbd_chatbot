from gpt4all import GPT4All
from tools import semantic_tool, sql_tool

MODEL_NAME = "phi-3-mini-4k-instruct-q4.gguf"
MODEL_PATH = "models"

# NOTE: The semantic threshold is no longer strictly used for SQL decision, 
# but kept here for reference if semantic score needs to be included later.
SEMANTIC_THRESHOLD = 0.65 


class Agent:
    def __init__(self):
        print("Loading model on CPU...")
        try:
            self.model = GPT4All(
                model_name=MODEL_NAME,
                model_path=MODEL_PATH,
                allow_download=False,
                device="cpu"
            )
        except Exception as e:
            print(f"Error loading model: {e}. Model will be unavailable.")
            self.model = None

    # ---------------- LLM classifier (The SQL Detector's Intent Check) ----------------
    def classify_intent(self, query: str) -> bool:
        """
        Uses LLM as a simple YES/NO classifier to detect if a business lookup is intended.
        """
        if not self.model:
            return False 
            
        prompt = f"""
Answer "yes" or "no" only.
Is the user trying to find a business, shop, service, restaurant, or local place?

Query: "{query}"
"""
        out = self.model.generate(prompt, max_tokens=5, temp=0.0) 
        return "yes" in out.lower()

    # ---------------- LLM short explanation (Fallback) ----------------
    def explain(self, query: str):
        """Generates a simple, short explanation or general answer for a query."""
        if not self.model:
            return "I am unable to provide general information as my language model is not available."
            
        prompt = f"""
Provide a helpful and concise answer to the following query. 
If the query asks for a definition or explanation, provide it simply.
If the query is a general question, provide a brief answer.
Keep the answer short and clear (max 3 sentences).

Query: "{query}"
"""
        return self.model.generate(prompt, max_tokens=100).strip()

    # ---------------- Consolidated SQL Detection Logic ----------------
    def is_sql_required(self, query: str) -> dict:
        """
        Determines if the query requires an SQL lookup based on LLM intent (YES/NO) 
        and the necessary parameters (City) being found.
        """
        sem = semantic_tool(query)
        category = sem.get("category")
        city = sem.get("city")
        
        # 1. LLM Check: The simple YES/NO from the model
        llm_says_yes = self.classify_intent(query)
        
        # 2. Parameter Check: SQL requires a city.
        has_required_params = bool(city)
        
        # SQL is required ONLY IF the LLM says "Yes" AND we found the necessary city parameter.
        is_sql = llm_says_yes and has_required_params
        
        return {
            "required": is_sql,
            "category": category,
            "city": city,
            "score": sem.get("score", 0.0) 
        }

    # ---------------- Main Chat Logic ----------------
    def chat(self, query: str):
        
        # Determine the path: SQL or Non-SQL
        detector_result = self.is_sql_required(query)
        
        is_sql = detector_result["required"]
        category = detector_result["category"]
        city = detector_result["city"]

        # 1. SQL Path (If the LLM says 'Yes' AND we have a City)
        if is_sql:
            data = sql_tool(category, city)
            
            # Check for zero results
            if data["data"]:
                return {
                    "type": "sql",
                    "category": category,
                    "city": city,
                    "results": data["data"]
                }
            
            # Fallback for Zero Results (If SQL failed, try general explanation)
            # This is the "Non SQL Results" path in the flowchart when SQL returns 0.
            return {
                "type": "text",
                "answer": self.explain(query)
            }

        # 2. Non-SQL Path (If LLM says 'No' or City is missing)
        # Directly fall back to the general explanation for everything else
        return {
            "type": "text",
            "answer": self.explain(query)
        }