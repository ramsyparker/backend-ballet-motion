from extensions import mongo
from flask import Flask, jsonify
from flask import request
from flask_cors import CORS
from config import Config, DevelopmentConfig
from flask_mail import Mail
from flask_jwt_extended import JWTManager
from flask_pymongo import PyMongo
import logging
from functools import wraps
from routes.decorators import require_api_key




# Blueprint
from routes.auth_routes import auth_bp
from routes.article_routes import article_bp
from routes.progress_routes import progress_bp
from routes.analysis_routes import analysis_bp

# Setup Logging
logging.basicConfig(level=logging.DEBUG)

# Inisialisasi App
app = Flask(__name__)
app.config.from_object(DevelopmentConfig)
app.config['STATIC_API_KEY'] = '1234567890abcdef'
CORS(app)


# Inisialisasi PyMongo
mongo.init_app(app)

# Inisialisasi JWT & Mail
jwt = JWTManager(app)
mail = Mail(app)
revoked_tokens = set()

@jwt.token_in_blocklist_loader
def check_if_token_is_revoked(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    print(f"Revoked token: {jti}")
    return jti in revoked_tokens


# Registrasi Blueprints

app.register_blueprint(analysis_bp)  # ← daftarkan
app.register_blueprint(article_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(progress_bp, url_prefix='/api')

# Root Endpoint
@app.route('/', methods=['GET'])
def root():
    return jsonify({"message": "Welcome to the API"}), 200

@app.route('/secure-data', methods=['GET'])
@require_api_key
def secure_data():
    return jsonify({"message": "API Key is valid, access granted!"})

# Run App
if __name__ == '__main__':
    app.run(debug=True)
