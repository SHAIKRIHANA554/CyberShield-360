"""Admin panel API routes."""
from datetime import datetime, timedelta

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from models.learning_model import LearningModel
from models.news_model import NewsModel
from models.notification_model import NotificationModel
from models.quiz_model import QuizModel
from models.threat_model import ThreatReportModel
from models.user_model import UserModel
from routes.auth_routes import admin_required
from utils.database import get_collection, paginate, serialize_doc
from utils.response import error_response, success_response

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@admin_bp.route("/dashboard", methods=["GET"])
@jwt_required()
@admin_required
def admin_dashboard():
    """Admin dashboard analytics."""
    user_collection = get_collection("users")
    user_ids = {str(user["_id"]) for user in user_collection.find({"role": "user"})}
    recent_cutoff = datetime.utcnow() - timedelta(hours=24)
    recent_login_logs = get_collection("activity_logs").find({
        "action": "login",
        "created_at": {"$gte": recent_cutoff}
    })
    recent_login_ids = {
        log.get("user_id") for log in recent_login_logs
        if log.get("user_id") in user_ids
    }
    active_module_count = get_collection("learning").count_documents({
        "type": {"$ne": "cyber_law"}, "is_active": True
    })
    progress_records = list(get_collection("learning_progress").find({}))
    completed_modules = sum(1 for record in progress_records if record.get("progress", 0) >= 100)
    possible_completions = len(user_ids) * active_module_count

    return success_response({
        "users_count": len(user_ids),
        "logged_in_users_24h": len(recent_login_ids),
        "reports_count": ThreatReportModel.count_all(),
        "quiz_attempts_count": get_collection("quiz_results").count_documents({}),
        "learning_progress": {
            "completed_modules": completed_modules,
            "tracked_modules": len(progress_records),
            "completion_percentage": round(completed_modules / possible_completions * 100, 1)
            if possible_completions else 0
        },
        "threat_stats": ThreatReportModel.get_stats(),
        "recent_reports": ThreatReportModel.get_recent(limit=10)
    })


# ---- USER MANAGEMENT ----
@admin_bp.route("/users", methods=["GET"])
@jwt_required()
@admin_required
def get_users():
    """Get all users."""
    page = int(request.args.get("page", 1))
    per_page = min(100, max(1, int(request.args.get("per_page", 50))))
    user_collection = get_collection("users")
    user_query = {"role": "user"}
    users = [
        serialize_doc(user)
        for user in user_collection.find(user_query)
        .sort("created_at", -1)
        .skip((page - 1) * per_page)
        .limit(per_page)
    ]
    progress_by_user = {}
    for progress in get_collection("learning_progress").find({}):
        summary = progress_by_user.setdefault(progress.get("user_id"), {"completed": 0, "progress_total": 0})
        summary["progress_total"] += progress.get("progress", 0)
        if progress.get("progress", 0) >= 100:
            summary["completed"] += 1

    quiz_attempts_by_user = {}
    for attempt in get_collection("quiz_results").find({}):
        user_attempts = quiz_attempts_by_user.setdefault(attempt.get("user_id"), {"count": 0, "score_total": 0})
        user_attempts["count"] += 1
        user_attempts["score_total"] += attempt.get("percentage", 0)

    last_login_by_user = {}
    for activity in get_collection("activity_logs").find({"action": "login"}).sort("created_at", -1):
        last_login_by_user.setdefault(activity.get("user_id"), activity.get("created_at"))

    learning_total = get_collection("learning").count_documents({
        "type": {"$ne": "cyber_law"}, "is_active": True
    })
    for u in users:
        u.pop("password", None)
        progress = progress_by_user.get(str(u["_id"]), {})
        quiz_attempts = quiz_attempts_by_user.get(str(u["_id"]), {})
        u["learning_completed"] = progress.get("completed", 0)
        u["learning_total"] = learning_total
        u["learning_average_progress"] = round(progress.get("progress_total", 0) / learning_total, 1) if learning_total else 0
        u["quiz_attempts"] = quiz_attempts.get("count", 0)
        u["quiz_average_score"] = round(quiz_attempts["score_total"] / quiz_attempts["count"], 1) if quiz_attempts.get("count") else None
        last_login = last_login_by_user.get(str(u["_id"]))
        u["last_login"] = last_login.isoformat() if hasattr(last_login, "isoformat") else last_login
    return success_response({"items": users, "total": user_collection.count_documents(user_query)})


@admin_bp.route("/users/<user_id>", methods=["DELETE"])
@jwt_required()
@admin_required
def delete_user(user_id):
    """Delete user."""
    if UserModel.delete(user_id):
        return success_response(None, "User deleted")
    return error_response("User not found", 404)


# ---- NEWS MANAGEMENT ----
@admin_bp.route("/news", methods=["GET"])
@jwt_required()
@admin_required
def list_admin_news():
    """List news articles for admin management."""
    page = max(1, int(request.args.get("page", 1)))
    per_page = min(100, max(1, int(request.args.get("per_page", 50))))
    return success_response(NewsModel.find_all(page=page, per_page=per_page))


@admin_bp.route("/news", methods=["POST"])
@jwt_required()
@admin_required
def create_news():
    """Create news article."""
    data = request.get_json() or {}
    if not data.get("title"):
        return error_response("Title is required")
    article = NewsModel.create(data)
    return success_response(article, "News created", 201)


@admin_bp.route("/news/<news_id>", methods=["PUT"])
@jwt_required()
@admin_required
def update_news(news_id):
    """Update news article."""
    data = request.get_json() or {}
    if NewsModel.update(news_id, data):
        return success_response(None, "News updated")
    return error_response("News not found", 404)


@admin_bp.route("/news/<news_id>", methods=["DELETE"])
@jwt_required()
@admin_required
def delete_news(news_id):
    """Delete news article."""
    if NewsModel.delete(news_id):
        return success_response(None, "News deleted")
    return error_response("News not found", 404)


# ---- LEARNING MANAGEMENT ----
@admin_bp.route("/learning", methods=["GET"])
@jwt_required()
@admin_required
def list_admin_learning():
    """List learning modules and cyber-law entries for admin management."""
    page = max(1, int(request.args.get("page", 1)))
    per_page = min(100, max(1, int(request.args.get("per_page", 100))))
    content_type = request.args.get("type")
    query = {"type": content_type} if content_type in {"article", "cyber_law"} else {}
    return success_response(paginate(get_collection("learning"), query, page, per_page))


@admin_bp.route("/learning", methods=["POST"])
@jwt_required()
@admin_required
def create_learning():
    """Create learning module."""
    data = request.get_json() or {}
    if not data.get("title"):
        return error_response("Title is required")
    module = LearningModel.create(data)
    return success_response(module, "Module created", 201)


@admin_bp.route("/learning/<module_id>", methods=["PUT"])
@jwt_required()
@admin_required
def update_learning(module_id):
    """Update learning module."""
    data = request.get_json() or {}
    if LearningModel.update(module_id, data):
        return success_response(None, "Module updated")
    return error_response("Module not found", 404)


@admin_bp.route("/learning/<module_id>", methods=["DELETE"])
@jwt_required()
@admin_required
def delete_learning(module_id):
    """Delete learning module."""
    if LearningModel.delete(module_id):
        return success_response(None, "Module deleted")
    return error_response("Module not found", 404)


# ---- QUIZ MANAGEMENT ----
@admin_bp.route("/quiz", methods=["GET"])
@jwt_required()
@admin_required
def list_admin_quizzes():
    """List quizzes, including answer keys, for admin management only."""
    page = max(1, int(request.args.get("page", 1)))
    per_page = min(100, max(1, int(request.args.get("per_page", 50))))
    return success_response(paginate(get_collection("quiz"), {}, page, per_page))


@admin_bp.route("/quiz", methods=["POST"])
@jwt_required()
@admin_required
def create_quiz():
    """Create quiz."""
    data = request.get_json() or {}
    if not data.get("title") or not data.get("questions"):
        return error_response("Title and questions are required")
    quiz = QuizModel.create(data)
    return success_response(quiz, "Quiz created", 201)


@admin_bp.route("/quiz/<quiz_id>", methods=["PUT"])
@jwt_required()
@admin_required
def update_quiz(quiz_id):
    """Update quiz."""
    data = request.get_json() or {}
    if QuizModel.update(quiz_id, data):
        return success_response(None, "Quiz updated")
    return error_response("Quiz not found", 404)


@admin_bp.route("/quiz/<quiz_id>", methods=["DELETE"])
@jwt_required()
@admin_required
def delete_quiz(quiz_id):
    """Delete quiz."""
    if QuizModel.delete(quiz_id):
        return success_response(None, "Quiz deleted")
    return error_response("Quiz not found", 404)


# ---- NOTIFICATION MANAGEMENT ----
@admin_bp.route("/notifications", methods=["POST"])
@jwt_required()
@admin_required
def create_notification():
    """Create notification/alert."""
    data = request.get_json() or {}
    if not data.get("title"):
        return error_response("Title is required")
    data.setdefault("is_global", True)
    notification = NotificationModel.create(data)
    return success_response(notification, "Notification created", 201)


@admin_bp.route("/notifications/<notification_id>", methods=["DELETE"])
@jwt_required()
@admin_required
def delete_notification(notification_id):
    """Delete notification."""
    if NotificationModel.delete(notification_id):
        return success_response(None, "Notification deleted")
    return error_response("Notification not found", 404)


# ---- ML DATASET & TRAINING MANAGEMENT ----
@admin_bp.route("/dataset/stats", methods=["GET"])
@jwt_required()
@admin_required
def get_dataset_stats():
    """Get ML dataset statistics and model status."""
    import os
    import pandas as pd
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    datasets_dir = os.path.join(base_dir, "ml_models", "datasets")
    models_dir = os.path.join(base_dir, "ml_models")

    url_csv = os.path.join(datasets_dir, "url_threats_dataset.csv")
    text_csv = os.path.join(datasets_dir, "text_threats_dataset.csv")

    url_count = len(pd.read_csv(url_csv)) if os.path.exists(url_csv) else 0
    text_count = len(pd.read_csv(text_csv)) if os.path.exists(text_csv) else 0

    return success_response({
        "url_dataset_count": url_count,
        "text_dataset_count": text_count,
        "url_model_trained": os.path.exists(os.path.join(models_dir, "url_rf_model.pkl")),
        "text_model_trained": os.path.exists(os.path.join(models_dir, "text_threat_model.pkl"))
    })


@admin_bp.route("/dataset/retrain", methods=["POST"])
@jwt_required()
@admin_required
def retrain_ml_models():
    """Retrain ML models using datasets."""
    try:
        from services.ml_models.trainer import ThreatMLTrainer
        trainer = ThreatMLTrainer()
        url_res = trainer.train_url_model()
        text_res = trainer.train_text_model()
        return success_response({"url": url_res, "text": text_res}, "ML Models trained successfully")
    except Exception as e:
        return error_response(f"Training failed: {e}", 500)
