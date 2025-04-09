// Simulate the chat loading
window.onload = function() {
    // Show the typing animation for 2 seconds and then load the message
    setTimeout(function() {
        // Remove typing animation and add a real message
        var typingMessage = document.querySelector('.typing');
        typingMessage.innerHTML = '<span class="message-text">Thanks for your message!</span>';

        // Scroll to the bottom of the chatbox
        document.querySelector('.messages').scrollTop = document.querySelector('.messages').scrollHeight;
    }, 2000); // Show typing animation for 2 seconds
};

function sendMessage() {
    var userMessage = document.getElementById('userMessage').value;
    if (userMessage.trim() !== "") {
        // Add sent message to chatbox
        var messageContainer = document.createElement('div');
        messageContainer.classList.add('message', 'sent');
        messageContainer.innerHTML = `<span class="message-text">${userMessage}</span>`;
        document.querySelector('.messages').appendChild(messageContainer);

        // Clear the input field
        document.getElementById('userMessage').value = "";

        // Scroll to the bottom of the chatbox
        document.querySelector('.messages').scrollTop = document.querySelector('.messages').scrollHeight;

        // Simulate "typing" animation after a short delay
        setTimeout(function() {
            var typingMessage = document.createElement('div');
            typingMessage.classList.add('message', 'typing');
            typingMessage.innerHTML = '<span class="typing-indicator"></span>';
            document.querySelector('.messages').appendChild(typingMessage);

            // Remove typing indicator after 2 seconds (simulate response)
            setTimeout(function() {
                document.querySelector('.messages').removeChild(typingMessage);

                // Simulate a response message
                var responseMessage = document.createElement('div');
                responseMessage.classList.add('message', 'received');
                responseMessage.innerHTML = `<span class="message-text">Thanks for your message!</span>`;
                document.querySelector('.messages').appendChild(responseMessage);

                // Scroll to the bottom of the chatbox
                document.querySelector('.messages').scrollTop = document.querySelector('.messages').scrollHeight;
            }, 2000); // Typing indicator stays for 2 seconds
        }, 1000); // Simulate delay before typing animation
    }
}
