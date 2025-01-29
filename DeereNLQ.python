import openai
from langchain import OpenAI
from langchain.prompts import PromptTemplate
from pymongo import MongoClient

# Example: Use your actual keys and connection strings
openai.api_key = "YOUR_OPENAI_API_KEY"
mongo_client = MongoClient("YOUR_MONGODB_URI")
db = mongo_client["myDatabase"]
collection = db["products"]

# Step 1: Ask user for input
user_input = "Find wireless headphones under $100 with good reviews"

# Step 2: Use an LLM (via LangChain) to parse out filters, keywords, etc.
llm = OpenAI(temperature=0)
parse_prompt = PromptTemplate(
    input_variables=["user_input"],
    template="""
    You are a helper that extracts search parameters from the user's query.
    The user input is: {user_input}
    Return the JSON with structure:
    {{
      "keywords": <string>,
      "price": <number>,
      "similarity": <string to use for moreLikeThis>
    }}
    """
)

parsed_response = llm(parse_prompt.format(user_input=user_input))
# Suppose the LLM returns JSON like:
# { "keywords": "wireless headphones", "price": 100, "similarity": "good reviews" }
# You would parse the JSON. For brevity, we’ll just do a mock parse:
parsed = {
    "keywords": "wireless headphones",
    "price": 100,
    "similarity": "good reviews"
}

# Step 3: Build the MongoDB aggregation
pipeline = [
    {
        "$search": {
            "compound": {
                "must": [
                    {
                        "text": {
                            "query": parsed["keywords"],
                            "path": ["name", "description"]
                        }
                    }
                ],
                "filter": [
                    {
                        "range": {
                            "path": "price",
                            "lte": parsed["price"]
                        }
                    }
                ],
                "should": [
                    {
                        "moreLikeThis": {
                            "path": "reviews",
                            "like": [ parsed["similarity"] ]
                        }
                    }
                ]
            }
        }
    },
    { "$limit": 5 }
]

# Step 4: Execute the query and retrieve documents
results = list(collection.aggregate(pipeline))

# Step 5: Pass results back to LLM for final answer (RAG)
context_snippets = "\n".join(
    [f"- {doc['name']} (${doc['price']}): {doc.get('description', '')}" for doc in results]
)

final_prompt = f"""
User asked: "{user_input}"

We found these products in the database:
{context_snippets}

Now provide a concise answer or recommendation:
"""

final_answer = llm(final_prompt)
print(final_answer)
