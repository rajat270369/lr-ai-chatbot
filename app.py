import os
import re
import sqlite3
import requests
from flask import Flask, render_template, request, jsonify, redirect, session, url_for

app = Flask(__name__)
app.secret_key = "your_strong_secret_here"  # Used for session-based login

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# ----------------------------
# DATABASE INIT FUNCTION
# ----------------------------
def init_db():
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

init_db()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message', '')
    language = request.json.get('language', 'en')
    template = request.json.get('template', 'general')

    match = re.search(r'\b\d{3}\b', user_input)
    if match:
        id_key = match.group()
        conn = sqlite3.connect('db.sqlite3')
        c = conn.cursor()
        result = None
        reply = None

        if template == "hotel":
            c.execute("SELECT * FROM hotel_bookings WHERE id = ?", (id_key,))
            result = c.fetchone()
            if result:
                reply = f"Booking ID {id_key}: {result[1]} booked a {result[2]} from {result[3]} to {result[4]}."
        elif template == "ecommerce":
            c.execute("SELECT * FROM ecommerce_orders WHERE id = ?", (id_key,))
            result = c.fetchone()
            if result:
                reply = f"Order {id_key}: {result[1]} - Status: {result[2]}, ETA: {result[3]}."
        elif template == "college":
            c.execute("SELECT * FROM college_admissions WHERE id = ?", (id_key,))
            result = c.fetchone()
            if result:
                reply = f"Admission ID {id_key}: {result[1]}, Course: {result[2]}, Status: {result[3]}."
        elif template == "clinic":
            c.execute("SELECT * FROM dental_appointments WHERE id = ?", (id_key,))
            result = c.fetchone()
            if result:
                reply = f"Appointment ID {id_key}: {result[1]} with {result[2]} at {result[3]}."
        elif template == "fitness":
            c.execute("SELECT * FROM gym_memberships WHERE id = ?", (id_key,))
            result = c.fetchone()
            if result:
                reply = f"Membership ID {id_key}: {result[1]}, Plan: {result[2]}, Expires: {result[3]}."
        elif template == "real_estate":
            c.execute("SELECT * FROM real_estate_properties WHERE id = ?", (id_key,))
            result = c.fetchone()
            if result:
                reply = f"Property ID {id_key}: {result[1]}, Type: {result[2]}, Status: {result[3]}."
        elif template == "salon":
            c.execute("SELECT * FROM salon_appointments WHERE id = ?", (id_key,))
            result = c.fetchone()
            if result:
                reply = f"Appointment ID {id_key}: {result[1]}, Service: {result[2]}, Time: {result[3]}."

        conn.close()

        if reply:
            return jsonify({'reply': reply})
        else:
            return jsonify({'reply': f"Sorry, I couldn't find any record for ID {id_key}."})

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama3-70b-8192",
        "max_tokens": 500,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are LR.AI, a helpful assistant for small businesses. "
                    "Ask the user for an ID (like booking or order ID) if the question implies a specific lookup. "
                    "Use bullet points and be concise. Reply in the user's language: " + language
                )
            },
            {"role": "user", "content": user_input}
        ]
    }

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return jsonify({'reply': data['choices'][0]['message']['content']})
    except requests.exceptions.RequestException as e:
        return jsonify({'reply': f"Error: {str(e)}"})

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == "admin123":
            session['admin'] = True
            return redirect(url_for('dashboard'))
        return "Incorrect password", 403
    return render_template('admin_login.html')

@app.route('/dashboard')
def dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin'))

    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()
    hotel = c.execute('SELECT * FROM hotel_bookings').fetchall()
    ecommerce = c.execute('SELECT * FROM ecommerce_orders').fetchall()
    college = c.execute('SELECT * FROM college_admissions').fetchall()
    clinic = c.execute('SELECT * FROM dental_appointments').fetchall()
    fitness = c.execute('SELECT * FROM gym_memberships').fetchall()
    real_estate = c.execute('SELECT * FROM real_estate_properties').fetchall()
    salon = c.execute('SELECT * FROM salon_appointments').fetchall()
    conn.close()

    return render_template('admin_dashboard.html', hotel=hotel, ecommerce=ecommerce, college=college, clinic=clinic, fitness=fitness, real_estate=real_estate, salon=salon)

@app.route('/add/<category>', methods=['POST'])
def add_entry(category):
    conn = sqlite3.connect('db.sqlite3')
    c = conn.cursor()
    form = request.form
    tables = {
        'hotel': ("INSERT OR REPLACE INTO hotel_bookings VALUES (?, ?, ?, ?, ?)",
                  (form['id'], form['guest_name'], form['room_type'], form['check_in'], form['check_out'])),
        'ecommerce': ("INSERT OR REPLACE INTO ecommerce_orders VALUES (?, ?, ?, ?)",
                      (form['id'], form['product'], form['status'], form['eta'])),
        'college': ("INSERT OR REPLACE INTO college_admissions VALUES (?, ?, ?, ?)",
                    (form['id'], form['name'], form['course'], form['status'])),
        'clinic': ("INSERT OR REPLACE INTO dental_appointments VALUES (?, ?, ?, ?)",
                   (form['id'], form['patient_name'], form['doctor'], form['time'])),
        'fitness': ("INSERT OR REPLACE INTO gym_memberships VALUES (?, ?, ?, ?)",
                    (form['id'], form['member_name'], form['plan'], form['expires'])),
        'real_estate': ("INSERT OR REPLACE INTO real_estate_properties VALUES (?, ?, ?, ?)",
                        (form['id'], form['location'], form['type'], form['status'])),
        'salon': ("INSERT OR REPLACE INTO salon_appointments VALUES (?, ?, ?, ?)",
                  (form['id'], form['client_name'], form['service'], form['time']))
    }
    if category in tables:
        query, data = tables[category]
        c.execute(query, data)
        conn.commit()
    conn.close()
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)


