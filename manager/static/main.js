console.log("JS Loaded");

// --- Chat system ---
function appendMessage(text, sender) {
    const box = document.getElementById("chatBox");
    const msg = document.createElement("div");
    msg.className = "message " + sender;
    msg.innerText = text;
    box.appendChild(msg);
    box.scrollTop = box.scrollHeight;
}

function sendMessage() {
    const input = document.getElementById("userInput");
    const text = input.value.trim();
    if (!text) return;

    appendMessage(text, "user");
    input.value = "";

    fetch("/chat/", {   // FIXED
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    })
      .then(res => res.json())        // FIXED
      .then(data => appendMessage(data.response, "bot")) // FIXED
      .catch(err => appendMessage("⚠️ Error: " + err, "bot"));
}


// Voice chat
function startVoiceChat() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return alert("Voice not supported");
    const rec = new SR();
    rec.lang = "en-US";

    rec.onresult = e => {
        const text = e.results[0][0].transcript;
        document.getElementById("userInput").value = text;
        sendMessage();
    };

    rec.start();
}

// ---- Voice Reminder (TTS) ----
function speak(text) {
    const msg = new SpeechSynthesisUtterance(text);
    msg.rate = 1;
    msg.pitch = 1;
    speechSynthesis.speak(msg);
}

// Poll backend every 20 seconds
setInterval(() => {
    fetch("/scheduler/check/")
    .then(r => r.json())
    .then(data => {
        if (data.due) {
            alert("🔔 Reminder: " + data.task);
            speak("Reminder: " + data.task);
        }
    });
}, 20000);


// --- Routine voice input ---
function parseTime(text) {
  // Match 6 4 pm or 6:04 pm
  const match = text.match(/(\d{1,2})[:\s](\d{1,2})\s?(am|pm)/i);
  if (!match) return null;

  let hour = parseInt(match[1]);
  let minute = parseInt(match[2]);
  const period = match[3].toLowerCase();

  if (period === "pm" && hour !== 12) hour += 12;
  if (period === "am" && hour === 12) hour = 0;

  return hour.toString().padStart(2, "0") + ":" + minute.toString().padStart(2, "0");
}


function startListening() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return alert("Voice not supported");

    const rec = new SR();
    rec.lang = "en-US";

    rec.onresult = e => {
        const text = e.results[0][0].transcript;

        const time = parseTime(text);
        if (time) document.getElementById("timeInput").value = time;

        document.getElementById("taskInput").value = text;
        document.getElementById("routineForm").submit();
    };

    rec.start();
}

// start/stop scheduler
function startScheduler() {
    fetch("/scheduler/start/")
        .then(res => res.json())
        .then(() => alert("Scheduler STARTED"));
}

function stopScheduler() {
    fetch("/scheduler/stop/")
        .then(res => res.json())
        .then(() => alert("Scheduler STOPPED"));
}

