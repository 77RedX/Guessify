// Import Express
const express = require('express');
const app = express();
const PORT = 3000;

// Enable JSON parsing for POST requests
app.use(express.json());

// ====== Placeholder Decision Tree Logic ======
// Later, you will replace this with your tree.js logic
let currentQuestion = "Is it an animal?";
let answers = []; // stores yes/no answers

// ====== API Endpoints ======

// Test endpoint
app.get('/', (req, res) => {
    res.send('Hello from Node.js backend!');
});

// Get the next question
app.get('/question', (req, res) => {
    res.json({ question: currentQuestion });
});

// Submit answer (yes/no)
app.post('/answer', (req, res) => {
    const { answer } = req.body;
    if (!answer) return res.status(400).json({ error: "Answer required" });

    // Save the answer (you will use this to traverse the tree)
    answers.push(answer);

    // For now, just send a dummy next question
    currentQuestion = "Is it bigger than a breadbox?";
    res.json({ question: currentQuestion });
});

// Learn a new character
app.post('/learn', (req, res) => {
    const { name, questionForNewCharacter, answerForNewCharacter } = req.body;
    if (!name || !questionForNewCharacter || !answerForNewCharacter) {
        return res.status(400).json({ error: "Missing data" });
    }

    // Here you will add the new character to your tree
    res.json({ message: `Learned new character: ${name}` });
});

// Start the server
app.listen(PORT, () => {
    console.log(`Server running at http://localhost:${PORT}`);
});
