import os
from urllib.parse import quote_plus

import certifi
from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

load_dotenv()
username = os.getenv("MONGO_DB_USERNAME")
password = os.getenv("MONGO_DB_PASSWORD")

if not username or not password:
    raise RuntimeError(
        "MONGO_DB_USERNAME and MONGO_DB_PASSWORD must be set (e.g. in a .env "
        "file) before running test_mongodb.py.",
    )

username = quote_plus(username)
password = quote_plus(password)

uri: str = f"mongodb+srv://{username}:{password}@cluster0.lbvk3s8.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

client = MongoClient(uri, server_api=ServerApi("1"), tlsCAFile=certifi.where())


# Send a ping to confirm a successful connection
try:
    client.admin.command("ping")
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)
