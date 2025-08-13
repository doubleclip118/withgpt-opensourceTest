import os
from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME", "withgpt")
RAW_COL = os.getenv("RAW_COL", "raw_data_jeongwoo")
DST_COL = os.getenv("DST_COL", "Rmx")

if not MONGODB_URI:
    raise RuntimeError("MONGODB_URI is not set. Check your .env")

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]
raw_col = db[RAW_COL]
dst_col = db[DST_COL]

# 인덱스(선택)
raw_col.create_index([("decision", ASCENDING), ("_id", ASCENDING)])
dst_col.create_index([("source_id", ASCENDING)], unique=False)
