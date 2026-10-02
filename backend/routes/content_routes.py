"""News, Learning, Quiz, Cyber Law routes."""
from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from models.learning_model import LearningModel
from models.news_model import NewsModel
from models.quiz_model import QuizModel
from routes.auth_routes import admin_required
from utils.database import get_collection, serialize_doc
from utils.response import error_response, success_response

content_bp = Blueprint("content", __name__, url_prefix="/api")


# ---- NEWS ----
@content_bp.route("/news", methods=["GET"])
def get_news():
    """Get cyber news articles."""
    category = request.args.get("category")
    search = request.args.get("search")
    page = int(request.args.get("page", 1))
    result = NewsModel.find_all(category, search, page)
    return success_response(result)


@content_bp.route("/news/<news_id>", methods=["GET"])
def get_news_detail(news_id):
    """Get single news article."""
    article = NewsModel.find_by_id(news_id)
    if not article:
        return error_response("Article not found", 404)
    return success_response(article)


@content_bp.route("/news/<news_id>/bookmark", methods=["POST"])
@jwt_required()
def bookmark_news(news_id):
    """Toggle news bookmark."""
    user_id = get_jwt_identity()
    bookmarked = NewsModel.toggle_bookmark(news_id, user_id)
    return success_response({"bookmarked": bookmarked})


# ---- CYBER LAW ----
@content_bp.route("/cyber-law", methods=["GET"])
def get_cyber_law():
    """Get cyber law and government updates."""
    category = request.args.get("category")
    query = {"type": "cyber_law"}
    if category:
        query["category"] = category
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    skip = (page - 1) * per_page
    col = get_collection("learning")
    total = col.count_documents(query)
    items = [serialize_doc(doc) for doc in col.find(query).sort("created_at", -1).skip(skip).limit(per_page)]
    return success_response({"items": items, "total": total, "page": page})


# ---- LEARNING ----
@content_bp.route("/learning", methods=["GET"])
def get_learning():
    """Get learning modules."""
    category = request.args.get("category")
    page = int(request.args.get("page", 1))
    result = LearningModel.find_all(category, page)
    return success_response(result)


@content_bp.route("/learning/<module_id>", methods=["GET"])
def get_learning_module(module_id):
    """Get single learning module."""
    module = LearningModel.find_by_id(module_id)
    if not module:
        return error_response("Module not found", 404)
    return success_response(module)


@content_bp.route("/learning/<module_id>/progress", methods=["POST"])
@jwt_required()
def update_learning_progress(module_id):
    """Update learning progress."""
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    progress = min(100, max(0, int(data.get("progress", 0))))
    LearningModel.update_progress(user_id, module_id, progress)

    # Update awareness score
    if progress >= 100:
        from models.user_model import UserModel
        user = UserModel.find_by_id(user_id)
        if user:
            new_score = min(100, user.get("awareness_score", 0) + 5)
            UserModel.update(user_id, {"awareness_score": new_score})

    return success_response({"progress": progress})


@content_bp.route("/learning/progress", methods=["GET"])
@jwt_required()
def get_learning_progress():
    """Get user's learning progress."""
    user_id = get_jwt_identity()
    progress = LearningModel.get_user_progress(user_id)
    return success_response(progress)


# ---- QUIZ ----
@content_bp.route("/quiz", methods=["GET"])
def get_quizzes():
    """Get available quizzes."""
    page = int(request.args.get("page", 1))
    result = QuizModel.find_all(page)
    for quiz in result.get("items", []):
        for question in quiz.get("questions", []):
            question.pop("correct", None)
    return success_response(result)


@content_bp.route("/quiz/<quiz_id>", methods=["GET"])
def get_quiz(quiz_id):
    """Get quiz questions (without answers)."""
    quiz = QuizModel.find_by_id(quiz_id)
    if not quiz:
        return error_response("Quiz not found", 404)
    # Remove correct answers from response
    if quiz.get("questions"):
        for q in quiz["questions"]:
            q.pop("correct", None)
    return success_response(quiz)


@content_bp.route("/quiz/<quiz_id>/submit", methods=["POST"])
@jwt_required()
def submit_quiz(quiz_id):
    """Submit quiz answers and get score."""
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    answers = data.get("answers", [])
    time_taken = int(data.get("time_taken", 0))

    quiz = QuizModel.find_by_id(quiz_id)
    if not quiz:
        return error_response("Quiz not found", 404)

    questions = quiz.get("questions", [])
    score = 0
    for i, q in enumerate(questions):
        if i < len(answers) and answers[i] == q.get("correct"):
            score += 1

    result = QuizModel.submit_result(user_id, quiz_id, score, len(questions), answers, time_taken)

    # Update awareness score
    from models.user_model import UserModel
    user = UserModel.find_by_id(user_id)
    if user and result.get("percentage", 0) >= 80:
        new_score = min(100, user.get("awareness_score", 0) + 10)
        UserModel.update(user_id, {"awareness_score": new_score})

    return success_response(result)


@content_bp.route("/quiz/leaderboard", methods=["GET"])
def get_leaderboard():
    """Get quiz leaderboard."""
    quiz_id = request.args.get("quiz_id")
    leaderboard = QuizModel.get_leaderboard(quiz_id)
    return success_response(leaderboard)


@content_bp.route("/quiz/results", methods=["GET"])
@jwt_required()
def get_quiz_results():
    """Get user's quiz results."""
    user_id = get_jwt_identity()
    results = QuizModel.get_user_results(user_id)
    return success_response(results)
