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

    updateUI(await res.json());
}

async function startRefining() {
    questionText.textContent = "Let me think more...";
    answerButtonsContainer.innerHTML = `<div class="spinner"></div>`;

    const data = await (await fetch(`${API}/api/start_refining`, {
        method: "POST",
        headers: { "Content-Type": "application/json" }
    })).json();

    updateUI(data);
}

async function refineAnswer(answer) {
    const data = await (await fetch(`${API}/api/refine_answer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answer })
    })).json();

    updateUI(data);
}

async function refineBack() {
    const data = await (await fetch(`${API}/api/refine_back`, {
        method: "POST",
        headers: { "Content-Type": "application/json" }
    })).json();

    updateUI(data);
}

async function goBack() {
    const data = await (await fetch(`${API}/api/back`, {
        method: "POST",
        headers: { "Content-Type": "application/json" }
    })).json();

    updateUI(data);
}

function updateUI(data) {

    if (data.error) {
        questionText.textContent = data.error;
        return;
    }

    // --- GIANT LEARNING MODES ---

    if (data.is_filling) {
        questionText.textContent = data.question;
        answerButtonsContainer.innerHTML = `
            <button onclick="fillAttribute('yes')">Yes</button>
            <button onclick="fillAttribute('no')">No</button>
        `;
        return;
    }

    // --- GUESS SCREEN ---
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

    // --- REFINING ---
    if (data.is_refining) {
        questionText.textContent = data.question;
        answerButtonsContainer.innerHTML = `
            <button onclick="refineAnswer('yes')">Yes</button>
            <button onclick="refineAnswer('no')">No</button>
            ${data.can_go_back ? `<button onclick="refineBack()">⬅ Back</button>` : ""}
        `;
        return;
    }

    // --- NORMAL TREE QUESTION ---
    if (data.question) {
        questionText.textContent = data.question;
        answerButtonsContainer.innerHTML = `
            <button onclick="sendAnswer('yes')">Yes</button>
            <button onclick="sendAnswer('no')">No</button>
            ${data.can_go_back ? `<button onclick="goBack()">⬅ Back</button>` : ""}
        `;
        return;
    }
}

// ======================================================
//  GUESS RESPONSES
// ======================================================

function guessYes() {
    questionText.textContent = "Great! I guessed it!";
    answerButtonsContainer.innerHTML = `
        <button onclick="resetGame()" id="play-again-btn">Play Again</button>
    `;
}

function guessNo(isSecondGuess) {
    const t = document.querySelector(".question-text").textContent;
    window.lastWrongGuess = t.replace("My guess is…", "")
                             .replace("Is that correct?", "")
                             .replace("!", "")
                             .trim();

    if (isSecondGuess) {
        showLearningStep1();
        return;
    }

    startRefining();
}

// ======================================================
//  LEARNING (STEP 1) — Ask for correct animal
// ======================================================

function showLearningStep1() {
    questionText.textContent = "Help me learn! What animal were you thinking of?";
    answerButtonsContainer.innerHTML = `
        <form onsubmit="submitLearningStep1(event)">
            <label>Correct Animal:</label>
            <input id="correct" required>
            <button type="submit">Continue</button>
        </form>
    `;
}

async function submitLearningStep1(e) {
    e.preventDefault();

    const correct = document.getElementById("correct").value.trim();

    const data = await (await fetch(`${API}/api/learn`, {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({
            wrong_guess: window.lastWrongGuess,
            correct_answer: correct
        })
    })).json();

    if (data.status === "ask_distinguishing") {
        showDistinguishingForm(correct);
        return;
    }

    if (data.is_filling) {
    showNewAnimalConfirm(data);
    return;
    }

    if (data.status === "done" || data.status === "ok") {
        questionText.textContent = "Thanks! I updated my knowledge!";
        answerButtonsContainer.innerHTML = `<button onclick="resetGame()">Play Again</button>`;
    }
}
// SHOW NEW ANIMAL MESSAGE
function showNewAnimalConfirm(firstFillData) {
    questionText.textContent = 
        "This animal does not exist in our dataset. Would you like to add it?";

    answerButtonsContainer.innerHTML = `
        <button onclick="beginAnimalFilling('${encodeURIComponent(JSON.stringify(firstFillData))}')">
            Add Animal
        </button>
        <button onclick="resetGame()">New Game</button>
    `;
}

// ANIMAL FILLING MESSAGE

function beginAnimalFilling(dataString) {
    const data = JSON.parse(decodeURIComponent(dataString));

    questionText.textContent = 
        "Please fill out all the following information about this animal.";

    answerButtonsContainer.innerHTML = `
        <button onclick="startFilling('${encodeURIComponent(JSON.stringify(data))}')">
            Proceed
        </button>
    `;
}
// START FILLING

function startFilling(dataString) {
    const data = JSON.parse(decodeURIComponent(dataString));
    updateUI(data);   // This triggers the first attribute question
}

// ======================================================
//  LEARNING (STEP 2, EXISTING ANIMAL)
// ======================================================

function showDistinguishingForm(correct) {
    questionText.textContent = `Give me a question that distinguishes ${correct} from my previous guess.`;

    answerButtonsContainer.innerHTML = `
        <form onsubmit="submitDistinguishing(event, '${correct}')">
            <label>Distinguishing Question:</label>
            <input id="q" required>

            <label>Answer for ${correct}:</label>
            <select id="a">
                <option>Yes</option>
                <option>No</option>
            </select>

            <button type="submit">Submit</button>
        </form>
    `;
}

async function submitDistinguishing(e, correct) {
    e.preventDefault();

    const q = document.getElementById("q").value.trim();
    const a = document.getElementById("a").value;

    const data = await (await fetch(`${API}/api/learn`, {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({
            wrong_guess: window.lastWrongGuess,
            correct_answer: correct,
            new_question: q,
            new_question_answer: a
        })
    })).json();

    questionText.textContent = "Thanks! I updated my knowledge!";
    answerButtonsContainer.innerHTML = `<button onclick="resetGame()">Play Again</button>`;
}

// ======================================================
//   LEARNING (ATTRIBUTE FILLING FOR NEW ANIMALS)
// ======================================================

async function fillAttribute(answer) {
    const data = await (await fetch(`${API}/api/attribute_answer`, {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body: JSON.stringify({answer})
    })).json();

    if (data.is_filling) {
        updateUI(data);
        return;
    }

    if (data.status === "done") {
        questionText.textContent = `Great! I added ${data.animal_added} to my knowledge!`;
        answerButtonsContainer.innerHTML = `<button onclick="resetGame()">Play Again</button>`;
    }
}

// ======================================================
// RESET
// ======================================================

function resetGame() {
    gameContainer.classList.add("hidden");
    startScreen.classList.remove("hidden");
}
