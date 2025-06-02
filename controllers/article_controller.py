from flask import current_app
from extensions import mongo

def get_all_articles():
    articles_cursor = mongo.db.articles.find()
    result = []

    for a in articles_cursor:
        result.append({
            'id': str(a['_id']),
            'title': a['title'],
            'content': a['content'],
            'imageUrl': f"/static/articles/{a.get('image_filename', '')}"
        })

    return result
