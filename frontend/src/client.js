const recordButton = document.getElementById('recordButton');
const transcription = document.getElementById('transcription');
const responseText = document.getElementById('response_GPT'); 
const sendButton = document.getElementById('sendButton');
const PlayButton = document.getElementById('PlayButton');
const saveConversationButton = document.getElementById('saveConversationButton');
const newConversationButton = document.getElementById('newConversationButton');

let isRecording = false;
let recognition;
let conversation = ""; // This variable will store the entire conversation
let speech = new SpeechSynthesisUtterance();
speech.lang = 'de-DE';
const audioElement = new Audio();

function generateSessionID() {
    const sessionID = 'session_' + Date.now();
    localStorage.setItem('sessionID', sessionID);
    return sessionID;
}

function generateUserID() {
    if (!localStorage.getItem('userID')) {
        const userID = 'user_' + Date.now();
        localStorage.setItem('userID', userID);
    }
    return localStorage.getItem('userID');
}

// Call this function when the page loads or when needed
const userID = generateUserID();

recordButton.addEventListener('click', function () {
    if (isRecording) {
        stopRecording();
    } else {
        startRecording();
    }
});

function startRecording() {
    transcription.textContent = '';
    isRecording = true;
    recordButton.textContent = 'Stop Recording';

    if ('webkitSpeechRecognition' in window) {
        recognition = new webkitSpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'de-DE';

        recognition.onresult = function (event) {
            let interim_transcript = '';
            let final_transcript = '';

            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                final_transcript += event.results[i][0].transcript +"\n";
                } else {
                    interim_transcript += event.results[i][0].transcript;
                }
            }

            transcription.textContent = final_transcript + interim_transcript;
            conversation = final_transcript; // store the input as the whole convo.
        };

        recognition.onerror = function (event) {
            console.error('Recognition error', event);
        };

        recognition.onend = function () {
            isRecording = false;
            recordButton.textContent = 'Start Recording';
        };

        recognition.start();
    } else {
        alert("Your browser doesn't support speech recognition. Please use Google Chrome.");
    }
}

function stopRecording() {
    isRecording = false;
    recordButton.textContent = 'Start Recording';

    if (recognition) {
        recognition.stop();
    }
}

function sendTextToServer() {
    console.log("sendTextToServer called");
    const transcriptionText = transcription.textContent;
    console.log("Transcription text being sent:", transcriptionText);
    
    fetch('http://127.0.0.1:8000/process-text/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: transcriptionText, session_id: sessionID })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Success:', data);
        responseText.textContent = data.answer;
        // Update session ID in case it was changed by the server
        sessionID = data.session_id;
        localStorage.setItem('sessionID', sessionID);
    })
    .catch(error => console.error('Error:', error));
}

if (sendButton) {
    sendButton.addEventListener('click', sendTextToServer);
} else {
    console.log('Send button not found');
}

PlayButton.addEventListener('click', () => {
    speech.text = responseText.textContent;
    window.speechSynthesis.speak(speech);
});

// Call this function when the page loads to ensure a session ID is available
let sessionID = localStorage.getItem('sessionID');
if (!sessionID) {
    sessionID = generateSessionID();
}

function sendConversationToServer() {
    const username = document.getElementById('usernameInput').value; // Assuming you have an input field for the username
    const sessionID = document.getElementById('sessionID').value;
    const conversationText = transcription.textContent;
    const openaiResponse = responseText.textContent;

    fetch('/api/save-conversation', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({  sessionID, conversation: conversationText, openaiResponse })
    })
    .then(response => response.json())
    .then(data => console.log("Conversation saved:", data))
    .catch(error => console.error("Error saving conversation:", error));
}

newConversationButton.addEventListener('click', () => {
    sessionID = generateSessionID();
    transcription.textContent = '';
    responseText.textContent = '';
    conversation = '';
    console.log('New conversation started with session ID:', sessionID);
});