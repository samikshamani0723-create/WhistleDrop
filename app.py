from flask import Flask, request, jsonify
import sqlite3
import os
import secrets
from functools import wraps
MODERATOR_API_KEY ="WhistleDrop@2026"

app = Flask(__name__)
DATABASE = "WhistleDrop.db"


def init_db():
    with sqlite3.connect(DATABASE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_code TEXT UNIQUE NOT NULL,
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                evidence_url TEXT,
                status TEXT NOT NULL DEFAULT 'SUBMITTED',
                status_update TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )

        """)


init_db()


@app.route("/")
def home():
    return "WhistleDrop API is running!"


@app.route("/reports", methods=["POST"])
def submit_report():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Valid JSON is required"}), 400

    category = data.get("category")
    description = data.get("description")
    evidence_url = data.get("evidence_url")

    allowed_categories = [
        "Security", "Harassment", "Corruption",
        "Technical", "Other"
    ]

    if category not in allowed_categories:
        return jsonify({"error": "Invalid category"}), 400

    if not isinstance(description, str) or not description.strip():
        return jsonify({"error": "Description is required"}), 400

    if evidence_url is not None and not isinstance(evidence_url, str):
        return jsonify({"error": "Evidence URL must be text"}), 400

    case_code = secrets.token_urlsafe(12)

    with sqlite3.connect(DATABASE) as conn:
        conn.execute("""
            INSERT INTO reports
            (case_code, category, description, evidence_url)
            VALUES (?, ?, ?, ?)
        """, (case_code, category, description.strip(), evidence_url))
    with sqlite3.connect(DATABASE) as conn:
        conn.execute("ALTER TABLE reports ADD COLUMN status_update TEXT")
            
    return jsonify({
        "message": "Report saved successfully",
        "case_code": case_code,
        "status": "SUBMITTED"
    }), 201

@app.route("/reports/<case_code>", methods=["GET"])
def track_report(case_code):
    with sqlite3.connect(DATABASE) as conn:
        report = conn.execute(
            """
            SELECT case_code, category, status, status_update
            FROM reports
            WHERE case_code = ?
            """,
            (case_code,)
        ).fetchone()

    if report is None:
        return jsonify({"error": "Report not found"}), 404

    return jsonify({
        "case_code": report[0],
        "category": report[1],
        "status": report[2],
        "status_update": report[3]
    }), 200


def moderator_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        api_key = request.headers.get("X-Moderator-Key")
        if not api_key or not secrets.compare_digest(
            api_key, MODERATOR_API_KEY
        ):
            return jsonify({"error": "Unauthorized"}), 401

        return func(*args, **kwargs)

    return wrapper

@app.route("/moderator/reports", methods=["GET"])
@moderator_required
def get_reports():
    category = request.args.get("category")
    status = request.args.get("status")

    allowed_categories = [
        "Security",
        "Harassment",
        "Corruption",
        "Technical",
        "Other"
    ]

    allowed_statuses = [
        "SUBMITTED",
        "UNDER_REVIEW",
        "RESOLVED",
        "DISMISSED"
    ]

    if category and category not in allowed_categories:
        return jsonify({"error": "Invalid category filter"}), 400

    if status and status not in allowed_statuses:
        return jsonify({"error": "Invalid status filter"}), 400

    query = """
        SELECT case_code, category, description,
               evidence_url, status, status_update, created_at
        FROM reports
    """

    conditions = []
    parameters = []

    if category:
        conditions.append("category = ?")
        parameters.append(category)

    if status:
        conditions.append("status = ?")
        parameters.append(status)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY created_at DESC"

    with sqlite3.connect(DATABASE) as conn:
        reports = conn.execute(query, parameters).fetchall()

    result = []

    for report in reports:
        result.append({
            "case_code": report[0],
            "category": report[1],
            "description": report[2],
            "evidence_url": report[3],
            "status": report[4],
            "status_update": report[5],
            "created_at": report[6]
        })

    return jsonify({
        "count": len(result),
        "reports": result
    }), 200

@app.route("/reports/<case_code>/status", methods=["PATCH"])
@moderator_required
def update_report_status(case_code):
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Valid JSON is required"}), 400

    new_status = data.get("status")
    status_update = data.get("status_update")

    allowed_statuses = [
        "UNDER_REVIEW",
        "RESOLVED",
        "DISMISSED"
    ]

    if new_status not in allowed_statuses:
        return jsonify({"error": "Invalid status"}), 400

    if status_update is not None and not isinstance(status_update, str):
        return jsonify({"error": "Status update must be text"}), 400

    with sqlite3.connect(DATABASE) as conn:

        report = conn.execute(
            "SELECT status FROM reports WHERE case_code = ?",
            (case_code,)
        ).fetchone()

        if report is None:
            return jsonify({"error": "Report not found"}), 404

        current_status = report[0]

        # Enforce workflow
        if current_status == "SUBMITTED":
            if new_status != "UNDER_REVIEW":
                return jsonify({
                    "error": "SUBMITTED reports can only move to UNDER_REVIEW"
                }), 400

        elif current_status == "UNDER_REVIEW":
            if new_status not in ["RESOLVED", "DISMISSED"]:
                return jsonify({
                    "error": "UNDER_REVIEW reports can only move to RESOLVED or DISMISSED"
                }), 400

        else:
            return jsonify({
                "error": "Report is already closed"
            }), 400

        conn.execute(
            """
            UPDATE reports
            SET status = ?, status_update = ?
            WHERE case_code = ?
            """,
            (new_status, status_update, case_code)
        )

    return jsonify({
        "case_code": case_code,
        "status": new_status,
        "status_update": status_update,
        "message": "Report status updated successfully"
    }), 200

if __name__ == "__main__":
    app.run(debug=True)