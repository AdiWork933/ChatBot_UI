// Copy code function
function copyCode(button) {
    const codeBlock = button.closest('.code-block');
    const code = codeBlock.querySelector('code').textContent;
    
    navigator.clipboard.writeText(code).then(() => {
        const originalText = button.innerHTML;
        button.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>Copied!';
        button.classList.add('copied');
        
        setTimeout(() => {
            button.innerHTML = originalText;
            button.classList.remove('copied');
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy: ', err);
        button.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>Error';
        setTimeout(() => {
            button.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg>Copy';
        }, 2000);
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const chatBox = document.getElementById('chat-box');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const thinkingAnimation = document.getElementById('thinking-animation');
    const editLastBtn = document.getElementById('edit-last-btn');

    let lastUserMessageElement = null;

    const addMessage = (message, sender) => {
        const messageElement = document.createElement('div');
        messageElement.classList.add('chat-message', `${sender}-message`);

        const messageContent = document.createElement('div');
        messageContent.classList.add('message-content');

        if (sender === 'bot') {
            messageContent.innerHTML = message;
            // Show edit button now that the bot has replied
            if (lastUserMessageElement) {
                editLastBtn.style.display = 'block';
            }
        } else {
            messageContent.textContent = message;
            lastUserMessageElement = messageElement;
            // Hide edit button when a new message is sent
            editLastBtn.style.display = 'none';
        }

        messageElement.appendChild(messageContent);
        chatBox.appendChild(messageElement);
        chatBox.scrollTop = chatBox.scrollHeight;
    };

    const editLastMessage = () => {
        if (!lastUserMessageElement) return;

        const botResponseElement = lastUserMessageElement.nextElementSibling;
        const messageContent = lastUserMessageElement.querySelector('.message-content').textContent;

        // Move text to input
        userInput.value = messageContent;
        userInput.focus();

        // Remove the user message and the bot's response
        if (botResponseElement && botResponseElement.classList.contains('bot-message')) {
            botResponseElement.remove();
        }
        lastUserMessageElement.remove();
        lastUserMessageElement = null;
        editLastBtn.style.display = 'none';
    };

    editLastBtn.addEventListener('click', editLastMessage);

    const sendMessage = async () => {
        const question = userInput.value.trim();
        if (question === '') return;

        addMessage(question, 'user');
        userInput.value = '';
        thinkingAnimation.style.display = 'flex';
        chatBox.scrollTop = chatBox.scrollHeight;

        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question: question }),
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const data = await response.json();
            thinkingAnimation.style.display = 'none';
            addMessage(data.answer, 'bot');

        } catch (error) {
            console.error('Error:', error);
            thinkingAnimation.style.display = 'none';
            addMessage('Sorry, something went wrong. Please try again.', 'bot');
        }
    };

    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
});
