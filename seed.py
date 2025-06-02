from flask import Flask
from flask_pymongo import PyMongo
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
mongo = PyMongo(app)

def seed_data():
    with app.app_context():
        # Insert 1 Chapter
        chapter_data = {
            "title": "Gerakan Advanced",
            "description": "Teknik-teknik dasar untuk pemula",
            "image_filename": "chapter-3.jpeg"
        }
        chapter_id = mongo.db.chapters.insert_one(chapter_data).inserted_id

        # Insert 5 Lessons dengan data unik
        lessons = [
            {
                "chapter_id": chapter_id,
                "title": "Rise & Releves",
                "description": "Langkah-langkah pemanasan sebelum latihan.",
                "video_url": "https://youtube.com/watch?v=pemanasan123",
                "image_filename": "rr.jpeg"
            },
            {
                "chapter_id": chapter_id,
                "title": "Pas De Bourre",
                "description": "Cara berdiri dan posisi tubuh yang benar.",
                "video_url": "https://youtube.com/watch?v=postur456",
                "image_filename": "pasdebourre.jpeg"
            },
            {
                "chapter_id": chapter_id,
                "title": "Balance",
                "description": "Menguasai kontrol gerakan tangan.",
                "video_url": "https://youtube.com/watch?v=tangan789",
                "image_filename": "balance.jpeg"
            },
            {
                "chapter_id": chapter_id,
                "title": "Saute",
                "description": "Dasar langkah kaki dan koordinasi.",
                "video_url": "https://youtube.com/watch?v=kaki321",
                "image_filename": "saute.jpeg"
            },
            {
                "chapter_id": chapter_id,
                "title": "Temps Leve",
                "description": "Gabungan dari semua teknik dalam latihan ringan.",
                "video_url": "https://youtube.com/watch?v=latihan654",
                "image_filename": "temps_leve.jpeg"
            },
            {
                "chapter_id": chapter_id,
                "title": "Reverence",
                "description": "Gabungan dari semua teknik dalam latihan ringan.",
                "video_url": "https://youtube.com/watch?v=latihan654",
                "image_filename": "reverence.jpeg"
            }
        ]
        mongo.db.lessons.insert_many(lessons) 


        print("✅ Berhasil insert 1 Chapter + 5 Lessons dengan data unik.")

if __name__ == '__main__':
    seed_data()
