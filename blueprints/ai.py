from flask import Blueprint, request, jsonify
from services.ai_service import ai_service

ai_bp = Blueprint('ai', __name__)

@ai_bp.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message')
    context = data.get('context')

    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    response = ai_service.get_ai_response(user_message, context)
    return jsonify({"response": response})
