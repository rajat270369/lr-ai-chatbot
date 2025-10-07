# app.py
import os
import sqlite3
import logging
import requests
from flask import Flask, render_template, request, jsonify, redirect, url_for, abort
from flask_cors import CORS
from werkzeug.exceptions import BadRequest

# -----------------------
# Basic configuration
# -----------------------
app = Flask(__name__)
# Allow both /chat and /chat/ (avoid trailing-slash 404s)
app.url_map.strict_slashes = False

# Dev-friendly CORS (restrict in production)
CORS(app)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory per-user conversation memory (simple)
session_memory = {}                                                     
MAX_MEMORY = int(os.environ.get("MAX_SESSION_MEMORY", 40))

# Groq/OpenAI-compatible API config (use env vars)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_API_URL = os.environ.get("GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "groq/llama-3.1-8b-instant")
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", 500))
TEMPERATURE = float(os.environ.get("TEMPERATURE", 0.0))

DB_PATH = os.environ.get("DB_PATH", "db.sqlite3")


# -----------------------
# Helper functions
# -----------------------
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    return conn


def initialize_tables():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS hotel_bookings (
        id TEXT PRIMARY KEY, guest_name TEXT, room_type TEXT, check_in TEXT, check_out TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS ecommerce_orders (
        id TEXT PRIMARY KEY, product TEXT, status TEXT, eta TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS college_admissions (
        id TEXT PRIMARY KEY, name TEXT, course TEXT, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS dental_appointments (
        id TEXT PRIMARY KEY, patient_name TEXT, doctor TEXT, time TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS gym_memberships (
        id TEXT PRIMARY KEY, member_name TEXT, plan TEXT, expires TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS real_estate_properties (
        id TEXT PRIMARY KEY, location TEXT, type TEXT, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS salon_appointments (
        id TEXT PRIMARY KEY, client_name TEXT, service TEXT, time TEXT)''')
    conn.commit()
    conn.close()


def append_memory(user_id: str, role: str, content: str):
    """Append a message to session_memory, keep it capped to MAX_MEMORY messages (excluding system)."""
    if user_id not in session_memory:
        session_memory[user_id] = []
    session_memory[user_id].append({"role": role, "content": content})
    # enforce cap while keeping system message (role == 'system') at index 0 if present
    msgs = session_memory[user_id]
    system = msgs[0] if len(msgs) and msgs[0].get("role") == "system" else None
    non_system = [m for m in msgs if m.get("role") != "system"]
    if len(non_system) > MAX_MEMORY:
        non_system = non_system[-MAX_MEMORY:]
    session_memory[user_id] = ([system] if system else []) + non_system


def extract_text_from_response_json(data, raw_text_fallback=""):
    """
    Try several common response shapes:
      - data['choices'][0]['message']['content']
      - data['choices'][0]['text']
      - data.get('text') or fallback to raw_text_fallback
    """
    if not isinstance(data, dict):
        return raw_text_fallback
    choices = data.get("choices")
    if isinstance(choices, list) and len(choices) > 0:
        first = choices[0]
        # typical OpenAI-compatible chat shape:
        msg = first.get("message") or {}
        if isinstance(msg, dict) and msg.get("content"):
            return msg.get("content")
        # older shapes or text completions:
        if first.get("text"):
            return first.get("text")
        # sometimes providers use 'output' or 'content'
        if first.get("output"):
            return first.get("output")
        if first.get("content"):
            return first.get("content")
    # fallback top-level fields
    for key in ("text", "response", "output", "content"):
        if data.get(key):
            return data.get(key)
    # last resort
    return raw_text_fallback


# -----------------------
# Initialize DB on import
# -----------------------
initialize_tables()


# -----------------------
# Routes
# -----------------------
@app.route("/")
def home():
    # If you have an index.html template in templates/, render it; else return a small message.
    try:
        return render_template("index.html")
    except Exception:
        return (
            "<h1>LR.AI Backend</h1>"
            "<p>Use POST /chat with JSON: {\"message\":\"...\"}</p>"
            "<p>Use GET /routes to list registered routes.</p>"
        ), 200


@app.route("/routes", methods=["GET"])
def list_routes():
    # Useful for debugging 404s: shows registered routes
    rules = []
    for rule in app.url_map.iter_rules():
        rules.append({
            "rule": str(rule),
            "methods": sorted(rule.methods),
            "endpoint": rule.endpoint
        })
    return jsonify({"routes": rules})


@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        password = request.form.get("password")
        if password == "12Ra442Ra1":
            return redirect("/dashboard")
        return "Access denied", 403
    try:
        return render_template("admin_login.html")
    except Exception:
        return "<form method='post'><input name='password' /><button>Login</button></form>"


@app.route("/dashboard")
def dashboard():
    conn = get_db_connection()
    c = conn.cursor()
    tables = {
        "hotel": "hotel_bookings",
        "ecommerce": "ecommerce_orders",
        "college": "college_admissions",
        "clinic": "dental_appointments",
        "fitness": "gym_memberships",
        "real_estate": "real_estate_properties",
        "salon": "salon_appointments",
    }
    data = {}
    try:
        for name, table in tables.items():
            try:
                rows = c.execute(f"SELECT * FROM {table}").fetchall()
            except Exception as e:
                logger.exception("Error reading table %s: %s", table, e)
                rows = []
            data[name] = rows
    finally:
        conn.close()
    try:
        return render_template("admin_dashboard.html", **data)
    except Exception:
        # If templates missing, return a JSON preview
        return jsonify(data)


@app.route("/add/<category>", methods=["POST"])
def add_entry(category):
    """
    Accepts form-encoded or JSON payloads.
    Fields depend on category. Returns redirect to /dashboard on success.
    """
    form = request.form.to_dict() or request.get_json(silent=True) or {}
    conn = get_db_connection()
    c = conn.cursor()
    try:
        if category == "hotel":
            c.execute(
                "INSERT OR REPLACE INTO hotel_bookings VALUES (?, ?, ?, ?, ?)",
                (form["id"], form["guest_name"], form["room_type"], form["check_in"], form["check_out"]),
            )
        elif category == "ecommerce":
            c.execute(
                "INSERT OR REPLACE INTO ecommerce_orders VALUES (?, ?, ?, ?)",
                (form["id"], form["product"], form["status"], form["eta"]),
            )
        elif category == "college":
            c.execute(
                "INSERT OR REPLACE INTO college_admissions VALUES (?, ?, ?, ?)",
                (form["id"], form["name"], form["course"], form["status"]),
            )
        elif category == "clinic":
            c.execute(
                "INSERT OR REPLACE INTO dental_appointments VALUES (?, ?, ?, ?)",
                (form["id"], form["patient_name"], form["doctor"], form["time"]),
            )
        elif category == "fitness":
            c.execute(
                "INSERT OR REPLACE INTO gym_memberships VALUES (?, ?, ?, ?)",
                (form["id"], form["member_name"], form["plan"], form["expires"]),
            )
        elif category == "real_estate":
            c.execute(
                "INSERT OR REPLACE INTO real_estate_properties VALUES (?, ?, ?, ?)",
                (form["id"], form["location"], form["type"], form["status"]),
            )
        elif category == "salon":
            c.execute(
                "INSERT OR REPLACE INTO salon_appointments VALUES (?, ?, ?, ?)",
                (form["id"], form["client_name"], form["service"], form["time"]),
            )
        else:
            conn.close()
            return f"Unknown category: {category}", 400
        conn.commit()
    except KeyError as e:
        conn.close()
        return f"Missing field: {e}", 400
    except Exception as e:
        conn.close()
        logger.exception("DB insert error: %s", e)
        return f"DB error: {str(e)}", 500
    conn.close()
    return redirect(url_for("dashboard"))


@app.route("/delete/<category>/<entry_id>", methods=["GET", "POST"])
def delete_entry(category, entry_id):
    table_map = {
        "hotel": "hotel_bookings",
        "ecommerce": "ecommerce_orders",
        "college": "college_admissions",
        "clinic": "dental_appointments",
        "fitness": "gym_memberships",
        "real_estate": "real_estate_properties",
        "salon": "salon_appointments",
    }
    table = table_map.get(category)
    if not table:
        return "Unknown category", 400
    conn = get_db_connection()
    c = conn.cursor()
    try:
        c.execute(f"DELETE FROM {table} WHERE id=?", (entry_id,))
        conn.commit()
    except Exception as e:
        logger.exception("Delete error: %s", e)
        conn.close()
        return f"DB delete error: {e}", 500
    conn.close()
    return redirect(url_for("dashboard"))


# -----------------------
# Chat endpoint (main)
# -----------------------
@app.route("/chat", methods=["POST", "GET", "OPTIONS"])
def chat():
    """
    POST JSON:
      {
        "message": "Hello",
        "language": "en",
        "template": "general",
        "user_id": "user123"  # optional
      }
    GET will return a short usage message (handy when debugging 404s).
    """
    logger.info("Incoming %s %s", request.method, request.path)

    if request.method == "GET":
        return jsonify({
            "ok": True,
            "message": "POST JSON {\"message\":\"...\"} to this endpoint. Use application/json content-type.",
            "routes_example": [str(r) for r in app.url_map.iter_rules()]
        })

    # validate JSON
    if not request.is_json:
        # Some clients set Content-Type incorrectly; attempt to parse JSON anyway
        try:
            payload = request.get_json(force=True, silent=False)
        except BadRequest:
            return jsonify({"error": "Invalid or missing JSON. Set Content-Type: application/json"}), 400
    else:
        payload = request.get_json(silent=True) or {}

    user_input = (payload.get("message") or "").strip()
    if not user_input:
        return jsonify({"error": "Please provide a non-empty 'message' field in the JSON body."}), 400

    language = payload.get("language", "en")
    template = payload.get("template", "general")
    user_id = payload.get("user_id", "default_user")

    # ensure API key present
    if not GROQ_API_KEY:
        logger.error("GROQ_API_KEY not set in environment")
        return jsonify({"error": "Server configuration error: GROQ_API_KEY is not set."}), 500

    # initialize system message if needed
    if user_id not in session_memory:
        system_prompt = (
            f"You are LR.AI, a helpful, polite, and structured AI assistant for {template.replace('_',' ')}. "
            "Keep replies clear, friendly, and remember previous conversation context. "
            f"All replies must be in this language: {language}."
        )
        session_memory[user_id] = [{"role": "system", "content": system_prompt}]

    append_memory(user_id, "user", user_input)

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    api_payload = {
        "model": GROQ_MODEL,
        "messages": session_memory[user_id],
        "max_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
    }

    logger.info("Calling Groq/OpenAI-compatible endpoint %s model=%s user=%s", GROQ_API_URL, GROQ_MODEL, user_id)

    try:
        resp = requests.post(GROQ_API_URL, headers=headers, json=api_payload, timeout=20)
    except requests.exceptions.RequestException as e:
        logger.exception("Network error when calling model API: %s", e)
        return jsonify({"error": "Network error when calling model API", "details": str(e)}), 502

    # expose provider error details to help debug 400s/404s from the provider side
    body_text = resp.text
    status = resp.status_code
    if status != 200:
        logger.warning("Model API returned non-200 status %s body: %s", status, body_text[:2000])
        # attempt JSON parse for helpful error info
        try:
            err_json = resp.json()
        except Exception:
            err_json = {"raw": body_text}
        return jsonify({"error": f"Model API error {status}", "details": err_json}), status

    # parse the success response
    try:
        data = resp.json()
    except Exception:
        # no-json body
        logger.exception("Model API returned non-JSON body")
        return jsonify({"error": "Model API returned non-JSON response", "raw": body_text}), 502

    # extract assistant reply from various possible shapes
    reply = extract_text_from_response_json(data, raw_text_fallback=body_text[:4000])
    append_memory(user_id, "assistant", reply)

    return jsonify({"reply": reply, "debug": {"model_response_snippet": (body_text[:1000])}})


# -----------------------
# Run
# -----------------------
if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 10000))
    debug = os.environ.get("FLASK_DEBUG", "True").lower() in ("1", "true", "yes")
    logger.info("Starting LR.AI backend on %s:%s debug=%s", host, port, debug)
    app.run(host=host, port=port, debug=debug)




