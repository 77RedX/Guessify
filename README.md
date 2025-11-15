# Guessify
A game that guesses a character/animal/object based on some questions. 
🐾 Guessify
A self-learning animal guessing game powered by decision trees + dynamic knowledge expansion.

Guessify is an intelligent guessing engine inspired by Akinator.
It asks Yes/No questions, predicts an animal, and learns from mistakes — expanding its dataset automatically.

Built with:

Flask (Python Backend)

DecisionTreeClassifier (Scikit-learn)

Dynamic CSV dataset

Interactive HTML/CSS/JS frontend

Refining questions + backtracking

Two-phase learning (existing animals vs. new animals)

🚀 Features
✔ Decision Tree Guessing

Guessify starts a simple Q&A session using a trained Decision Tree Classifier.

✔ Refining Phase

If the first guess is wrong:

Guessify asks a small set of high-importance questions (not asked in the tree path)

This improves accuracy for the second guess

✔ Second Guess Logic

Uses a smart Hamming-distance similarity algorithm:

Uses all known answers from tree + refine phases

Unknown answers are ignored (not treated as "No")

Guarantees best match

This fixes the problem where second guess could be inaccurate.

✔ Dynamic Learning

If both guesses are wrong:

🟦 If the animal exists in the dataset

→ Ask one distinguishing question
→ Add/modify only that feature for that animal

🟩 If the animal is NEW

→ Ask user:

This animal does not exist in our dataset.
Would you like to add it?
[ Add Animal ]   [ New Game ]


→ Ask user to fill ALL attributes
→ Add full row to dataset

✔ Back Button Support

Go back during tree phase

Go back during refining phase

Full path reconstruction from saved answers

✔ Dataset Autoupdates

Dataset stored in CSV (dataset.csv)

Automatically reloads + retrains model after learning

New features (columns) added dynamically

📁 Project Structure
project/
│── frontend/
│   ├── index.html
│   ├── styles.css
│   └── script.js
│
│── dataset.csv
│── tree.joblib
│── app.py
│── README.md

🧠 How Guessify Works (Deep Dive)
1. Tree Phase

Uses Decision Tree to pick a path of questions

Tracks answers + asked_features

2. First Guess

Uses leaf node prediction:

My guess is… <animal>!


If wrong → refining begins.

3. Refining Phase

Selects remaining features NOT asked yet

Sorts by feature importance

Asks ~4–8 high-value questions

Supports backtracking inside refining

4. Second Guess

Builds user_vec using:

Tree answers

Refining answers

unknown = -1 (meaning skip)

Calculates Hamming distance:

distance += 1 only when: user_answer != dataset_answer
unknown answers → ignored


Closest matching animal becomes second guess.

5. Learning
📌 Case A: animal exists

Update only a single new question:

Distinguishing Question → Converted to Feature → Applied to that animal

📌 Case B: new animal

Flow:

“Would you like to add it?”

User clicks “Proceed”

Ask ALL attributes one-by-one

Add full row

Retrain model

🛠 Installation
1️⃣ Install dependencies
pip install flask flask-cors pandas scikit-learn joblib numpy

2️⃣ Run the server
python app.py

3️⃣ Open the frontend

Visit:

http://127.0.0.1:5000

🧪 Adding Knowledge Manually

dataset.csv can be edited manually to adjust or clean-up known animals.

Adding a new column = new question.
Guessify automatically handles it!

🔮 Future Improvements (Optional)

GUI/Desktop version

User-facing dataset editor

Multi-language support

Speech input (“yes/no”)

Animated transitions

More ML models (Random Forest, CatBoost)

Export knowledge stats