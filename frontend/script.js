const API = "http://127.0.0.1:5000";

let loadingScreen, startScreen, gameContainer, startBtn;
let questionText, answerButtonsContainer;

document.addEventListener("DOMContentLoaded", () => {
    loadingScreen = document.getElementById("loading-screen");
    startScreen = document.getElementById("start-screen");
    gameContainer = document.getElementById("game-container");
    startBtn = document.getElementById("start-btn");
    questionText = document.querySelector(".question-text");
    answerButtonsContainer = document.getElementById("answer-buttons");

    window.addEventListener("load", onLoaded);
    startBtn.addEventListener("click", startGame);
});

function onLoaded() {
    setTimeout(() => {
        loadingScreen.classList.add("fade-out");
        loadingScreen.addEventListener("transitionend", () => {
            loadingScreen.classList.add("hidden");
            startScreen.classList.remove("hidden");
        }, { once: true });
    }, 1000);
}

async function startGame() {
    startScreen.classList.add("hidden");
    loadingScreen.classList.remove("hidden");

    const res = await fetch(`${API}/api/start`, { method: "POST" });
    const data = await res.json();

    loadingScreen.classList.add("hidden");
    gameContainer.classList.remove("hidden");

    updateUI(data);
}

async function sendAnswer(answer) {
    questionText.textContent = "Thinking...";
    answerButtonsContainer.innerHTML = "";

    const res = await fetch(`${API}/api/answer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answer })
    });

    const data = await res.json();

    if (data.error) {
        questionText.textContent = data.error;
        return;
    }

    updateUI(data);
}

async function startRefining() {
    questionText.textContent = "Let me think more...";
    answerButtonsContainer.innerHTML = `<div class="spinner"></div>`;

    const res = await fetch(`${API}/api/start_refining`, {
        method: "POST",
        headers: { "Content-Type": "application/json" }
    });

    const data = await res.json();
    updateUI(data);
}

async function refineAnswer(answer) {
    const res = await fetch(`${API}/api/refine_answer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answer })
    });

    const data = await res.json();

    if (data.error) {
        questionText.textContent = data.error;
        return;
    }

    updateUI(data);
}

async function goBack() {
    questionText.textContent = "Going back...";
    answerButtonsContainer.innerHTML = `<div class="spinner"></div>`;

    try {
        const res = await fetch(`${API}/api/back`, {
            method: "POST",
            headers: { "Content-Type": "application/json" }
        });

        const data = await res.json();

        if (data.error) {
            questionText.textContent = data.error;
            answerButtonsContainer.innerHTML = `<button onclick="goBack()">Try Again</button>`;
            return;
        }

        updateUI(data);

    } catch (err) {
        console.error(err);
        questionText.textContent = "Error going back.";
    }
}
async function refineBack() {
    questionText.textContent = "Going back...";
    answerButtonsContainer.innerHTML = `<div class="spinner"></div>`;

    const res = await fetch(`${API}/api/refine_back`, {
        method: "POST",
        headers: { "Content-Type": "application/json" }
    });

    const data = await res.json();

    if (data.error) {
        questionText.textContent = data.error;
        return;
    }

    updateUI(data);
}


function updateUI(data) {
    // ============================
    //  GUESS SCREEN
    // ============================
    if (data.is_guess) {
        questionText.textContent = `My guess is… ${data.character}! Is that correct?`;

        answerButtonsContainer.innerHTML = `
    <button onclick="guessYes()">Yes</button>
    <button onclick="guessNo(${data.is_second_guess})">No</button>
    ${
        data.can_go_back
            ? (data.is_refining
                ? `<button onclick="refineBack()">⬅ Back</button>`
                : `<button onclick="goBack()">⬅ Back</button>`)
            : ""
    }
`;
        return;
    }

    // ============================
    //  QUESTION SCREEN
    // ============================
    questionText.textContent = data.question;

    if (data.is_refining) {
    let html = `
        <button onclick="refineAnswer('yes')">Yes</button>
        <button onclick="refineAnswer('no')">No</button>
    `;

    if (data.can_go_back) {
        html += `<button onclick="refineBack()">⬅ Back</button>`;
    }

    answerButtonsContainer.innerHTML = html;
    return;
}



    // Normal tree traversal
    let html = `
        <button onclick="sendAnswer('yes')">Yes</button>
        <button onclick="sendAnswer('no')">No</button>
    `;

    if (data.can_go_back) html += `<button onclick="goBack()">⬅ Back</button>`;

    answerButtonsContainer.innerHTML = html;
}


// ======================================================
//       GUESS HANDLERS
// ======================================================

function guessYes() {
    questionText.textContent = "Great! I guessed it!";
    answerButtonsContainer.innerHTML = `
        <button onclick="resetGame()" id="play-again-btn">Play Again</button>
    `;
}

function guessNo(isSecondGuess) {
    // Extract wrong guess cleanly
    const text = document.querySelector(".question-text").textContent;
    window.lastWrongGuess = text
        .replace("My guess is…", "")
        .replace("Is that correct?", "")
        .replace("!", "")
        .trim();

    if (isSecondGuess) {
        showLearningForm();
        return;
    }

    startRefining();
}


// ======================================================
//          LEARNING FORM
// ======================================================

function showLearningForm() {
    questionText.textContent = "Help me learn!";

    answerButtonsContainer.innerHTML = `
        <form onsubmit="submitLearning(event)">
            <label>Correct Animal:</label>
            <input id="correct" required>

            <label>Distinguishing Question:</label>
            <input id="q" required>

            <label>Correct answer to that question:</label>
            <select id="a">
                <option>Yes</option>
                <option>No</option>
            </select>

            <button type="submit">Submit</button>
        </form>
    `;
}

async function submitLearning(e) {
    e.preventDefault();

    const correct = document.getElementById("correct").value;
    const q = document.getElementById("q").value;
    const a = document.getElementById("a").value;

    await fetch(`${API}/api/learn`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            wrong_guess: window.lastWrongGuess,
            correct_answer: correct,
            new_question: q,
            new_question_answer: a
        })
    });

    resetGame();
}


// ======================================================
//          RESET GAME
// ======================================================

function resetGame() {
    gameContainer.classList.add("hidden");
    startScreen.classList.remove("hidden");
}
