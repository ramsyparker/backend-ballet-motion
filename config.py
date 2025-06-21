import os
from datetime import timedelta

class Config:
    GOOGLE_CLIENT_ID = "582378404984-ckh17s4d1jut74338h4drf8h8186bqbp.apps.googleusercontent.com"
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key'
    MONGO_URI = 'mongodb+srv://balletmotion30:Password30@capstone.a6u5hbn.mongodb.net/ballet_motion?retryWrites=true&w=majority&appName=Capstone'
    MONGO_DBNAME = 'ballet_motion'
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'uploads')
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY") or "jwt_secret_key"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = 'elcapstone69@gmail.com'
    MAIL_PASSWORD = 'siad fffv ajwx zsly'
    MAIL_DEFAULT_SENDER = 'elcapstone69@gmail.com'
    BASE_URL = 'http://localhost:5000'
    OTP_EXPIRY_MINUTES = 10


class ProductionConfig(Config):
    BASE_URL = 'https://yourproductiondomain.com'

class DevelopmentConfig(Config):
    DEBUG = True
