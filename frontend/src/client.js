const recordButton = document.getElementById('recordButton');
const transcription = document.getElementById('transcription');
const responseText = document.getElementById('response_GPT'); // Element to display the full response text
const sendButton = document.getElementById('sendButton');
const PlayButton = document.getElementById('PlayButton');
const saveConversationButton = document.getElementById('saveConversationButton');

let isRecording = false;
let recognition;
let conversation = ""; // This variable will store the entire conversation
let speech = new SpeechSynthesisUtterance();
const audioElement = new Audio();

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
        recognition.lang = 'en-US';

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
    const transcriptionText = transcription.textContent;
    const url = 'http://127.0.0.1:8000/process-text/';
    let sessionId = sessionStorage.getItem('session_id');  // Retrieve session_id from storage

    console.log("Transcription text being sent:", transcriptionText);
    
    // Corrected from inputText to transcriptionText based on your context
    fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: transcriptionText, session_id: sessionId })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Success:', data);
        responseText.textContent = data.answer;
    })
    .catch(error => console.error('Error:', error));
}

if (sendButton) {
    sendButton.addEventListener('click', sendTextToServer);
} else {
    console.log('Send button not found');
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


PlayButton.addEventListener('click', () => {
    speech.text = responseText.textContent;
    window.speechSynthesis.speak(speech);
});


function sendConversationToServer() {
    const username = document.getElementById('usernameInput').value; // Assuming you have an input field for the username
    const conversationText = transcription.textContent;
    const openaiResponse = responseText.textContent;

    fetch('/api/save-conversation', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({  username, conversation: conversationText, openaiResponse })
    })
    .then(response => response.json())
    .then(data => console.log("Conversation saved:", data))
    .catch(error => console.error("Error saving conversation:", error));
}