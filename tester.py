from pymongo import MongoClient

# Replace the following with your MongoDB connection details
client = MongoClient("mongodb://localhost:27017/")
db = client["recipes"]
collection = db["2M_recipes"]

# Fetch all documents
documents = collection.find()

# Update each document with the position field
for position, document in enumerate(documents):
    collection.update_one({"_id": document["_id"]}, {"$set": {"position": position}})

print("Position field added to all documents.")