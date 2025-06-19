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
    language = request.json.get('language', 'en')

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    prompt = {
        "model": "llama3-70b-8192",
        "max_tokens": 500,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are LR.AI, a helpful, polite, and concise assistant that can help answer questions for businesses, freelancers, customers, and users. "
                    "Keep your answers clear and brief. Use numbered lists when needed and adapt to the user's context. "
                    f"Respond in {language} language."
                )
            },
            {"role": "user", "content": user_input}
        ]
    }

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=prompt)
        response.raise_for_status()
        data = response.json()
        reply = data['choices'][0]['message']['content']
        return jsonify({'reply': reply})
    except Exception as e:
        return jsonify({'reply': f"Error: {str(e)}"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)
