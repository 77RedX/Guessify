let loadingScreen = null;
let startScreen = null;
let gameContainer = null;
let startBtn = null;
let questionText = null;
let answerButtonsContainer = null;

const API_BASE_URL = 'http://127.0.0.1:5000';

document.addEventListener('DOMContentLoaded', () => {
    loadingScreen = document.getElementById('loading-screen');
    startScreen = document.getElementById('start-screen');
    gameContainer = document.getElementById('game-container');
    startBtn = document.getElementById('start-btn');
    questionText = document.querySelector('.question-text');
    answerButtonsContainer = document.getElementById('answer-buttons');

    window.addEventListener('load', handlePageLoad);
    
    if (startBtn) {
        startBtn.addEventListener('click', startGame);
    } else {
        console.error("Start button not found!");
    }
});

function handlePageLoad() {
    if (!loadingScreen || !startScreen) return;

    setTimeout(() => {
        loadingScreen.classList.add('fade-out');
        
        loadingScreen.addEventListener('transitionend', () => {
            loadingScreen.classList.add('hidden');
            startScreen.classList.remove('hidden'); 
        }, { once: true }); 

    }, 2000);
}

async function startGame() {
    if (!startScreen || !loadingScreen || !gameContainer) return;

    startScreen.classList.add('hidden');
    loadingScreen.classList.remove('hidden');
    loadingScreen.classList.remove('fade-out');
    loadingScreen.style.opacity = '1';

    try {
        const response = await fetch(`${API_BASE_URL}/api/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        loadingScreen.classList.add('hidden');
        gameContainer.classList.remove('hidden');
        updateUIWithQuestion(data);

    } catch (error) {
        console.error('Error starting game:', error);
        loadingScreen.classList.add('hidden');
        startScreen.classList.remove('hidden');
    }
}

async function handleAnswer(answer) {
    if (!questionText || !answerButtonsContainer) return;

    questionText.textContent = "Thinking...";
    answerButtonsContainer.innerHTML = "";

    try {
        const response = await fetch(`${API_BASE_URL}/api/answer`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ answer: answer })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        updateUIWithQuestion(data);

    } catch (error) {
        console.error('Error submitting answer:', error);
        questionText.textContent = 'Error: Could not get next question. Please try again.';
        answerButtonsContainer.innerHTML = `<button onclick="handleAnswer('${answer}')">Try Again</button>`;
    }
}

function updateUIWithQuestion(data) {
    if (data.is_guess) {
        questionText.textContent = `My guess is... ${data.character}!`;
        
        answerButtonsContainer.innerHTML = `
            <button id="play-again-btn" onclick="resetGame()">Play Again?</button>
        `;
        const playAgainBtn = document.getElementById('play-again-btn');
        if(playAgainBtn) {
            playAgainBtn.style.cssText = `
                grid-column: 1 / -1;
                font-size: 1.1rem;
                font-weight: 600;
                padding: 0.8rem 2.5rem;
                cursor: pointer;
                border: none;
                border-radius: 50px;
                background-color: #0ca8ff;
                color: white;
                box-shadow: 0 4px 15px rgba(12, 168, 255, 0.3);
                transition: all 0.2s ease;
            `;
        }
    } else {
        questionText.textContent = data.question;

        answerButtonsContainer.innerHTML = `
            <button id="yes-btn" onclick="handleAnswer('Yes')">Yes</button>
            <button id="no-btn" onclick="handleAnswer('No')">No</button>
        `;
    }
}

function resetGame() {
    if (!gameContainer || !startScreen) return;
    
    gameContainer.classList.add('hidden');
    startScreen.classList.remove('hidden');
}

