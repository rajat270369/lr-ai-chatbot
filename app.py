from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message')

    # For now, return a dummy message (replace this with your model later)
    response = f"BlueBox received: {user_input}"
    return jsonify({'reply': response})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)
