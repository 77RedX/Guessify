import pandas as pd
from sklearn.tree import DecisionTreeClassifier
import numpy as np
from flask import Flask, jsonify, request, session
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app) 
app.secret_key = os.urandom(24) 

def load_data():
    FILE_NAME = 'dataset.csv'
    df = None
    try:
        df = pd.read_csv(FILE_NAME)
        print(f"Dataset '{FILE_NAME}' loaded successfully.")
    except Exception as e:
        print(f"Warning: Could not load '{FILE_NAME}' ({e}). Using fallback dataset.")
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
        df = pd.DataFrame(data)

    df = df.drop_duplicates(subset=['Animal']).dropna()
    return df

def train_model(X, y):
    model = DecisionTreeClassifier(random_state=42)
    model.fit(X, y)
    return model

def format_question(feature_name):
    q = feature_name
    if q.startswith('Is'):
        q = q.replace('Is', 'Is it ')
    elif q.startswith('Can'):
        q = q.replace('Can', 'Can it ')
    elif q.startswith('Has'):
        q = q.replace('Has', 'Does it have ')
    
    q = q.replace('BeDomesticated', 'be domesticated')
    q = q.replace('Aquatic', 'aquatic')
    q = q.replace('Carnivore', 'carnivorous')
    q = q.replace('Herbivore', 'herbivorous')
    q = q.replace('Dangerous', 'dangerous')
    q = q.replace('Mammal', 'a mammal')
    q = q.replace('FoundInAfrica', 'found in Africa')
    q = q.replace('Fur', 'fur')
    q = q.replace('Wings', 'wings')
    q = q.replace('Nocturnal', 'nocturnal')
    q = q.replace('Pet', 'a pet')
    q = q.replace('Large', 'large')
    
    return q.strip() + '?'

try:
    GLOBAL_DF = load_data()
    GLOBAL_X = GLOBAL_DF.drop('Animal', axis=1).astype(int)
    GLOBAL_Y = GLOBAL_DF['Animal']
    GLOBAL_MODEL = train_model(GLOBAL_X, GLOBAL_Y)
    GLOBAL_TREE = GLOBAL_MODEL.tree_
    GLOBAL_FEATURE_NAMES = GLOBAL_X.columns.tolist()
    print("--- Model trained and ready! ---")
except Exception as e:
    print(f"FATAL ERROR: Could not train model on startup. {e}")
    GLOBAL_MODEL = None 

def get_next_question_or_guess(node_index):
    if GLOBAL_TREE.children_left[node_index] == GLOBAL_TREE.children_right[node_index]:
        predicted_index = np.argmax(GLOBAL_TREE.value[node_index][0])
        character_guess = GLOBAL_MODEL.classes_[predicted_index]
        return {
            "is_guess": True,
            "character": character_guess,
            "question": f"Is it {character_guess}?"
        }
    
    feature_index = GLOBAL_TREE.feature[node_index]
    feature_name = GLOBAL_FEATURE_NAMES[feature_index]
    question = format_question(feature_name)
    
    return {
        "is_guess": False,
        "question": question,
        "node_index": node_index
    }

@app.route('/api/start', methods=['POST'])
def api_start():
    if GLOBAL_MODEL is None:
        return jsonify({"error": "Model not loaded"}), 500

    session['current_node'] = 0
    response_data = get_next_question_or_guess(0)
    return jsonify(response_data)

@app.route('/api/answer', methods=['POST'])
def api_answer():
    if GLOBAL_MODEL is None:
        return jsonify({"error": "Model not loaded"}), 500

    data = request.json
    answer = data.get('answer')
    
    if 'current_node' not in session:
        return api_start()
        
    current_node_index = session['current_node']
    
    if answer == 'Yes':
        next_node_index = GLOBAL_TREE.children_right[current_node_index]
    else:
        next_node_index = GLOBAL_TREE.children_left[current_node_index]

    session['current_node'] = int(next_node_index)
    
    response_data = get_next_question_or_guess(next_node_index)
    return jsonify(response_data)

if __name__ == '__main__':
    app.run(debug=True, port=5000)

