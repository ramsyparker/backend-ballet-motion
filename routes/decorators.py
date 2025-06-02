from functools import wraps
from flask import request, jsonify, current_app

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('x-api-key')
        if api_key != current_app.config['STATIC_API_KEY']:
            return jsonify({"message": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated
