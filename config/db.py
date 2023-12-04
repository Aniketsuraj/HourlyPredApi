from pymongo.mongo_client import MongoClient

host = "localhost"
port = 27017
db = "pvvnl"
collection = "predict"
MONGO_URL = f"mongodb://{host}:{port}"
client = MongoClient(MONGO_URL)

db1 = client[db]
collection_name = db1[collection]
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)