from pymongo import MongoClient

# Ganti dengan URI kamu
uri = "mongodb+srv://balletmotion30:Password30@capstone.a6u5hbn.mongodb.net/ballet_motion?retryWrites=true&w=majority&appName=Capstone"

try:
        client = MongoClient(uri)
        db = client["ballet_motion"]
        # Ambil dan tampilkan semua nama koleksi
        collections = db.list_collection_names()
        print("✅ Koleksi dalam database 'ballet_motion':")
        for col in collections:
            print("-", col)
except Exception as e:
        print("Terjadi kesalahan:", e)