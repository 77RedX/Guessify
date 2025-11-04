# app.py
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import pandas as pd
import numpy as np
import joblib
import os

app = Flask(__name__, static_folder="frontend", static_url_path="")
CORS(app)

# --- Load model & data ---
model = joblib.load("tree.joblib")
df = pd.read_csv("dataset.csv")
feature_names = df.drop("Animal", axis=1).columns.tolist()

# Question mappings
feature_questions = {
    f: f.replace('Is', 'Is it ').replace('Can', 'Can it ').replace('Has', 'Does it have ') + '?'
    for f in feature_names
}

# --- Global state for simplicity (can replace with sessions later) ---
game_state = {
    "current_index": 0,
    "answers": {}
}

# --- Utility: convert NumPy types to native Python ---
def clean_json(obj):
    if isinstance(obj, dict):
        return {k: clean_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_json(v) for v in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    else:
        return obj
    
@app.route("/")
def serve_index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/api/start", methods=["POST"])
def api_start():
    game_state["current_index"] = 0
    game_state["answers"] = {}
    question = feature_questions[feature_names[0]]
    return jsonify({"question": question, "is_guess": False})

@app.route("/api/answer", methods=["POST"])
def api_answer():
    data = request.get_json()
    answer = data.get("answer", "").lower().strip()

    if answer not in ["yes", "no"]:
        return jsonify({"error": "Invalid answer"}), 400

    value = 1 if answer == "yes" else 0
    current_index = game_state["current_index"]
    feature = feature_names[current_index]
    game_state["answers"][feature] = value

    # If we've asked all questions, make a guess
    if current_index >= len(feature_names) - 1:
        X_test = pd.DataFrame([game_state["answers"]], columns=feature_names).fillna(0)
        prediction = model.predict(X_test)[0]
        response = {"is_guess": True, "character": prediction}
    else:
        # Ask next question
        game_state["current_index"] += 1
        next_feature = feature_names[game_state["current_index"]]
        question = feature_questions[next_feature]
        response = {"is_guess": False, "question": question}

    return jsonify(clean_json(response))

if __name__ == "__main__":
    app.run(debug=True)
