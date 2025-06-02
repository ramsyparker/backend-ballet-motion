from pymongo import MongoClient

# Ganti password dan connection string sesuai yang berhasil tadi
connection_string = "mongodb+srv://novalaula486:Test1234@cluster0.7ovcl59.mongodb.net/?retryWrites=true&w=majority&authSource=admin"
client = MongoClient(connection_string)

# Akses database dan koleksi
db = client["ballet_app"]  # kamu bebas beri nama, misal: ballet_app
collection = db["users"]   # nama koleksi, misalnya: users

# Data yang akan dimasukkan
data = {
    "username": "ballet_user1",
    "email": "ballet1@example.com",
    "role": "student",
    "created_at": "2025-05-21"
}

# Insert data
result = collection.insert_one(data)
print("✅ Data berhasil dimasukkan dengan _id:", result.inserted_id)
