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

def normalize_input_animal(name):
    name = name.strip().lower()
    if not name:
        return ""
    return name[0].upper() + name[1:]


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
    "phase": "idle",            # idle / playing / refining / filling_attributes
    "current_node": 0,
    "answers": {},
    "asked_features": [],
    "user_features": {},
    "refine_queue": [],
    "refine_index": 0,
    "second_guess": None,
}

# Utilities
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

    i = game_state["refine_index"]
    feat = game_state["refine_queue"][i]

    game_state["answers"][feat] = val
    game_state["user_features"][feat] = val
    game_state["refine_index"] += 1

    if game_state["refine_index"] >= len(game_state["refine_queue"]):
        game_state["phase"] = "refining"

        # Build user vector: 1 = yes, 0 = no, -1 = unknown
        user_vec = np.array([game_state["answers"].get(f, -1) for f in feature_names])

        # Compute Hamming distance ignoring unknown answers
        distances = []
        for row in X_df.values:
            d = 0
            for a, b in zip(user_vec, row):
                if a == -1:
                    continue  # Skip unanswered features
                if a != b:
                    d += 1
            distances.append(d)

        best = int(np.argmin(distances))
        animal = df["Animal"].iloc[best]


        game_state["second_guess"] = animal

        return jsonify({
            "is_guess": True,
            "character": animal,
            "is_second_guess": True,
            "is_refining": True,
            "can_go_back": True
        })

    nxt_feat = game_state["refine_queue"][game_state["refine_index"]]

    return jsonify({
        "is_guess": False,
        "is_refining": True,
        "question": feature_questions[nxt_feat],
        "can_go_back": True
    })

@app.route("/api/refine_back", methods=["POST"])
def api_refine_back():
    if game_state["phase"] != "refining":
        return jsonify({"error": "Not in refining mode"}), 400

    if game_state["refine_index"] <= 0:
        return jsonify({"error": "Already at first refine question"}), 400

    game_state["refine_index"] -= 1

    feat = game_state["refine_queue"][game_state["refine_index"]]

    game_state["answers"].pop(feat, None)
    game_state["user_features"].pop(feat, None)

    return jsonify({
        "is_guess": False,
        "is_refining": True,
        "question": feature_questions[feat],
        "can_go_back": game_state["refine_index"] > 0
    })

@app.route("/api/back", methods=["POST"])
def api_back():
    if game_state["phase"] == "refining":
        return jsonify({"error": "Cannot go back during refining"}), 400

    asked = game_state["asked_features"]
    if len(asked) == 0:
        return jsonify({"error": "Already at first question"}), 400

    last = asked.pop()
    game_state["answers"].pop(last, None)
    game_state["user_features"].pop(last, None)

    node = 0

    for feat in asked:
        val = game_state["answers"][feat]
        idx = feature_names.index(feat)

        while not is_leaf(node):
            if tree.feature[node] == idx:
                node = tree.children_left[node] if val <= tree.threshold[node] else tree.children_right[node]
                break
            left = tree.children_left[node]
            if left == tree.children_right[node]:
                break
            node = left

    game_state["current_node"] = node

    if is_leaf(node):
        animal = model.classes_[np.argmax(tree.value[node][0])]
        return jsonify({
            "is_guess": True,
            "character": animal,
            "is_second_guess": False,
            "can_go_back": len(asked) > 0
        })

    feat_name = feature_names[tree.feature[node]]
    return jsonify({
        "is_guess": False,
        "question": feature_questions[feat_name],
        "can_go_back": len(asked) > 0
    })

# =====================================================
#     LEARNING (NEW) — EXISTING VS NEW ANIMAL
# =====================================================

@app.route("/api/learn", methods=["POST"])
def api_learn():
    global df, model, tree, X_df, feature_names, importances, feature_questions

    data = request.json
    correct = data.get("correct_answer","")
    wrong = data.get("wrong_guess")

    if not correct:
        return jsonify({"error": "Missing correct_answer"}), 400

    exists = correct in df["Animal"].tolist()

    # Case: This request includes the distinguishing question
    q = data.get("new_question")
    a = data.get("new_question_answer")

    if exists and q and a:
        feature = reverse_question(q)
        if feature not in df.columns:
            df[feature] = 0

        user_val = 1 if a.lower() == "yes" else 0
        wrong_val = 1 - user_val
        df.loc[df["Animal"] == correct, feature] = user_val
        df.loc[df["Animal"] == wrong, feature] = wrong_val

        df.to_csv(DATA_FILE, index=False)
        model = train_model(df)
        joblib.dump(model, MODEL_FILE)

        tree = model.tree_
        X_df = df.drop("Animal", axis=1).astype(int)
        feature_names = X_df.columns.tolist()
        importances = model.feature_importances_
        feature_questions = {f: make_question_text(f) for f in feature_names}

        reset_state()
        return jsonify({"status": "ok", "learned": "updated_existing"})

    if exists and not (q and a):
        return jsonify({"status": "ask_distinguishing"})

    # NEW ANIMAL CASE
    game_state["phase"] = "filling_attributes"
    game_state["new_animal"] = correct
    game_state["fill_index"] = 0
    game_state["fill_answers"] = {}

    first_feat = feature_names[0] if feature_names else None

    if not first_feat:
        df.loc[len(df)] = {"Animal": correct}
        df.to_csv(DATA_FILE, index=False)
        reset_state()
        return jsonify({"status": "done", "animal_added": correct})

    return jsonify({
        "is_filling": True,
        "feature": first_feat,
        "question": feature_questions[first_feat],
        "index": 0
    })

@app.route("/api/attribute_answer", methods=["POST"])
def api_attribute_answer():
    global df, model, tree, X_df, feature_names, importances, feature_questions

    if game_state["phase"] != "filling_attributes":
        return jsonify({"error": "Not in attribute filling mode"}), 400

    ans = request.json.get("answer", "").lower().strip()
    if ans not in ["yes", "no"]:
        return jsonify({"error": "Invalid answer"}), 400

    val = 1 if ans == "yes" else 0
    idx = game_state["fill_index"]
    feat = feature_names[idx]

    game_state["fill_answers"][feat] = val
    game_state["fill_index"] += 1

    if game_state["fill_index"] >= len(feature_names):
        new_row = {f: game_state["fill_answers"].get(f, 0) for f in feature_names}
        new_row["Animal"] = game_state["new_animal"]

        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df[df.columns[df.columns!="Animal"]] = df[df.columns[df.columns!="Animal"]].fillna(0)

        df.to_csv(DATA_FILE, index=False)
        model = train_model(df)
        joblib.dump(model, MODEL_FILE)

        tree = model.tree_
        X_df = df.drop("Animal", axis=1).astype(int)
        feature_names = X_df.columns.tolist()
        importances = model.feature_importances_
        feature_questions = {f: make_question_text(f) for f in feature_names}

        added = game_state["new_animal"]
        reset_state()

        return jsonify({"status": "done", "animal_added": added})

    next_feat = feature_names[game_state["fill_index"]]

    return jsonify({
        "is_filling": True,
        "feature": next_feat,
        "question": feature_questions[next_feat],
        "index": game_state["fill_index"]
    })

def reset_state():
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

if __name__ == "__main__":
    app.run(debug=True)
