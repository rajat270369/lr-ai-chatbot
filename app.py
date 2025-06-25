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
                   "You are LR.AI, an assistant for businesses. "
                   "Keep responses short, clear, and easy to scan. "
                   "Use a maximum of 3 to 5 bullet points or lines unless the user asks for more. "
                   "Avoid long paragraphs. Use short sentences. "
                   "Add spacing between points. Always respond in this language: " + language
                     )

            },
            {"role": "user", "content": user_input}
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
