import os
import pymongo

def get_connection():
    # Connect to MongoDB instance
    mongo_uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017/budgetplanner")
    client = pymongo.MongoClient(mongo_uri)
    return client.get_default_database()