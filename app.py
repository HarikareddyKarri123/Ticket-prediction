import os

import joblib
from flask import Flask, jsonify, request

from database import init_db, create_user, authenticate_user, save_ticket, get_user_tickets, update_ticket_status, get_user_by_id, get_department_tickets
from deadline_parser import extract_deadline
from preprocess import preprocess_text

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "model")

app = Flask(__name__)

priority_model = None
category_model = None
department_model = None
vectorizer = None


def load_models() -> None:
    """Load trained ML models from the model folder."""
    global priority_model, category_model, department_model, vectorizer

    priority_path = os.path.join(MODEL_DIR, "priority_model.pkl")
    category_path = os.path.join(MODEL_DIR, "category_model.pkl")
    department_path = os.path.join(MODEL_DIR, "department_model.pkl")
    vectorizer_path = os.path.join(MODEL_DIR, "vectorizer.pkl")

    missing_files = [
        path
        for path in [priority_path, category_path, department_path, vectorizer_path]
        if not os.path.exists(path)
    ]

    if missing_files:
        raise FileNotFoundError(
            "Model files not found. Run 'python train_model.py' first."
        )

    vectorizer = joblib.load(vectorizer_path)
    priority_model = joblib.load(priority_path)
    category_model = joblib.load(category_path)
    department_model = joblib.load(department_path)


@app.route("/", methods=["GET"])
def home():
    return "Backend Running Successfully"


# ── Auth Routes ───────────────────────────────────────────────────────────────

@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Please provide JSON body."}), 400

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""
    role = (data.get("role") or "Employee").strip()

    if not name:
        return jsonify({"error": "Full name is required."}), 400
    if not email:
        return jsonify({"error": "Email is required."}), 400
    if not password or len(password) < 4:
        return jsonify({"error": "Password must be at least 4 characters."}), 400

    user = create_user(name, email, password, role)
    if user is None:
        return jsonify({"error": "An account with this email already exists."}), 409

    return jsonify({"user": user}), 201


@app.route("/signin", methods=["POST"])
def signin():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Please provide JSON body."}), 400

    email = (data.get("email") or "").strip()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    user = authenticate_user(email, password)
    if user is None:
        return jsonify({"error": "Invalid email or password."}), 401

    return jsonify({"user": user})


# ── Ticket Routes ─────────────────────────────────────────────────────────────

@app.route("/tickets", methods=["POST"])
def create_ticket():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Please provide JSON body."}), 400

    user_id = data.get("user_id")
    title = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()
    priority = data.get("priority", "")
    category = data.get("category", "")
    department = data.get("department", "")
    deadline = data.get("deadline")

    if not user_id or not title or not description:
        return jsonify({"error": "user_id, title, and description are required."}), 400

    ticket = save_ticket(user_id, title, description, priority, category, department, deadline)
    return jsonify({"ticket": ticket}), 201


@app.route("/tickets/<int:user_id>", methods=["GET"])
def list_tickets(user_id):
    user = get_user_by_id(user_id)
    if user and user.get("role") and user.get("role") != "Employee":
        tickets = get_department_tickets(user["role"])
    else:
        tickets = get_user_tickets(user_id)
    return jsonify({"tickets": tickets})


# ── ML Prediction Route (unchanged) ──────────────────────────────────────────

@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json(silent=True)

    if not data or "ticket" not in data:
        return jsonify({"error": "Please provide JSON with a 'ticket' field."}), 400

    ticket_text = data["ticket"].strip()
    if not ticket_text:
        return jsonify({"error": "Ticket text cannot be empty."}), 400

    cleaned_text = preprocess_text(ticket_text)
    X = vectorizer.transform([cleaned_text])

    predicted_priority = priority_model.predict(X)[0]
    predicted_category = category_model.predict(X)[0]
    predicted_department = department_model.predict(X)[0]
    deadline = extract_deadline(ticket_text)

    response = {
        "ticket": ticket_text,
        "priority": predicted_priority,
        "category": predicted_category,
        "department": predicted_department,
        "deadline_detected": deadline,
    }

    return jsonify(response)


@app.route("/tickets/status", methods=["POST"])
def change_ticket_status():
    data = request.get_json(silent=True)
    if not data or "ticket_id" not in data or "status" not in data:
        return jsonify({"error": "ticket_id and status are required."}), 400
    
    ticket_id = data["ticket_id"]
    status = data["status"]
    
    if status not in ["Open", "In Progress", "Resolved", "Closed"]:
        return jsonify({"error": "Invalid status."}), 400
        
    success = update_ticket_status(ticket_id, status)
    if not success:
        return jsonify({"error": "Failed to update status."}), 500
        
    return jsonify({"message": "Status updated successfully."})


if __name__ == "__main__":
    init_db()
    load_models()
    app.run(debug=True, host="0.0.0.0", port=5000)
