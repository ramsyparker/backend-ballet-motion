from flask import Blueprint, jsonify
from controllers.article_controller import get_all_articles

article_bp = Blueprint('articles', __name__)

@article_bp.route('/articles', methods=['GET'])
def get_articles_route():
    data = get_all_articles()
    return jsonify({'status': True, 'articles': data})
