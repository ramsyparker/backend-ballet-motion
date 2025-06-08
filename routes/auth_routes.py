import os
import requests
from extensions import mongo
from flask import Blueprint, jsonify, request, current_app, url_for
from bson.objectid import ObjectId
from flask_jwt_extended import create_access_token,jwt_required, get_jwt, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_mail import Mail,Message
from datetime import datetime
import random
import logging
from datetime import datetime, timedelta
from routes.decorators import require_api_key
import firebase_admin
from firebase_admin import credentials, auth

# Inisialisasi Firebase Admin hanya sekali di awal aplikasi
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase_service_account.json")  # path ke file JSON Anda
    firebase_admin.initialize_app(cred)


auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

UPLOAD_FOLDER = "static/profile_pictures"
DEFAULT_PROFILE_PICTURE = "profile_pictures/default.jpeg"

# Pastikan folder penyimpanan ada
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

revoked_tokens = set()
mail = Mail()

@auth_bp.route('/register', methods=['POST'])
@require_api_key
def register():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Invalid JSON"}), 400

        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        if not username or not email or not password:
            return jsonify({"status": "error", "message": "All fields are required"}), 422

        if mongo.db.users.find_one({"username": username}):
            return jsonify({"status": "error", "message": "Username already taken"}), 422

        if mongo.db.users.find_one({"email": email}):
            return jsonify({"status": "error", "message": "Email already taken"}), 422

        otp = str(random.randint(100000, 999999))

        new_user = {
            "username": username,
            "email": email,
            "password": generate_password_hash(password),
            "is_verified": False,
            "register_otp": otp,
            "register_otp_created_at": datetime.utcnow(),
            "reset_otp": '',
            "reset_otp_created_at": None,
            "profile_picture": DEFAULT_PROFILE_PICTURE
        }

        inserted = mongo.db.users.insert_one(new_user)

        msg = Message("Your OTP Code",
                      sender=current_app.config['MAIL_USERNAME'],
                      recipients=[email])
        msg.body = f"Your OTP code is: {otp}"

        try:
            mail.send(msg)
        except Exception as e:
            mongo.db.users.delete_one({"_id": inserted.inserted_id})
            return jsonify({
                "status": "error",
                "message": "Failed to send OTP email",
                "error": str(e)
            }), 500

        return jsonify({
            "status": "success",
            "message": "Registration successful. Please check your email for the OTP."
        }), 201

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "An unexpected error occurred",
            "error": str(e)
        }), 500
def get_profile_picture(user):
    # user sekarang adalah dict dari PyMongo, bukan objek SQLAlchemy
    profile_picture = user.get("profile_picture", DEFAULT_PROFILE_PICTURE)

    if profile_picture != DEFAULT_PROFILE_PICTURE:
        return url_for('static', filename=f'profile_pictures/{profile_picture}', _external=True)
    
    return url_for('static', filename=DEFAULT_PROFILE_PICTURE, _external=True)

@auth_bp.route("/update-profile-picture", methods=["POST"])
def update_profile_picture():
    user_id = request.form.get("id")
    file = request.files.get("profile_picture")

    if not file or file.filename == "":
        return jsonify({"status": "error", "message": "No selected file"}), 400

    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404

    # Hapus gambar lama jika bukan default
    if user.get('profile_picture') and user['profile_picture'] != DEFAULT_PROFILE_PICTURE:
        old_path = os.path.join(UPLOAD_FOLDER, user['profile_picture'])
        if os.path.exists(old_path):
            os.remove(old_path)

    filename = secure_filename(f"user_{user_id}_{file.filename}")
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    mongo.db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"profile_picture": filename}}
    )

    return jsonify({
        "status": "success",
        "message": "Profile picture updated",
        "profile_picture": filename
    }), 200

@auth_bp.route('/delete-profile-picture', methods=['POST'])
def delete_profile_picture():
    user_id = request.json.get('id')

    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404

    if user.get('profile_picture') and user['profile_picture'] != DEFAULT_PROFILE_PICTURE:
        old_path = os.path.join(UPLOAD_FOLDER, user['profile_picture'])
        if os.path.exists(old_path):
            os.remove(old_path)

    mongo.db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"profile_picture": DEFAULT_PROFILE_PICTURE}}
    )

    return jsonify({
        "status": "success",
        "message": "Profile picture deleted"
    }), 200
@auth_bp.route('/verify_register_otp', methods=['POST'])
@require_api_key
def verify_register_otp():
    data = request.get_json()
    email = data.get('email')
    otp = data.get('otp')

    if not email or not otp:
        return jsonify({"status": "error", "message": "Email and OTP are required"}), 422

    user = mongo.db.users.find_one({"email": email})
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404

    if user.get("is_verified"):
        return jsonify({
            "status": "success",
            "message": "User already verified",
            "user": {
                "id": str(user["_id"]),
                "username": user["username"],
                "email": user["email"]
            }
        }), 200

    if user.get("register_otp") != otp:
        return jsonify({"status": "error", "message": "Invalid OTP"}), 401

    otp_expiry = user.get("register_otp_created_at") + timedelta(minutes=current_app.config["OTP_EXPIRY_MINUTES"])
    if datetime.utcnow() > otp_expiry:
        return jsonify({"status": "error", "message": "OTP has expired. Please request a new one."}), 401

    mongo.db.users.update_one({"_id": user["_id"]}, {
        "$set": {"is_verified": True},
        "$unset": {"register_otp": "", "register_otp_created_at": ""}
    })

    token = create_access_token(identity=str(user["_id"]))
    return jsonify({
        "status": "success",
        "message": "OTP verified successfully",
        "token": token,
        "user": {
            "id": str(user["_id"]),
            "username": user["username"],
            "email": user["email"],
            "profile_picture": user.get("profile_picture", DEFAULT_PROFILE_PICTURE)
        }
    }), 200

@auth_bp.route('/login', methods=['POST'])
@require_api_key
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"status": "error", "message": "Email and password are required"}), 422

    user = mongo.db.users.find_one({"email": email})
    if not user or not check_password_hash(user['password'], password):
        return jsonify({"status": "error", "message": "Invalid credentials"}), 401

    if not user.get("is_verified"):
        return jsonify({"status": "error", "message": "Please verify your email before logging in"}), 403

    token = create_access_token(identity=str(user["_id"]))
    return jsonify({
        "status": "success",
        "message": "Login successful",
        "token": token,
        "user": {
            "id": str(user["_id"]),
            "username": user["username"],
            "email": user["email"],
            "profile_picture": get_profile_picture(user)
        }
    }), 200

@auth_bp.route('/google-login', methods=['POST'])
def google_login():
    data = request.get_json()
    id_token = data.get("idToken")

    if not id_token:
        return jsonify({"status": "error", "message": "Missing Google token"}), 400

    try:
        # Verifikasi token ke Firebase
        decoded_token = auth.verify_id_token(id_token)
        email = decoded_token.get("email")
        username = decoded_token.get("name") or decoded_token.get("email").split("@")[0]
        picture = decoded_token.get("picture")

        if not email:
            return jsonify({"status": "error", "message": "Google token missing email"}), 400

        # Cek user sudah ada di DB atau belum
        user = mongo.db.users.find_one({"email": email})

        if not user:
            # Buat user baru jika belum ada
            user_data = {
                "email": email,
                "username": username,
                "password": generate_password_hash(ObjectId().__str__()),  # password acak
                "profile_picture": picture,
                "is_verified": True,
                "from_google": True
            }
            user_id = mongo.db.users.insert_one(user_data).inserted_id
            user = user_data
            user["_id"] = user_id

        # Buat JWT token
        token = create_access_token(identity=str(user["_id"]))

        return jsonify({
            "status": "success",
            "message": "Login with Google successful",
            "token": token,
            "user": {
                "id": str(user["_id"]),
                "username": user["username"],
                "email": user["email"],
                "profile_picture": get_profile_picture(user)
            }
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": f"Invalid Firebase token: {str(e)}"}), 400@auth_bp.route('/forgot-password', methods=['POST'])


@auth_bp.route('/forgot-password', methods=['POST'])
@require_api_key
def forgot_password():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Invalid JSON"}), 400

        email = data.get('email')
        if not email:
            return jsonify({"status": "error", "message": "Email is required"}), 422

        user = mongo.db.users.find_one({"email": email})
        if not user:
            return jsonify({"status": "error", "message": "Email not found"}), 404

        reset_otp = str(random.randint(100000, 999999))
        reset_otp_created_at = datetime.utcnow()

        mongo.db.users.update_one(
            {"email": email},
            {
                "$set": {
                    "reset_otp": reset_otp,
                    "reset_otp_created_at": reset_otp_created_at
                }
            }
        )

        msg = Message("Password Reset OTP",
                      sender=current_app.config['MAIL_USERNAME'],
                      recipients=[email])
        msg.body = f"Your password reset OTP code is: {reset_otp}"

        try:
            mail.send(msg)
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": "Failed to send OTP email",
                "error": str(e)
            }), 500

        return jsonify({
            "status": "success",
            "message": "Password reset OTP has been sent to your email."
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "An unexpected error occurred",
            "error": str(e)
        }), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    revoked_tokens.add(jti)
    return jsonify({"status": "success", "message": "Logged out successfully"}), 200

@auth_bp.route('/update-profile', methods=['PUT'])
@jwt_required()
def update_profile():
   
    user_id = get_jwt_identity()
    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})

    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404

    data = request.get_json()
    new_username = data.get('username')
    new_email = data.get('email')

    if not new_username and not new_email:
        return jsonify({
            "status": "error",
            "message": "At least one field (username or email) must be provided"
        }), 400

    if new_username:
        existing = mongo.db.users.find_one({"username": new_username, "_id": {"$ne": user["_id"]}})
        if existing:
            return jsonify({"status": "error", "message": "Username is already taken"}), 422

    if new_email:
        existing = mongo.db.users.find_one({"email": new_email, "_id": {"$ne": user["_id"]}})
        if existing:
            return jsonify({"status": "error", "message": "Email is already taken"}), 422

    update_fields = {}
    if new_username:
        update_fields["username"] = new_username
    if new_email:
        update_fields["email"] = new_email

    mongo.db.users.update_one({"_id": user["_id"]}, {"$set": update_fields})

    return jsonify({
        "status": "success",
        "message": "Profile updated successfully",
        "data": {
            "id": str(user["_id"]),
            "username": new_username or user["username"],
            "email": new_email or user["email"]
        }
    }), 200
@auth_bp.route('/verify-reset-otp', methods=['POST'])
@require_api_key
def verify_reset_otp():
   
    data = request.get_json()
    email = data.get('email')
    otp = data.get('otp')

    if not email or not otp:
        return jsonify({"status": "error", "message": "Email and OTP are required"}), 400

    user = mongo.db.users.find_one({"email": email})
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404

    expiry = user.get('reset_otp_created_at')
    if not expiry or user.get('reset_otp') != otp or datetime.utcnow() > expiry + timedelta(minutes=current_app.config['OTP_EXPIRY_MINUTES']):
        return jsonify({"status": "error", "message": "Invalid or expired OTP"}), 400

    return jsonify({"status": "success", "message": "OTP verified"}), 200
@auth_bp.route('/resend-reset-otp', methods=['POST'])
@require_api_key
def resend_reset_otp():
   
    try:
        data = request.get_json()
        email = data.get('email')
        if not email:
            return jsonify({"status": "error", "message": "Email is required"}), 422

        user = mongo.db.users.find_one({"email": email})
        if not user:
            return jsonify({"status": "error", "message": "User not found"}), 404

        otp = str(random.randint(100000, 999999))
        mongo.db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {
                "reset_otp": otp,
                "reset_otp_created_at": datetime.utcnow()
            }}
        )

        msg = Message("Reset OTP Code",
                      sender=current_app.config['MAIL_USERNAME'],
                      recipients=[email])
        msg.body = f"Your password reset OTP code is: {otp}"
        mail.send(msg)

        return jsonify({"status": "success", "message": "OTP sent successfully"}), 200

    except Exception as e:
        logging.error(f"Failed to resend reset OTP: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
@auth_bp.route('/reset-password', methods=['POST'])
@require_api_key
def reset_password():
   
    data = request.get_json()
    email = data.get('email')
    new_password = data.get('new_password')

    if not email or not new_password:
        return jsonify({"status": "error", "message": "Email and new password are required"}), 400

    user = mongo.db.users.find_one({"email": email})
    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404

    mongo.db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"password": generate_password_hash(new_password)},
         "$unset": {"reset_otp": "", "reset_otp_created_at": ""}}
    )

    return jsonify({"status": "success", "message": "Password updated successfully"}), 200
@auth_bp.route('/reset-password-loggedin', methods=['PUT'])
@jwt_required()
def reset_password_loggedin():
    user_id = get_jwt_identity()
    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})

    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404

    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')

    if not current_password or not new_password:
        return jsonify({"status": "error", "message": "Both fields required"}), 400

    if not check_password_hash(user["password"], current_password):
        return jsonify({"status": "error", "message": "Current password is incorrect"}), 401

    mongo.db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"password": generate_password_hash(new_password)}}
    )

    return jsonify({"status": "success", "message": "Password updated successfully"}), 200

@auth_bp.route('/delete-user', methods=['DELETE'])
@jwt_required()
def delete_user():
   
    user_id = get_jwt_identity()

    result = mongo.db.users.delete_one({"_id": ObjectId(user_id)})

    if result.deleted_count == 0:
        return jsonify({"status": "error", "message": "User not found"}), 404

    return jsonify({"status": "success", "message": "User deleted successfully"}), 200

@auth_bp.route('/users', methods=['GET'])
def get_all_users():
    try:
        users = mongo.db.users.find()
        user_list = [{
            "id": str(user["_id"]),
            "username": user.get("username"),
            "email": user.get("email")
        } for user in users]

        return jsonify({"status": "success", "data": user_list}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


