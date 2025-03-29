document.addEventListener('DOMContentLoaded', () => {
    // Connect to WebSocket server
    const socket = io();
    
    // Get DOM elements
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const modelSelect = document.getElementById('model-select');
    const statusIndicator = document.getElementById('status-indicator');
    const statusText = document.getElementById('status-text');
    
    let isProcessing = false;
    let currentMessageContainer = null;
    
    // Connect to socket.io
    socket.on('connect', () => {
        console.log('Connected to server');
        setStatus('idle');
    });
    
    // Listen for agent responses
    socket.on('agent response', (data) => {
        console.log('Received response:', data);
        
        switch (data.type) {
            case 'thinking':
                setStatus('thinking');
                addAgentMessage(data.message);
                break;
                
            case 'progress':
                setStatus('working');
                appendProgressToCurrentMessage(data.message);
                break;
                
            case 'result':
                setStatus('idle');
                appendResultToCurrentMessage(data.message);
                isProcessing = false;
                enableInput();
                break;
                
            case 'error':
                setStatus('error');
                appendErrorToCurrentMessage(data.message);
                isProcessing = false;
                enableInput();
                break;
                
            case 'system':
                addSystemMessage(data.message);
                break;
        }
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    });
    
    // Handle send button click
    sendButton.addEventListener('click', sendMessage);
    
    // Handle enter key in textarea
    userInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            sendMessage();
        }
    });
    
    // Handle model selection change
    modelSelect.addEventListener('change', () => {
        const selectedModel = modelSelect.value;
        socket.emit('model change', selectedModel);
    });
    
    // Function to send a message
    function sendMessage() {
        const message = userInput.value.trim();
        
        if (message && !isProcessing) {
            isProcessing = true;
            
            // Add user message to chat
            addUserMessage(message);
            
            // Send message to server
            socket.emit('chat message', message);
            
            // Clear input field
            userInput.value = '';
            
            // Disable input while processing
            disableInput();
            
            // Set status to thinking
            setStatus('thinking');
        }
    }
    
    // Function to add a user message to the chat
    function addUserMessage(message) {
        const messageEl = document.createElement('div');
        messageEl.className = 'message user';
        messageEl.innerHTML = `
            <div class="message-content">
                <p>${escapeHtml(message)}</p>
            </div>
        `;
        chatMessages.appendChild(messageEl);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Function to add an agent message to the chat
    function addAgentMessage(message) {
        currentMessageContainer = document.createElement('div');
        currentMessageContainer.className = 'message agent';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        const messageText = document.createElement('p');
        messageText.textContent = message;
        
        messageContent.appendChild(messageText);
        currentMessageContainer.appendChild(messageContent);
        chatMessages.appendChild(currentMessageContainer);
    }
    
    // Function to add a system message to the chat
    function addSystemMessage(message) {
        const messageEl = document.createElement('div');
        messageEl.className = 'message system';
        messageEl.innerHTML = `
            <div class="message-content">
                <p>${escapeHtml(message)}</p>
            </div>
        `;
        chatMessages.appendChild(messageEl);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Function to append progress to the current message
    function appendProgressToCurrentMessage(progress) {
        if (!currentMessageContainer) return;
        
        const messageContent = currentMessageContainer.querySelector('.message-content');
        
        // Check if a progress container already exists
        let progressContainer = messageContent.querySelector('.progress-container');
        
        if (!progressContainer) {
            progressContainer = document.createElement('div');
            progressContainer.className = 'progress-container';
            messageContent.appendChild(progressContainer);
        }
        
        const progressItem = document.createElement('div');
        progressItem.className = 'progress-item';
        progressItem.textContent = progress;
        progressContainer.appendChild(progressItem);
        
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Function to append the final result to the current message
    function appendResultToCurrentMessage(result) {
        if (!currentMessageContainer) return;
        
        const messageContent = currentMessageContainer.querySelector('.message-content');
        
        // Remove the thinking text if it exists
        const thinkingText = messageContent.querySelector('p');
        if (thinkingText && thinkingText.textContent === 'Thinking...') {
            thinkingText.remove();
        }
        
        // Add the result
        const resultText = document.createElement('p');
        resultText.textContent = result;
        
        // Insert the result at the beginning of the message content
        messageContent.insertBefore(resultText, messageContent.firstChild);
        
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Function to append an error to the current message
    function appendErrorToCurrentMessage(error) {
        if (!currentMessageContainer) return;
        
        const messageContent = currentMessageContainer.querySelector('.message-content');
        
        // Add the error
        const errorText = document.createElement('p');
        errorText.textContent = `Error: ${error}`;
        errorText.style.color = '#ea4335';
        
        messageContent.appendChild(errorText);
        
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Function to set the status
    function setStatus(status) {
        statusIndicator.className = `status-indicator ${status}`;
        
        switch (status) {
            case 'idle':
                statusText.textContent = 'Idle';
                break;
            case 'thinking':
                statusText.textContent = 'Thinking...';
                break;
            case 'working':
                statusText.textContent = 'Working...';
                break;
            case 'error':
                statusText.textContent = 'Error';
                break;
        }
    }
    
    // Function to disable input during processing
    function disableInput() {
        userInput.disabled = true;
        sendButton.disabled = true;
    }
    
    // Function to enable input after processing
    function enableInput() {
        userInput.disabled = false;
        sendButton.disabled = false;
        userInput.focus();
    }
    
    // Helper function to escape HTML
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}); 
