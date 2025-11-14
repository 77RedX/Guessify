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
X_df = df.drop("Animal", axis=1).astype(int)
feature_names = X_df.columns.tolist()
tree = model.tree_

# --- Question formatting ---
feature_questions = {
    f: f.replace("Is", "Is it ").replace("Can", "Can it ").replace("Has", "Does it have ") + "?"
    for f in feature_names
}

# --- Global state (for simplicity) ---
game_state = {
    "current_node": 0,   # start at root node of the tree
    "answers": {}
}

# --- Utility ---
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

# --- Serve frontend ---
@app.route("/")
def serve_index():
    return send_from_directory(app.static_folder, "index.html")

# --- Start new game ---
@app.route("/api/start", methods=["POST"])
def api_start():
    game_state["current_node"] = 0
    game_state["answers"] = {}
    node = game_state["current_node"]

    feature_index = tree.feature[node]
    feature_name = feature_names[feature_index]
    question = feature_questions.get(feature_name, feature_name + "?")

    return jsonify({"question": question, "is_guess": False})


# --- Handle user answer ---
@app.route("/api/answer", methods=["POST"])
def api_answer():
    data = request.get_json()
    answer = data.get("answer", "").lower().strip()

    if answer not in ["yes", "no"]:
        return jsonify({"error": "Invalid answer"}), 400

    value = 1 if answer == "yes" else 0
    node = game_state["current_node"]

    feature_index = tree.feature[node]
    feature_name = feature_names[feature_index]
    game_state["answers"][feature_name] = value

    # Decide next node based on the user's answer
    threshold = tree.threshold[node]
    if value <= threshold:
        next_node = tree.children_left[node]
    else:
        next_node = tree.children_right[node]

    # Check if next node is a leaf
    if tree.children_left[next_node] == tree.children_right[next_node]:
        predicted_index = np.argmax(tree.value[next_node][0])
        predicted_animal = model.classes_[predicted_index]
        return jsonify({"is_guess": True, "character": predicted_animal})

    # Otherwise, ask next question
    game_state["current_node"] = next_node
    next_feature_index = tree.feature[next_node]
    next_feature = feature_names[next_feature_index]
    next_question = feature_questions.get(next_feature, next_feature + "?")

    return jsonify(clean_json({"is_guess": False, "question": next_question}))


if __name__ == "__main__":
    app.run(debug=True)
