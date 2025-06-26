import os
import sqlite3
import requests
from flask import Flask, render_template, request, jsonify, redirect, url_for

app = Flask(__name__)
session_memory = {}  # 🧠 short-term chat memory

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == "admin123":
            return redirect('/dashboard')
        return "Access denied"
    return render_template('admin_login.html')

@app.route('/dashboard')
def dashboard():
    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()
    tables = {
        'hotel': 'hotel_bookings',
        'ecommerce': 'ecommerce_orders',
        'college': 'college_admissions',
        'clinic': 'dental_appointments',
        'fitness': 'gym_memberships',
        'real_estate': 'real_estate_properties',
        'salon': 'salon_appointments'
    }
    data = {name: c.execute(f"SELECT * FROM {table}").fetchall() for name, table in tables.items()}
    conn.close()
    return render_template('admin_dashboard.html', **data)

@app.route('/add/<category>', methods=['POST'])
def add_entry(category):
    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()
    form = request.form
    try:
        if category == 'hotel':
            c.execute("INSERT OR REPLACE INTO hotel_bookings VALUES (?, ?, ?, ?, ?)",
                      (form['id'], form['guest_name'], form['room_type'], form['check_in'], form['check_out']))
        elif category == 'ecommerce':
            c.execute("INSERT OR REPLACE INTO ecommerce_orders VALUES (?, ?, ?, ?)",
                      (form['id'], form['product'], form['status'], form['eta']))
        elif category == 'college':
            c.execute("INSERT OR REPLACE INTO college_admissions VALUES (?, ?, ?, ?)",
                      (form['id'], form['name'], form['course'], form['status']))
        elif category == 'clinic':
            c.execute("INSERT OR REPLACE INTO dental_appointments VALUES (?, ?, ?, ?)",
                      (form['id'], form['patient_name'], form['doctor'], form['time']))
        elif category == 'fitness':
            c.execute("INSERT OR REPLACE INTO gym_memberships VALUES (?, ?, ?, ?)",
                      (form['id'], form['member_name'], form['plan'], form['expires']))
        elif category == 'real_estate':
            c.execute("INSERT OR REPLACE INTO real_estate_properties VALUES (?, ?, ?, ?)",
                      (form['id'], form['location'], form['type'], form['status']))
        elif category == 'salon':
            c.execute("INSERT OR REPLACE INTO salon_appointments VALUES (?, ?, ?, ?)",
                      (form['id'], form['client_name'], form['service'], form['time']))
        conn.commit()
    except KeyError as e:
        conn.close()
        return f"Missing field: {e}", 400
    conn.close()
    return redirect(url_for('dashboard'))

def initialize_tables():
    conn = sqlite3.connect('db.sqlite3')
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

initialize_tables()


@app.route('/delete/<category>/<int:entry_id>')
def delete_entry(category, entry_id):
    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()
    table_map = {
        'hotel': 'hotel_bookings',
        'ecommerce': 'ecommerce_orders',
        'college': 'college_admissions',
        'clinic': 'dental_appointments',
        'fitness': 'gym_memberships',
        'real_estate': 'real_estate_properties',
        'salon': 'salon_appointments'
    }
    table = table_map.get(category)
    if table:
        c.execute(f"DELETE FROM {table} WHERE id=?", (entry_id,))
        conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message')
    language = request.json.get('language', 'en')
    template = request.json.get('template', 'general')
    user_id = "default_user"

    # Initialize memory
    if user_id not in session_memory:
        session_memory[user_id] = [{
            "role": "system",
            "content": (
                f"You are LR.AI, a helpful, polite, and structured AI assistant for {template.replace('_', ' ')}. "
                "Keep replies clear, friendly, and remember previous conversation context. "
                f"All replies must be in this language: {language}."
            )
        }]

    # Add user message to memory
    session_memory[user_id].append({"role": "user", "content": user_input})

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama3-70b-8192",
        "max_tokens": 500,
        "messages": session_memory[user_id]
    }

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        reply = response.json()['choices'][0]['message']['content']

        # Add bot reply to memory
        session_memory[user_id].append({"role": "assistant", "content": reply})

        return jsonify({'reply': reply})
    except requests.exceptions.RequestException as e:
        return jsonify({'reply': f"Error: {str(e)}"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)




