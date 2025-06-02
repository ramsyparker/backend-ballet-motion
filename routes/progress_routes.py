from flask import Blueprint, jsonify, request, current_app
from extensions import mongo
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson.objectid import ObjectId
from routes.decorators import require_api_key
progress_bp = Blueprint('progress', __name__)

@progress_bp.route('/chapters', methods=['GET'])
@require_api_key
def get_chapters():
    
    chapters = list(mongo.db.chapters.find())
    result = []

    for chapter in chapters:
        lessons = list(mongo.db.lessons.find({"chapter_id": str(chapter['_id'])}))
        lesson_list = [{
            "id": str(lesson['_id']),
            "title": lesson['title'],
            "description": lesson['description'],
            "video_url": lesson['video_url'],
            "imageUrl": f"/static/lesson/{lesson.get('image_filename', '')}"
        } for lesson in lessons]

        result.append({
            "id": str(chapter['_id']),
            "title": chapter['title'],
            "description": chapter['description'],
            "lessons": lesson_list,
            "imageUrl": f"/static/chapters/{chapter.get('image_filename', '')}"
        })

    return jsonify(result)


@progress_bp.route('/progress', methods=['GET'])
@jwt_required()
@require_api_key

def get_user_progress():
    
    user_id = get_jwt_identity()

    total_lessons = mongo.db.lessons.count_documents({})
    completed = mongo.db.user_progress.count_documents({
        "user_id": user_id,
        "is_completed": True
    })

    global_progress = (completed / total_lessons * 100) if total_lessons else 0

    chapters = list(mongo.db.chapters.find())
    chapter_progress_data = []

    completed_lesson_ids = [
        str(p['lesson_id']) for p in mongo.db.user_progress.find(
            {"user_id": user_id, "is_completed": True}
        )
    ]

    for chapter in chapters:
        lessons = list(mongo.db.lessons.find({"chapter_id": chapter['_id']}))
        lesson_ids = [lesson['_id'] for lesson in lessons]
        total = len(lesson_ids)

        completed_lessons = mongo.db.user_progress.count_documents({
            "user_id": user_id,
            "lesson_id": {"$in": lesson_ids},
            "is_completed": True
        })

        percent = (completed_lessons / total * 100) if total else 0

        chapter_progress_data.append({
            "chapter_id": str(chapter['_id']),
            "chapter_title": chapter['title'],
            "completed_lessons": completed_lessons,
            "total_lessons": total,
            "progress_percent": percent
        })

    return jsonify({
        "total_lessons": total_lessons,
        "completed_lessons": completed,
        "progress_percent": global_progress,
        "chapters": chapter_progress_data,
        "completed_lesson_ids": completed_lesson_ids
    })


@progress_bp.route('/progress', methods=['POST'])
@jwt_required()
@require_api_key
def update_progress():
    
    user_id = get_jwt_identity()
    data = request.json
    lesson_id = data.get('lesson_id')

    existing = mongo.db.user_progress.find_one({
        "user_id": user_id,
        "lesson_id": ObjectId(lesson_id)
    })

    if existing:
        mongo.db.user_progress.update_one(
            {"_id": existing['_id']},
            {"$set": {"is_completed": True}}
        )
    else:
        mongo.db.user_progress.insert_one({
            "user_id": user_id,
            "lesson_id": ObjectId(lesson_id),
            "is_completed": True
        })

    return jsonify({"message": "Progress diperbarui."})
