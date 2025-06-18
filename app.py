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
                    "You are BlueBox, a helpful and concise assistant built for students. "
                    "Keep responses short and to the point. When the user asks about multiple items or categories, "
                    "format the answer as a clean, numbered list.\n\n"
                    "Example:\n"
                    "User: What are some popular engineering branches?\n"
                    "Assistant:\n"
                    "1. Computer Science\n"
                    "2. Mechanical Engineering\n"
                    "3. Electrical Engineering\n"
                    "4. Civil Engineering\n"
                    "5. Chemical Engineering\n"
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
