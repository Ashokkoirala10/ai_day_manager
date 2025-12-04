console.log("Enhanced AI Day Planner Loaded 🚀");

// ===== GLOBAL STATE & UTILITY =====
let chatbotOpen = false;
let pendingTask = null;

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// ===== CORE CHAT SYSTEM (Legacy/Main Chat Box) =====

function appendMessage(text, sender) {
    const box = document.getElementById("chatBox");
    
    // Remove welcome message if exists
    const welcome = box.querySelector('.chat-welcome');
    if (welcome && sender !== 'welcome') {
        welcome.remove();
    }
    
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
    
    // Show typing indicator
    const typingMsg = document.createElement("div");
    typingMsg.className = "message bot typing";
    typingMsg.innerHTML = '<span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>';
    typingMsg.id = "typing-indicator";
    document.getElementById("chatBox").appendChild(typingMsg);

    fetch("/chat/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
    })
    .then(res => res.json())
    .then(data => {
        // Remove typing indicator
        document.getElementById("typing-indicator")?.remove();
        appendMessage(data.response, "bot");
        
        // Check if message contains task creation intent
        checkForTaskCreation(text, data.response);
    })
    .catch(err => {
        document.getElementById("typing-indicator")?.remove();
        appendMessage("⚠️ Error: " + err, "bot");
    });
}

function checkForTaskCreation(userMsg, botResponse) {
    // If bot suggests creating a task, show quick action
    const taskKeywords = ['remind', 'task', 'todo', 'schedule', 'add'];
    if (taskKeywords.some(kw => userMsg.toLowerCase().includes(kw))) {
        // Auto-parse and offer to create task
        parseAndSuggestTask(userMsg);
    }
}

function parseAndSuggestTask(text) {
    // Simple client-side parsing for demo
    const timeMatch = text.match(/(\d{1,2}):?(\d{2})?\s*(am|pm)?/i);
    if (timeMatch) {
        showTaskQuickAdd(text, timeMatch[0]);
    }
}

function showTaskQuickAdd(taskText, timeText) {
    // Show a notification-style quick add popup
    const popup = document.createElement('div');
    popup.className = 'quick-add-popup';
    popup.innerHTML = `
        <div class="quick-add-content">
            <i class="fas fa-magic"></i>
            <p>Would you like to create this task?</p>
            <button onclick="quickAddTask('${taskText}', '${timeText}')" class="btn btn-sm btn-primary">
                <i class="fas fa-plus"></i> Add Task
            </button>
            <button onclick="this.closest('.quick-add-popup').remove()" class="btn btn-sm btn-secondary">
                Dismiss
            </button>
        </div>
    `;
    document.body.appendChild(popup);
    
    setTimeout(() => popup.remove(), 5000);
}

// ===== CHATBOT FUNCTIONS (Floating Modal) =====

function toggleChatbot() {
    const modal = document.getElementById('chatbotModal');
    const overlay = document.getElementById('chatbotOverlay');
    const badge = document.getElementById('chatBadge');
    
    chatbotOpen = !chatbotOpen;
    
    if (chatbotOpen) {
        modal.classList.add('open');
        overlay.classList.add('open');
        document.getElementById('chatbotInput').focus();
        badge.style.display = 'none';
    } else {
        modal.classList.remove('open');
        overlay.classList.remove('open');
    }
}

function sendChatMessage() {
    const input = document.getElementById('chatbotInput');
    const text = input.value.trim();
    if (!text) return;

    // Add user message to chat
    appendChatMessage(text, 'user');
    input.value = '';

    // Show typing indicator
    showTypingIndicator();

    // Send to AI
    fetch("/chat/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
    })
    .then(res => res.json())
    .then(data => {
        removeTypingIndicator();
        appendChatMessage(data.response, 'bot');
        
        // Check if this is a task creation request
        if (isTaskCreationRequest(text)) {
            parseAndShowTaskConfirmation(text);
        }
    })
    .catch(err => {
        removeTypingIndicator();
        appendChatMessage("⚠️ Error: " + err, 'bot');
    });
}

function sendQuickMessage(message) {
    document.getElementById('chatbotInput').value = message;
    sendChatMessage();
}

function appendChatMessage(text, sender) {
    const chatBody = document.getElementById('chatbotBody');
    
    // Remove welcome message if exists
    const welcome = chatBody.querySelector('.chat-welcome');
    if (welcome && sender !== 'welcome') {
        welcome.remove();
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${sender}`;
    
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.textContent = text;
    
    messageDiv.appendChild(bubble);
    chatBody.appendChild(messageDiv);
    
    // Scroll to bottom
    chatBody.scrollTop = chatBody.scrollHeight;
}

function showTypingIndicator() {
    const chatBody = document.getElementById('chatbotBody');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'chat-message bot';
    typingDiv.id = 'typingIndicator';
    typingDiv.innerHTML = `
        <div class="typing-indicator">
            <span class="typing-dot-chat"></span>
            <span class="typing-dot-chat"></span>
            <span class="typing-dot-chat"></span>
        </div>
    `;
    chatBody.appendChild(typingDiv);
    chatBody.scrollTop = chatBody.scrollHeight;
}

function removeTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) indicator.remove();
}

function isTaskCreationRequest(text) {
    const taskKeywords = [
        'add', 'create', 'remind', 'schedule', 'task', 'todo',
        'meeting', 'call', 'buy', 'workout', 'appointment'
    ];
    const lowerText = text.toLowerCase();
    return taskKeywords.some(keyword => lowerText.includes(keyword));
}

function parseAndShowTaskConfirmation(text) {
    // Parse the natural language input
    const parsed = parseNaturalLanguageTask(text);
    
    if (parsed) {
        pendingTask = parsed;
        showTaskConfirmation(parsed);
    }
}

function parseNaturalLanguageTask(text) {
    // Simple client-side parsing
    const result = {
        title: text,
        time: '09:00',
        date: new Date().toISOString().split('T')[0],
        priority: 'medium',
        category: 'other'
    };
    
    // Extract time
    const timeMatch = text.match(/(\d{1,2}):?(\d{2})?\s*(am|pm)?/i);
    if (timeMatch) {
        let hour = parseInt(timeMatch[1]);
        let minute = timeMatch[2] ? parseInt(timeMatch[2]) : 0;
        const period = timeMatch[3] ? timeMatch[3].toLowerCase() : '';
        
        if (period === 'pm' && hour !== 12) hour += 12;
        if (period === 'am' && hour === 12) hour = 0;
        
        result.time = `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`;
        
        // Remove time from title
        result.title = text.replace(timeMatch[0], '').trim();
    }
    
    // Extract date
    if (text.toLowerCase().includes('tomorrow')) {
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        result.date = tomorrow.toISOString().split('T')[0];
        result.title = result.title.replace(/tomorrow/gi, '').trim();
    } else if (text.toLowerCase().includes('today')) {
        result.title = result.title.replace(/today/gi, '').trim();
    }
    
    // Extract priority
    if (/urgent|important|asap|critical|high priority/i.test(text)) {
        result.priority = 'high';
    } else if (/low priority|optional|maybe/i.test(text)) {
        result.priority = 'low';
    }
    
    // Extract category
    if (/meeting|work|office|project/i.test(text)) {
        result.category = 'work';
    } else if (/gym|exercise|workout|health|doctor/i.test(text)) {
        result.category = 'health';
    } else if (/buy|shop|purchase|groceries/i.test(text)) {
        result.category = 'shopping';
    } else if (/study|read|learn|course/i.test(text)) {
        result.category = 'study';
    } else if (/call|family|friend|personal/i.test(text)) {
        result.category = 'personal';
    }
    
    // Clean up title
    result.title = result.title
        .replace(/\b(add|create|remind me to|schedule|task|todo)\b/gi, '')
        .replace(/\bat\b/gi, '')
        .replace(/\s+/g, ' ')
        .trim();
    
    if (!result.title) {
        result.title = 'New Task';
    } else {
        result.title = result.title.charAt(0).toUpperCase() + result.title.slice(1);
    }
    
    return result;
}

function showTaskConfirmation(task) {
    const chatBody = document.getElementById('chatbotBody');
    
    const priorityEmoji = {
        high: '🔴',
        medium: '🟡',
        low: '🟢'
    };
    
    const categoryEmoji = {
        work: '💼',
        personal: '👤',
        health: '💪',
        study: '📚',
        shopping: '🛒',
        other: '📋'
    };
    
    const confirmDiv = document.createElement('div');
    confirmDiv.className = 'task-confirmation';
    confirmDiv.innerHTML = `
        <div class="task-confirmation-header">
            <i class="fas fa-check-circle"></i>
            <span>Create this task?</span>
        </div>
        <div class="task-confirmation-body">
            <div class="task-detail">
                <span class="task-detail-label">Task:</span>
                <span class="task-detail-value">${task.title}</span>
            </div>
            <div class="task-detail">
                <span class="task-detail-label">Time:</span>
                <span class="task-detail-value">${formatTime(task.time)}</span>
            </div>
            <div class="task-detail">
                <span class="task-detail-label">Date:</span>
                <span class="task-detail-value">${formatDate(task.date)}</span>
            </div>
            <div class="task-detail">
                <span class="task-detail-label">Priority:</span>
                <span class="task-detail-value">${priorityEmoji[task.priority]} ${task.priority.charAt(0).toUpperCase() + task.priority.slice(1)}</span>
            </div>
            <div class="task-detail">
                <span class="task-detail-label">Category:</span>
                <span class="task-detail-value">${categoryEmoji[task.category]} ${task.category.charAt(0).toUpperCase() + task.category.slice(1)}</span>
            </div>
        </div>
        <div class="task-confirmation-actions">
            <button class="btn-confirm primary" onclick="confirmCreateTask()">
                <i class="fas fa-check"></i> Yes, Create
            </button>
            <button class="btn-confirm secondary" onclick="cancelCreateTask()">
                <i class="fas fa-times"></i> Cancel
            </button>
        </div>
    `;
    
    chatBody.appendChild(confirmDiv);
    chatBody.scrollTop = chatBody.scrollHeight;
}

function confirmCreateTask() {
    if (!pendingTask) return;
    
    // Create the task
    fetch("/task/add/", {
        method: "POST",
        headers: { 
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie('csrftoken')
        },
        body: JSON.stringify(pendingTask)
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            appendChatMessage('✅ Task created successfully! Refreshing your task list...', 'bot');
            
            // Remove confirmation
            document.querySelector('.task-confirmation')?.remove();
            
            // Reload page after 1 second to show new task
            setTimeout(() => {
                location.reload();
            }, 1000);
        } else {
            appendChatMessage('❌ Failed to create task. Please try again.', 'bot');
        }
        
        pendingTask = null;
    })
    .catch(err => {
        appendChatMessage('❌ Error creating task: ' + err, 'bot');
        pendingTask = null;
    });
}

function cancelCreateTask() {
    document.querySelector('.task-confirmation')?.remove();
    appendChatMessage('Task creation cancelled. What else can I help you with?', 'bot');
    pendingTask = null;
}

function formatTime(timeStr) {
    const [hours, minutes] = timeStr.split(':');
    const hour = parseInt(hours);
    const ampm = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour % 12 || 12;
    return `${displayHour}:${minutes} ${ampm}`;
}

function formatDate(dateStr) {
    const date = new Date(dateStr);
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    
    if (date.toDateString() === today.toDateString()) {
        return 'Today';
    } else if (date.toDateString() === tomorrow.toDateString()) {
        return 'Tomorrow';
    } else {
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    }
}

function startVoiceChatbot() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
        alert("Voice recognition not supported in this browser");
        return;
    }
    
    const rec = new SR();
    rec.lang = "en-US";
    
    const btn = event.target.closest('button');
    const originalIcon = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-microphone-slash"></i>';
    btn.style.background = 'var(--danger)';

    rec.onresult = e => {
        const text = e.results[0][0].transcript;
        document.getElementById('chatbotInput').value = text;
        btn.innerHTML = originalIcon;
        btn.style.background = '';
        sendChatMessage();
    };
    
    rec.onerror = rec.onend = () => {
        btn.innerHTML = originalIcon;
        btn.style.background = '';
    };

    rec.start();
}

function clearChat() {
    if (!confirm('Clear all chat messages?')) return;
    
    fetch("/chat/clear/")
    .then(res => res.json())
    .then(() => {
        const chatBody = document.getElementById('chatbotBody');
        chatBody.innerHTML = `
            <div class="chat-welcome">
                <div class="welcome-icon">
                    <i class="fas fa-hand-sparkles"></i>
                </div>
                <h4>Hello! I'm your AI assistant</h4>
                <p>I can help you:</p>
                <ul>
                    <li>📝 Create tasks naturally</li>
                    <li>🎯 Break down complex projects</li>
                    <li>💡 Give productivity tips</li>
                    <li>📊 Analyze your schedule</li>
                </ul>
                <div class="quick-actions">
                    <button class="quick-btn" onclick="sendQuickMessage('Create a task')">
                        <i class="fas fa-plus"></i> Create Task
                    </button>
                    <button class="quick-btn" onclick="sendQuickMessage('What should I do next?')">
                        <i class="fas fa-lightbulb"></i> Suggestions
                    </button>
                </div>
            </div>
        `;
    });
}

// ===== TASK MANAGEMENT (Original Functions) =====

function toggleComplete(taskId) {
    fetch(`/task/toggle/${taskId}/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" }
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            const taskElement = document.querySelector(`[data-task-id="${taskId}"]`);
            if (taskElement) {
                taskElement.classList.toggle('completed');
                updateStats();
            }
            showToast(data.is_completed ? '✅ Task completed!' : '↩️ Task reopened');
        }
    })
    .catch(err => showToast('❌ Error updating task', 'error'));
}

function deleteTask(taskId) {
    if (!confirm('Delete this task?')) return;
    
    window.location.href = `/task/delete/${taskId}/`;
}

function editTask(taskId) {
    fetch(`/task/details/${taskId}/`)
    .then(res => res.json())
    .then(data => {
        showTaskModal(data);
    });
}

function showTaskModal(task) {
    const modal = document.getElementById('taskModal') || createTaskModal();
    
    // Populate modal with task data
    document.getElementById('modalTaskTitle').value = task.title;
    document.getElementById('modalTaskDescription').value = task.description || '';
    document.getElementById('modalTaskTime').value = task.time;
    document.getElementById('modalTaskDate').value = task.date;
    document.getElementById('modalTaskPriority').value = task.priority;
    document.getElementById('modalTaskCategory').value = task.category;
    document.getElementById('modalTaskDuration').value = task.estimated_duration;
    document.getElementById('modalTaskTags').value = task.tags || '';
    document.getElementById('modalTaskId').value = task.id;
    
    // Load subtasks
    const subtasksList = document.getElementById('subtasksList');
    subtasksList.innerHTML = task.subtasks.map(st => `
        <div class="subtask-item ${st.is_completed ? 'completed' : ''}">
            <input type="checkbox" ${st.is_completed ? 'checked' : ''} 
                   onchange="toggleComplete(${st.id})">
            <span>${st.title}</span>
        </div>
    `).join('');
    
    // Show modal
    modal.style.display = 'block';
}

function createTaskModal() {
    // Create modal dynamically if it doesn't exist
    const modal = document.createElement('div');
    modal.id = 'taskModal';
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content">
            <span class="close" onclick="closeTaskModal()">&times;</span>
            <h2>Edit Task</h2>
            <form onsubmit="saveTask(event)">
                <input type="hidden" id="modalTaskId">
                
                <div class="form-group">
                    <label>Title</label>
                    <input type="text" id="modalTaskTitle" class="form-control" required>
                </div>
                
                <div class="form-group">
                    <label>Description</label>
                    <textarea id="modalTaskDescription" class="form-control" rows="3"></textarea>
                </div>
                
                <div class="row">
                    <div class="col-md-6">
                        <label>Time</label>
                        <input type="time" id="modalTaskTime" class="form-control" required>
                    </div>
                    <div class="col-md-6">
                        <label>Date</label>
                        <input type="date" id="modalTaskDate" class="form-control" required>
                    </div>
                </div>
                
                <div class="row">
                    <div class="col-md-4">
                        <label>Priority</label>
                        <select id="modalTaskPriority" class="form-select">
                            <option value="low">Low</option>
                            <option value="medium">Medium</option>
                            <option value="high">High</option>
                        </select>
                    </div>
                    <div class="col-md-4">
                        <label>Category</label>
                        <select id="modalTaskCategory" class="form-select">
                            <option value="work">Work</option>
                            <option value="personal">Personal</option>
                            <option value="health">Health</option>
                            <option value="study">Study</option>
                            <option value="shopping">Shopping</option>
                            <option value="other">Other</option>
                        </select>
                    </div>
                    <div class="col-md-4">
                        <label>Duration (min)</label>
                        <input type="number" id="modalTaskDuration" class="form-control" value="30">
                    </div>
                </div>
                
                <div class="form-group">
                    <label>Tags (comma-separated)</label>
                    <input type="text" id="modalTaskTags" class="form-control" placeholder="work, urgent, meeting">
                </div>
                
                <div class="form-group">
                    <label>Subtasks</label>
                    <div id="subtasksList"></div>
                    <button type="button" class="btn btn-sm btn-secondary" onclick="addSubtaskField()">
                        <i class="fas fa-plus"></i> Add Subtask
                    </button>
                </div>
                
                <div class="modal-actions">
                    <button type="submit" class="btn btn-primary">Save Changes</button>
                    <button type="button" class="btn btn-secondary" onclick="closeTaskModal()">Cancel</button>
                </div>
            </form>
        </div>
    `;
    document.body.appendChild(modal);
    return modal;
}

function closeTaskModal() {
    document.getElementById('taskModal').style.display = 'none';
}

function saveTask(event) {
    event.preventDefault();
    
    const taskId = document.getElementById('modalTaskId').value;
    const data = {
        title: document.getElementById('modalTaskTitle').value,
        description: document.getElementById('modalTaskDescription').value,
        time: document.getElementById('modalTaskTime').value,
        date: document.getElementById('modalTaskDate').value,
        priority: document.getElementById('modalTaskPriority').value,
        category: document.getElementById('modalTaskCategory').value,
        estimated_duration: document.getElementById('modalTaskDuration').value,
        tags: document.getElementById('modalTaskTags').value
    };
    
    fetch(`/task/update/${taskId}/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    })
    .then(res => res.json())
    .then(result => {
        if (result.success) {
            showToast('✅ Task updated successfully!');
            closeTaskModal();
            location.reload();
        }
    })
    .catch(err => showToast('❌ Error updating task', 'error'));
}

// ===== VOICE TASK INPUT (Original Functions) =====
function startListening() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
        alert("Voice not supported");
        return;
    }

    const rec = new SR();
    rec.lang = "en-US";
    
    const btn = event.target;
    btn.innerHTML = '<i class="fas fa-microphone-slash"></i>';
    btn.style.background = 'var(--danger)';

    rec.onresult = e => {
        const text = e.results[0][0].transcript;
        document.getElementById("taskInput").value = text;
        
        // Auto-parse time if mentioned
        const timeMatch = text.match(/(\d{1,2}):?(\d{2})?\s*(am|pm)?/i);
        if (timeMatch) {
            const time = parseTimeFromSpeech(timeMatch[0]);
            if (time) document.getElementById("timeInput").value = time;
        }
        
        btn.innerHTML = '<i class="fas fa-microphone"></i>';
        btn.style.background = '';
    };
    
    rec.onerror = rec.onend = () => {
        btn.innerHTML = '<i class="fas fa-microphone"></i>';
        btn.style.background = '';
    };

    rec.start();
}

function parseTimeFromSpeech(timeStr) {
    // Parse various time formats from speech
    const match = timeStr.match(/(\d{1,2}):?(\d{2})?\s*(am|pm)?/i);
    if (!match) return null;
    
    let hour = parseInt(match[1]);
    const minute = match[2] ? parseInt(match[2]) : 0;
    const period = match[3] ? match[3].toLowerCase() : '';
    
    if (period === 'pm' && hour !== 12) hour += 12;
    if (period === 'am' && hour === 12) hour = 0;
    
    return `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`;
}

// ===== TTS REMINDERS & NOTIFICATIONS (Original Functions) =====
function speak(text) {
    if (!('speechSynthesis' in window)) return;
    
    const msg = new SpeechSynthesisUtterance(text);
    msg.rate = 1;
    msg.pitch = 1;
    msg.volume = 1;
    speechSynthesis.speak(msg);
}

// Poll for due tasks
setInterval(() => {
    fetch("/scheduler/check/")
    .then(r => r.json())
    .then(data => {
        if (data.due) {
            const message = `🔔 Reminder: ${data.task}`;
            showNotification(message, data.priority);
            speak(`Reminder: ${data.task}`);
        }
    });
}, 30000); // Check every 30 seconds

function showNotification(message, priority = 'medium') {
    // Request permission first
    if (Notification.permission === 'default') {
        Notification.requestPermission();
    }
    
    if (Notification.permission === 'granted') {
        const priorityEmoji = {
            high: '🔴',
            medium: '🟡',
            low: '🟢'
        };
        
        new Notification('AI Day Planner', {
            body: `${priorityEmoji[priority] || '📋'} ${message}`,
            icon: '/static/icon.png',
            badge: '/static/badge.png'
        });
    }
    
    // Also show in-app toast
    showToast(message);
}

function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
        <span>${message}</span>
    `;
    document.body.appendChild(toast);
    
    setTimeout(() => toast.classList.add('show'), 100);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ===== SCHEDULER CONTROLS (Original Functions) =====
function startScheduler() {
    fetch("/scheduler/start/")
    .then(res => res.json())
    .then(() => showToast("✅ Scheduler started"));
}

function stopScheduler() {
    fetch("/scheduler/stop/")
    .then(res => res.json())
    .then(() => showToast("🛑 Scheduler stopped"));
}

// ===== PRODUCTIVITY STATS (Original Functions) =====
function loadProductivityStats() {
    fetch("/stats/?days=7")
    .then(res => res.json())
    .then(data => {
        updateStatsDisplay(data);
        if (window.Chart) {
            renderProductivityChart(data);
        }
    });
}

function updateStatsDisplay(data) {
    const statsContainer = document.getElementById('statsContainer');
    if (!statsContainer) return;
    
    statsContainer.innerHTML = `
        <div class="stat-summary">
            <div class="stat-item">
                <h4>${data.totals.completed}</h4>
                <p>Tasks Completed</p>
            </div>
            <div class="stat-item">
                <h4>${data.totals.avg_completion_rate}%</h4>
                <p>Completion Rate</p>
            </div>
        </div>
    `;
}

function renderProductivityChart(data) {
    const ctx = document.getElementById('productivityChart');
    if (!ctx) return;
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.daily_stats.map(d => d.date),
            datasets: [{
                label: 'Tasks Completed',
                data: data.daily_stats.map(d => d.completed),
                borderColor: 'rgb(99, 102, 241)',
                backgroundColor: 'rgba(99, 102, 241, 0.1)',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                }
            }
        }
    });
}

// ===== FILTERS & SEARCH (Original Functions) =====
function applyFilters() {
    const status = document.getElementById('filterStatus')?.value || 'all';
    const priority = document.getElementById('filterPriority')?.value || 'all';
    const category = document.getElementById('filterCategory')?.value || 'all';
    const search = document.getElementById('searchInput')?.value || '';
    
    const params = new URLSearchParams({
        status,
        priority,
        category,
        search
    });
    
    window.location.href = `/?${params.toString()}`;
}

function updateStats() {
    // Reload page to update stats (or use AJAX for smoother UX)
    location.reload();
}

// ===== LOAD & LISTENERS =====
window.addEventListener("load", () => {
    // --- Load Legacy Chat History ---
    fetch("/chat/history/")
    .then(res => res.json())
    .then(data => {
        const chatBox = document.getElementById("chatBox");
        if (chatBox) { // Check if the main chat box exists
            if (data.history.length === 0) {
                appendMessage("Hey there! 👋 How can I help you plan your day?", "bot");
            } else {
                data.history.forEach(msg => appendMessage(msg.message, msg.sender));
            }
        }
    });

    // --- Load Chatbot History ---
    fetch("/chat/history/")
    .then(res => res.json())
    .then(data => {
        const chatBody = document.getElementById('chatbotBody');
        if (chatBody) { // Check if the floating chatbot body exists
            if (data.history && data.history.length > 0) {
                chatBody.innerHTML = ''; // Clear welcome
                
                data.history.forEach(msg => {
                    appendChatMessage(msg.message, msg.sender);
                });
                
                // Show notification badge if there are messages
                if (!chatbotOpen && data.history.length > 0) {
                    const badge = document.getElementById('chatBadge');
                    if (badge) {
                        badge.style.display = 'flex';
                        badge.textContent = Math.min(data.history.length, 9);
                    }
                }
            }
        }
    });

    // Clear main chat button listener
    document.getElementById("clearChatBtn")?.addEventListener("click", () => {
        if (confirm("Clear chat history?")) {
            fetch("/chat/clear/")
            .then(res => res.json())
            .then(() => {
                const chatBox = document.getElementById("chatBox");
                if (chatBox) {
                    chatBox.innerHTML = `
                        <div class="chat-welcome">
                            <i class="fas fa-comments"></i>
                            <p>Chat cleared! How can I help you?</p>
                        </div>
                    `;
                }
            });
        }
    });
    
    // Load productivity stats
    loadProductivityStats();
    
    // Request notification permission on load
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
});

// Close chatbot on Escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && chatbotOpen) {
        toggleChatbot();
    }
});

console.log("✅ All features loaded successfully!");