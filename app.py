from flask import Flask, render_template, request, jsonify
import os, requests, re

app = Flask(__name__)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Dummy data per industry
COLLEGE_ADMISSIONS = {
    "101": "Admission ID 101: B.Tech in CS, Status: Confirmed.",
    "102": "Admission ID 102: BA in Psychology, Status: Pending Docs."
}

DENTAL_APPOINTMENTS = {
    "201": "Appointment ID 201: Dr. Sharma, July 2nd, 11:00 AM.",
    "202": "Appointment ID 202: Cleaning with Dr. Patel, July 3rd, 2:30 PM."
}

HOTEL_BOOKINGS = {
    "301": "Booking ID 301: Deluxe Room, Check-in: June 28, Check-out: July 1.",
    "302": "Booking ID 302: Suite Room, Check-in: July 5, 2 nights."
}

GYM_MEMBERSHIPS = {
    "401": "Membership ID 401: Valid until August 15, 2025.",
    "402": "Membership ID 402: Expired on May 30, 2025."
}

ECOM_ORDERS = {
    "501": "Order #501: Shoes - Shipped, ETA June 30.",
    "502": "Order #502: T-shirt - Delivered on June 24."
}

REAL_ESTATE = {
    "601": "Property ID 601: 2BHK Flat in Gurgaon, Status: Available.",
    "602": "Property ID 602: Studio in Mumbai, Status: Booked."
}

SALON_APPOINTMENTS = {
    "701": "Salon ID 701: Haircut with Anya, July 1 at 4 PM.",
    "702": "Salon ID 702: Facial with Meera, June 30 at 11 AM."
}

TEMPLATE_LOOKUP = {
    "college": COLLEGE_ADMISSIONS,
    "clinic": DENTAL_APPOINTMENTS,
    "hotel": HOTEL_BOOKINGS,
    "fitness": GYM_MEMBERSHIPS,
    "ecommerce": ECOM_ORDERS,
    "real_estate": REAL_ESTATE,
    "salon": SALON_APPOINTMENTS
}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message', '')
    language = request.json.get('language', 'en')
    template = request.json.get('template', 'general')

    # Detect numeric IDs and respond from data
    match = re.search(r'\b\d{3}\b', user_input)
    if template in TEMPLATE_LOOKUP and match:
        id_key = match.group()
        data = TEMPLATE_LOOKUP[template]
        if id_key in data:
            return jsonify({'reply': data[id_key]})
        else:
            return jsonify({'reply': f"Sorry, I couldn’t find any info for ID #{id_key}."})

    # Otherwise forward to Groq
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
                    "Use clean formatting, bullet points, and speak in the user's selected language: " + language
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)

