import os
import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message')

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
                    "You are LR.AI, a helpful and concise assistant for students. "
                    "Keep replies short and structured. If asked about multiple items or steps, respond with a clean, numbered list."
                )
            },
            {"role": "user", "content": user_input}
        ]
    }

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        reply = response.json()['choices'][0]['message']['content']
        return jsonify({'reply': reply})
    except Exception as e:
        return jsonify({'reply': f"Error: {e}"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)
