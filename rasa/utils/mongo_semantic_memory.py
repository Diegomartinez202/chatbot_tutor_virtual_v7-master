from pymongo import MongoClient
import os
from datetime import datetime

client = MongoClient(os.getenv("MONGO_URI", "mongodb://mongo:27017"))
db = client["rasa"]
collection = db["semantic_memory"]