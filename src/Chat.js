window.onload = function() {
    // Show the typing animation for 2 seconds and then load the message
    setTimeout(function() {
        // Remove typing animation and add a real message
        var typingMessage = document.querySelector('.typing');
        typingMessage.innerHTML = `<span class="message-text">${defaultMessage}</span>`;
        typingMessage.classList.remove('typing');
        typingMessage.classList.add('received');

        // Scroll to the bottom of the chatbox
        document.querySelector('.messages').scrollTop = document.querySelector('.messages').scrollHeight;
    }, 2000); // Show typing animation for 2 seconds
};

function sendMessage(message, isAuto = false) {

    var userMessage = message || document.getElementById('userMessage').value;
    if (userMessage.trim() !== "") {
        if (!isAuto) {
            var messageContainer = document.createElement('div');
            messageContainer.classList.add('message', 'sent');
            messageContainer.innerHTML = `<span class="message-text">${userMessage}</span>`;
            document.querySelector('.messages').appendChild(messageContainer);
            document.getElementById('userMessage').value = "";
        }

        document.querySelector('.messages').scrollTop = document.querySelector('.messages').scrollHeight;

        var typingMessage = document.createElement('div');
        typingMessage.classList.add('message', 'typing');
        typingMessage.innerHTML = '<span class="typing-indicator"></span>';
        document.querySelector('.messages').appendChild(typingMessage);

        fetch("http://127.0.0.1:5000/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: userMessage })
        })
            .then(response => response.json())
            .then(data => {
                document.querySelector('.messages').removeChild(typingMessage);

                var responseMessage = document.createElement('div');
                responseMessage.classList.add('message', 'received');
                responseMessage.innerHTML = `<span class="message-text">${data.reply}</span>`;
                document.querySelector('.messages').appendChild(responseMessage);

                document.querySelector('.messages').scrollTop = document.querySelector('.messages').scrollHeight;
            })
            .catch(error => {
                console.error("Error:", error);
                document.querySelector('.messages').removeChild(typingMessage);

                var errorMessage = document.createElement('div');
                errorMessage.classList.add('message', 'received', 'error');
                errorMessage.innerHTML = `<span class="message-text">Sorry, I couldn't process your request. Please try again later.</span>`;
                document.querySelector('.messages').appendChild(errorMessage);
                document.querySelector('.messages').scrollTop = document.querySelector('.messages').scrollHeight;
            });
    }
}


// Add event listener for pressing Enter in the input field
document.getElementById('userMessage').addEventListener('keypress', function(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
});


function generateFAQButtons() {
    if (window.location.pathname === "/FAQ.html") {
        var buttonContainer = document.createElement('div');
        buttonContainer.classList.add('button-container');
        console.log('Button container created.');

        // Array of FAQ questions to be displayed as buttons
        var buttons = [
            "How to keep track on inventory?",
            "How to know my best selling item?",
            "How to know my sales trend?",
            "How to contact Grab?"
        ];

        // Create a button for each FAQ item
        buttons.forEach(function(buttonText) {
            var button = document.createElement('button');
            button.classList.add('btn');
            button.innerText = buttonText;
            button.onclick = function() {
                sendMessage(`You clicked on: ${buttonText}`);
            };
            buttonContainer.appendChild(button);
        });

        // Append the button container to the chat container
        document.querySelector('.messages').appendChild(buttonContainer);
    }
}