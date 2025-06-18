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
        "max_tokens": 600,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are BlueBox, a concise and helpful assistant for students. "
                    "Keep replies short and clear. When asked about multiple items (like steps, options, or colleges), "
                    "always format the answer as a numbered list."
                )
            },
            {
                "role": "user",
                "content": "Can you give me 5 tips to prepare for exams?"
            },
            {
                "role": "assistant",
                "content": (
                    "1. Make a study schedule and stick to it.\n"
                    "2. Focus on understanding concepts, not just memorizing.\n"
                    "3. Take regular breaks to avoid burnout.\n"
                    "4. Practice with past papers and mock tests.\n"
                    "5. Get enough sleep before the exam day."
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
