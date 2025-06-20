import os
import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Load Groq API Key from environment variables
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Print key status (not the key itself) for debugging
if GROQ_API_KEY:
    print("✅ Groq API Key loaded successfully.")
else:
    print("❌ Groq API Key NOT FOUND. Please set GROQ_API_KEY in environment variables.")

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
                    "You are LR.AI, a helpful, polite, and concise assistant that helps businesses, freelancers, and users. "
                    "Respond clearly, use numbered lists when applicable, and adapt based on the user's language. "
                    f"Reply in the user's language: {language}."
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
