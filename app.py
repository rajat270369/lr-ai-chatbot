import os
import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Load Groq API Key
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

if GROQ_API_KEY:
    print("✅ Groq API Key loaded.")
else:
    print("❌ Groq API Key not found.")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message')
    language = request.json.get('language', 'en')
    template = request.json.get('template', 'general')

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    industry_prompts = {
    "college": "You are an admissions assistant for a college. Help with courses, fees, scholarships, and campus life.",
    "clinic": "You are a clinic receptionist assistant. Help with appointments, services, timings, and patient queries.",
    "hotel": "You assist hotel guests. Help with room availability, pricing, booking, and facilities.",
    "ecommerce": "You are a product assistant for an online store. Help with product suggestions, order tracking, and returns.",
    "salon": "You are a salon booking assistant. Help clients pick styles, book slots, and view prices.",
    "consultant": "You are a consultant lead bot. Ask qualifying questions and explain services clearly.",
    "fitness": "You are a gym assistant. Suggest workout plans, book trainer sessions, and answer fitness questions.",
    "real_estate": "You are a property assistant. Help users find houses based on location, price, and type.",
    "therapist": "You are a calm mental health assistant. Help users understand therapy options and book sessions."
}

industry_prompt = industry_prompts.get(template, "You are a helpful and polite AI assistant for all types of businesses.")

payload = {
    "model": "llama3-70b-8192",
    "max_tokens": 500,
    "messages": [
        {
            "role": "system",
            "content": (
                f"{industry_prompt} "
                "Keep responses short, use bullet points if listing, and keep them clean and readable. "
                f"Reply in this language: {language}."
            )
        },
        {
            "role": "user",
            "content": user_input
        }
      ]
    }


    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        reply = data['choices'][0]['message']['content']
        return jsonify({'reply': reply})
    except requests.exceptions.RequestException as e:
        return jsonify({'reply': f"Error: {str(e)}"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)
