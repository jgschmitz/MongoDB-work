rom langchain_mongodb.chat_message_histories import MongoDBChatMessageHistory
from pymongo import MongoClient

# Better approach: use LangChain's LLMChain with a prompt template
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pymongo import MongoClient

client = MongoClient("<ATLAS_CONNECTION_STRING>")
db = client["sample_mflix"]
collection = db["movies"]

llm = ChatOpenAI(model="gpt-4", temperature=0)

prompt = PromptTemplate.from_template("""
You are a MongoDB query expert. Convert the natural language request into a MongoDB find() filter as valid JSON only. No explanation.

Collection: movies
Schema: {{ title: string, year: number, genre: string, director: string, imdb: {{ rating: number }} }}

Request: {user_input}

MongoDB filter JSON:
""")

chain = prompt | llm

user_input = "show me all the movies made in 2000"
result = chain.invoke({"user_input": user_input})

# LLM returns: {"year": 2000}
import json
query_filter = json.loads(result.content)

# Execute against Atlas
movies = list(collection.find(query_filter, {"title": 1, "year": 1, "_id": 0}))
print(movies)
