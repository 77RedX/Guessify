# app.py
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import pandas as pd
import numpy as np
import joblib

app = Flask(__name__, static_folder="frontend", static_url_path="")
CORS(app)

# =====================================================
#                 DATA LOADING / TRAINING
# =====================================================

DATA_FILE = "dataset.csv"
MODEL_FILE = "tree.joblib"

def load_data():
    try:
        df_local = pd.read_csv(DATA_FILE)
        print(f"Dataset '{DATA_FILE}' loaded successfully.")
    except Exception:
        print("Fallback dataset loaded.")
        data = {
            'Animal': ['Dog', 'Cat', 'Lion', 'Eagle', 'Shark', 'Elephant', 'Frog', 'Bat'],
            'IsMammal': [1, 1, 1, 0, 0, 1, 0, 1],
            'CanFly': [0, 0, 0, 1, 0, 0, 0, 1],
            'IsAquatic': [0, 0, 0, 0, 1, 0, 1, 0],
            'IsPet': [1, 1, 0, 0, 0, 0, 0, 0],
            'IsCarnivore': [1, 1, 1, 1, 1, 0, 0, 0],
            'IsFoundInAfrica': [0, 0, 1, 0, 0, 1, 0, 0],
            'IsLarge': [0, 0, 1, 0, 1, 1, 0, 0],
            'HasFur': [1, 1, 1, 0, 0, 0, 0, 1],
            'CanBeDomesticated': [1, 1, 0, 0, 0, 0, 0, 0],
            'IsDangerous': [0, 0, 1, 0, 1, 0, 0, 0],
            'IsHerbivore': [0, 0, 0, 0, 0, 1, 1, 0],
            'HasWings': [0, 0, 0, 1, 0, 0, 0, 1],
            'IsNocturnal': [0, 1, 1, 0, 0, 0, 1, 1],
        }
        df_local = pd.DataFrame(data)

    return df_local.drop_duplicates(subset=["Animal"]).dropna().reset_index(drop=True)


def train_model(df_local):
    X = df_local.drop("Animal", axis=1).astype(int)
    y = df_local["Animal"]
    from sklearn.tree import DecisionTreeClassifier
    model_local = DecisionTreeClassifier(random_state=42)
    model_local.fit(X, y)
    return model_local


def reverse_question(question):
    q = question.lower().strip()
    if q.startswith("is it "):
        feature = "Is" + q[5:].capitalize()
    elif q.startswith("can it "):
        feature = "Can" + q[7:].capitalize()
    elif q.startswith("does it have "):
        feature = "Has" + q[13:].capitalize()
    else:
        raise ValueError("Invalid question format.")
    return feature.strip("?")

# =====================================================
#                 LOAD GLOBALS
# =====================================================

df = load_data()
model = train_model(df)
joblib.dump(model, MODEL_FILE)

tree = model.tree_
X_df = df.drop("Animal", axis=1).astype(int)
feature_names = X_df.columns.tolist()
importances = model.feature_importances_

def make_question_text(f):
    return f.replace("Is", "Is it ").replace("Can", "Can it ").replace("Has", "Does it have ") + "?"

feature_questions = {f: make_question_text(f) for f in feature_names}

# =====================================================
#                 GAME STATE
# =====================================================

game_state = {
    "phase": "idle",          # idle / playing / refining
    "current_node": 0,
    "answers": {},
    "asked_features": [],
    "user_features": {},
    "refine_queue": [],
    "refine_index": 0,
    "second_guess": None
}

# Utilities
def clean_json(obj):
    if isinstance(obj, dict): return {k: clean_json(v) for k, v in obj.items()}
    if isinstance(obj, list): return [clean_json(v) for v in obj]
    if isinstance(obj, np.integer): return int(obj)
    if isinstance(obj, np.floating): return float(obj)
    return obj

def get_node_feature(idx):
    f = tree.feature[idx]
    return None if f == -2 else feature_names[f]

def is_leaf(idx):
    return tree.children_left[idx] == tree.children_right[idx]

def next_node(idx, val):
    th = tree.threshold[idx]
    return int(tree.children_left[idx] if val <= th else tree.children_right[idx])

# =====================================================
# ROUTES
# =====================================================

@app.route("/")
def serve_index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/api/start", methods=["POST"])
def api_start():
    game_state.update({
        "phase": "playing",
        "current_node": 0,
        "answers": {},
        "asked_features": [],
        "user_features": {},
        "refine_queue": [],
        "refine_index": 0,
        "second_guess": None
    })

    node = 0
    feat = get_node_feature(node)
    if feat is None:
        idx = np.argmax(tree.value[node][0])
        animal = model.classes_[idx]
        return jsonify({
            "is_guess": True,
            "character": animal,
            "is_second_guess": False,
            "can_go_back": False
        })

    return jsonify({
        "is_guess": False,
        "question": feature_questions[feat],
        "can_go_back": False
    })


@app.route("/api/answer", methods=["POST"])
def api_answer():
    if game_state["phase"] != "playing":
        return jsonify({"error": "Not accepting answers now"}), 400

    ans = request.json.get("answer", "").lower().strip()
    if ans not in ["yes", "no"]:
        return jsonify({"error": "Invalid answer"}), 400

    val = 1 if ans == "yes" else 0

    node = game_state["current_node"]
    feat = get_node_feature(node)
    # safety: if feat is None, something's off
    if feat is None:
        return jsonify({"error": "Invalid traversal state"}), 500

    game_state["answers"][feat] = val
    game_state["user_features"][feat] = val
    game_state["asked_features"].append(feat)

    nxt = next_node(node, val)

    if is_leaf(nxt):
        idx = np.argmax(tree.value[nxt][0])
        animal = model.classes_[idx]
        game_state["current_node"] = nxt
        return jsonify({
            "is_guess": True,
            "character": animal,
            "is_second_guess": False,
            "can_go_back": len(game_state["asked_features"]) > 0
        })

    game_state["current_node"] = nxt
    nxt_feat = get_node_feature(nxt)
    return jsonify({
        "is_guess": False,
        "question": feature_questions[nxt_feat],
        "can_go_back": len(game_state["asked_features"]) > 0
    })


@app.route("/api/start_refining", methods=["POST"])
def api_start_refining():
    game_state["phase"] = "refining"

    asked = set(game_state["answers"].keys())
    remaining = [f for f in feature_names if f not in asked]

    remaining.sort(key=lambda f: importances[feature_names.index(f)], reverse=True)

    count = max(4, min(8, max(1, len(remaining) // 3)))
    queue = remaining[:count]

    game_state["refine_queue"] = queue
    game_state["refine_index"] = 0

    first_feature = queue[0]

    return jsonify({
        "is_guess": False,
        "is_refining": True,
        "question": feature_questions[first_feature],
        "can_go_back": False
    })


@app.route("/api/refine_answer", methods=["POST"])
def api_refine_answer():
    ans = request.json.get("answer", "").lower().strip()
    val = 1 if ans == "yes" else 0

    idx = game_state["refine_index"]
    feat = game_state["refine_queue"][idx]

    # record the user's refine answer
    game_state["answers"][feat] = val
    game_state["user_features"][feat] = val

    # advance index (we have now answered idx-th refining question)
    game_state["refine_index"] += 1

    # If we've finished the refine queue -> make second guess
    if game_state["refine_index"] >= len(game_state["refine_queue"]):
        
        game_state["phase"] = "refining"
        user_vec = np.array([game_state["answers"].get(f, 0) for f in feature_names])
        distances = ((X_df.values - user_vec) != 0).sum(axis=1)
        best = np.argmin(distances)
        animal = df["Animal"].iloc[best]

        game_state["second_guess"] = animal

        # Allow going back from the second guess if there is at least one answered question
        can_go_back = len(game_state["asked_features"]) > 0 or game_state["refine_index"] > 0

        return jsonify({
            "is_guess": True,
            "character": animal,
            "is_second_guess": True,
            "is_refining": True,
            "can_go_back": can_go_back
        })

    # Otherwise send the next refining question.
    # Allow back once at least one refine answer has been given (so second refine question shows Back)
    nxt_feat = game_state["refine_queue"][game_state["refine_index"]]
    can_go_back = game_state["refine_index"] > 0  # True if we've answered at least one refine question

    return jsonify({
        "is_guess": False,
        "is_refining": True,
        "question": feature_questions[nxt_feat],
        "can_go_back": can_go_back
    })
@app.route("/api/refine_back", methods=["POST"])
def api_refine_back():
    # Must be in refining phase
    if game_state["phase"] != "refining":
        return jsonify({"error": "Not in refining mode"}), 400

    # Cannot go back from the very first refine question
    if game_state["refine_index"] <= 0:
        return jsonify({"error": "Already at first refine question"}), 400

    # Move back one refine question
    game_state["refine_index"] -= 1

    # Identify which feature we are undoing
    feat = game_state["refine_queue"][game_state["refine_index"]]

    # Remove its stored answer
    game_state["answers"].pop(feat, None)
    game_state["user_features"].pop(feat, None)

    # Now show the previous refine question
    prev_feat = feat

    return jsonify({
        "is_guess": False,
        "is_refining": True,
        "question": feature_questions[prev_feat],
        "can_go_back": game_state["refine_index"] > 0
    })


@app.route("/api/back", methods=["POST"])
def api_back():
    global game_state, tree, feature_names, feature_questions

    # No going back during refining mode
    if game_state["phase"] == "refining":
        return jsonify({"error": "Cannot go back during refining"}), 400

    asked = game_state["asked_features"]

    # If nothing answered yet → cannot go back
    if len(asked) == 0:
        return jsonify({"error": "Already at first question"}), 400

    # Remove last answered question
    last_feature = asked.pop()
    game_state["answers"].pop(last_feature, None)
    game_state["user_features"].pop(last_feature, None)

    # Re-traverse from root
    node = 0

    for feat in asked:
        val = game_state["answers"][feat]
        feature_index = feature_names.index(feat)

        # Follow the actual tree path
        # traverse until we hit the split node for this feature (or leaf)
        progressed = False
        while True:
            if is_leaf(node):
                break
            if tree.feature[node] == feature_index:
                thresh = tree.threshold[node]
                node = tree.children_left[node] if val <= thresh else tree.children_right[node]
                progressed = True
                break
            # otherwise step into left child and continue searching
            left = tree.children_left[node]
            if left == tree.children_right[node]:
                break
            node = left

        # if we didn't find the exact split node, just continue with current node state

    game_state["current_node"] = int(node)

    # If leaf → return the guess
    if is_leaf(node):
        animal_idx = np.argmax(tree.value[node][0])
        animal = model.classes_[animal_idx]
        return jsonify({
            "is_guess": True,
            "character": animal,
            "is_second_guess": False,
            "can_go_back": len(asked) > 0
        })

    # Otherwise return previous question
    feat_index = tree.feature[node]
    feat_name = feature_names[feat_index]
    return jsonify({
        "is_guess": False,
        "question": feature_questions[feat_name],
        "can_go_back": len(asked) > 0
    })


@app.route("/api/learn", methods=["POST"])
def api_learn():
    global df, model, tree, X_df, feature_names, importances, feature_questions

    data = request.json
    wrong = data.get("wrong_guess")
    correct = data.get("correct_answer")
    question = data.get("new_question")
    ans = data.get("new_question_answer")

    if not correct or not question:
        return jsonify({"error": "Missing fields"}), 400

    feature = reverse_question(question)

    if feature not in df.columns:
        df[feature] = 0

    exists = correct in df["Animal"].values

    if exists:
        df.loc[df["Animal"] == correct, feature] = 1 if ans.lower()=="yes" else 0
    else:
        new_row = {}
        for col in df.columns:
            if col == "Animal":
                continue
            val = game_state["user_features"].get(col, game_state["answers"].get(col, 0))
            new_row[col] = int(val)
        new_row["Animal"] = correct

        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

        df.loc[df["Animal"] == correct, feature] = 1 if ans.lower()=="yes" else 0

    df[df.columns[df.columns!="Animal"]] = df[df.columns[df.columns!="Animal"]].fillna(0).astype(int)
    df.to_csv(DATA_FILE, index=False)

    model = train_model(df)
    joblib.dump(model, MODEL_FILE)

    tree = model.tree_
    X_df = df.drop("Animal", axis=1).astype(int)
    feature_names = X_df.columns.tolist()
    importances = model.feature_importances_
    feature_questions = {f: make_question_text(f) for f in feature_names}

    game_state.update({
        "phase": "idle",
        "current_node": 0,
        "answers": {},
        "asked_features": [],
        "user_features": {},
        "refine_queue": [],
        "refine_index": 0,
        "second_guess": None
    })

    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True)
