window.onload = function() {
    setTimeout(function() {
        var typingMessage = document.querySelector('.typing');
        typingMessage.innerHTML = `<span class="message-text">${defaultMessage}</span>`;
        typingMessage.classList.remove('typing');
        typingMessage.classList.add('received');

        document.querySelector('.messages').scrollTop = document.querySelector('.messages').scrollHeight;
        if (window.location.pathname.includes('FAQ.html')) {
            generateFAQButtons();
            console.log("This is the FAQ page.");
        }

    }, 2000);

};

async function sendMessage(message, merchantId = '2a1c4', isAuto = false) {
    const userInput = document.getElementById('userMessage');
    const userMessage = message || userInput.value;

    if (userMessage.trim() === "") return;

    // Display the user's message in the chat
    if (!isAuto) {
        const messageContainer = document.createElement('div');
        messageContainer.classList.add('message', 'sent');
        messageContainer.innerHTML = `${userMessage}`;
        document.querySelector('.messages').appendChild(messageContainer);
        userInput.value = "";
    }

    // Scroll to bottom
    document.querySelector('.messages').scrollTop = document.querySelector('.messages').scrollHeight;

    // Show typing indicator
    const typingMessage = document.createElement('div');
    typingMessage.classList.add('message', 'typing');
    typingMessage.innerHTML = '<span class="dot"></span><span class="dot"></span><span class="dot"></span>'; // optional animated dots
    document.querySelector('.messages').appendChild(typingMessage);

    try {
        const response = await fetch('http://127.0.0.1:5001/api/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                merchant_id: merchantId,
                query: userMessage,
            }),
        });

        const data = await response.json();
        document.querySelector('.messages').removeChild(typingMessage);

        const responseMessage = document.createElement('div');
        responseMessage.classList.add('message', 'received');

        if (response.ok) {
            responseMessage.innerHTML = `${data.response}`;
        } else {
            responseMessage.classList.add('error');
            responseMessage.innerHTML = `Error: ${data.error || "Unexpected error"}`;
        }

        document.querySelector('.messages').appendChild(responseMessage);
        document.querySelector('.messages').scrollTop = document.querySelector('.messages').scrollHeight;
    } catch (error) {
        console.error('Network error:', error);
        document.querySelector('.messages').removeChild(typingMessage);

        const errorMessage = document.createElement('div');
        errorMessage.classList.add('message', 'received', 'error');
        errorMessage.innerHTML = `Sorry, I couldn't connect to the server. Please check if it's running on port 5000.`;
        document.querySelector('.messages').appendChild(errorMessage);
        document.querySelector('.messages').scrollTop = document.querySelector('.messages').scrollHeight;
    }
}


/* FAQ page */
// Function to generate FAQ buttons
function generateFAQButtons() {
    console.log('generateFAQButtons function called');

    var buttonContainer = document.createElement('div');
    buttonContainer.classList.add('btnContainer');

    var buttons = [
        "How to know my <b><i>Inventory Status</i></b>?",
        "How to know my <b><i>Sales Trend</i></b>?",
        "How to <b><i>Boost Sales</i></b>?",
        "How to <b><i>contact Grab</i></b>?"
    ];

    buttons.forEach(function (text) {
        const button = document.createElement('button');
        button.classList.add('btn');
        button.innerHTML = text;  // Use innerHTML to render the HTML tags

        // Attach click event
        button.onclick = function () {
            console.log("Button clicked: " + text);

            // Create and append answer message to the chat
            let answerMessage = '';

            if (text.includes("contact Grab")) {
                answerMessage = formatGrabContactNumber();
            } else if (text.includes("Inventory Status")) {
                answerMessage = formatInventoryFAQ();
            } else if (text.includes("Boost Sales")) {
                answerMessage = formatBoostSalesFAQ();
            } else if (text.includes("Sales Trend")) {
                answerMessage = formatSalesTrendFAQ();
            }

            // Scroll the new answer message into view
            scrollToNewMessage();
        };

        // Append the button to a container
        buttonContainer.appendChild(button);
    });

    document.querySelector('.messages').appendChild(buttonContainer);
}

// Function to scroll to the newly added message
    function scrollToNewMessage() {
        const messagesContainer = document.querySelector('.messages');
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

// Example of the formatGrabContactNumber function that returns an answer message
    function formatGrabContactNumber() {
        const messageContent = `
        📞 Grab Contact Information<br>
        - Singapore: +65 3157 8888<br>
        - Malaysia: 1300 800 888<br>
        - Indonesia: 021 8064 1111<br>
        - Thailand: 02 100 9999<br>
        - Philippines: 02 888 8888<br>
    `;

        const message = document.createElement('div');
        message.classList.add('message', 'received');
        message.innerHTML = messageContent;  // Add the message HTML
        document.querySelector('.messages').appendChild(message);

        // Scroll the newly appended message into view
        scrollToNewMessage();
    }


    function formatInventoryFAQ() {
    // Create the message content for inventory tracking FAQ
    const messageContent = `
        To keep track of your inventory, you can press the <i>Business Insight</i>.<br>
        You are able to get other information too. For example, your best-selling product and slow-moving product.<br>
        Would you like to know your slow-moving item by now?`;

    // Display the message as a regular chat message (not AI-based)
    const message = document.createElement('div');
    message.classList.add('message', 'received');
    message.innerHTML = messageContent;  // Add the message HTML
    document.querySelector('.messages').appendChild(message);

    // Create and append the button directly to the chat container
    const button = document.createElement('button');
    button.classList.add('btn');  // Keep this class for your styling if needed
    button.innerText = "Yes";

    button.onclick = function () {
        // Action when the button is clicked (for example, show inventory data)
        displayInventoryStatus();
        scrollToNewMessage();
    };

    // Append the button directly to the messages container without the grey background
    document.querySelector('.messages').appendChild(button);
}

function formatSalesTrendFAQ() {
    // Create the message content for inventory tracking FAQ
    const messageContent = `
        To know your sales trend, you can press the <i>Business Insight</i>.<br>
        You are able to get other information too. For example, your best-selling product and slow-moving product.<br>
        <b><i> Would you like to know your sales trend by now?</i></b>`;

    const message = document.createElement('div');
    message.classList.add('message', 'received');
    message.innerHTML = messageContent;  // Add the message HTML
    document.querySelector('.messages').appendChild(message);

    const button = document.createElement('button');
    button.classList.add('btn');
    button.innerText = "Yes";

    button.onclick = function () {
        displaySalesTrend();
        scrollToNewMessage();
    };

    document.querySelector('.messages').appendChild(button);
}


function formatBoostSalesFAQ() {
    const defaultBoostSales = 'How to boost sales ?';
    sendMessage(defaultBoostSales);

    const messageContent = `
        To get personalised advices,you can press the <br><i>Tailored Advice</i><br> to get your personalised advices on how to boost your sales.`;

    const message = document.createElement('div');
    message.classList.add('message', 'received');
    message.innerHTML = messageContent;  // Add the message HTML
    document.querySelector('.messages').appendChild(message);

    const button = document.createElement('button');
    button.classList.add('btn');  // Keep this class for your styling if needed
    button.innerText = "Yes";

    button.onclick = function () {
        // Action when the button is clicked (for example, show inventory data)
        displaySalesTrend();
        scrollToNewMessage();
    };

    document.querySelector('.messages').appendChild(button);
}


/* Business Insight page */
/* Generate buttons for Business Insight */
function generateBusinessInsightbuttons(){
    var buttonContainer = document.createElement('div');
    buttonContainer.classList.add('btnContainer');

    var buttons = [
        "Sales Trend",
        "Sales Opportunity",
        "Inventory Status",
        "Operational bottleneck"
    ];

    buttons.forEach(function (text) {
        const button = document.createElement('button');
        button.classList.add('btn');
        button.innerHTML = text;  // Use innerHTML to render the HTML tags

        // Attach click event
        button.onclick = function () {
            console.log("Button clicked: " + text);

            let answerMessage = '';

            if (text.includes("Sales Trend")) {
                answerMessage = displaySalesTrend();
            } else if (text.includes("Sales Opportunity")) {
                answerMessage = displaySalesTrend();
            } else if (text.includes("Inventory Status")) {
                answerMessage = displayInventoryStatus();
            } else if (text.includes("Operational Bottleneck")) {
                answerMessage = displaySalesTrend();
            }

            scrollToNewMessage();
        };

        // Append the button to a container
        buttonContainer.appendChild(button);
    });

    document.querySelector('.messages').appendChild(buttonContainer);
}



function displayInventoryStatus() {
    scrollToNewMessage();
    const inventoryMessage = "Here is your store inventory summary :";

    const message = document.createElement('div');
    message.classList.add('message', 'received');
    message.innerText = inventoryMessage;  // Add the inventory summary message
    document.querySelector('.messages').appendChild(message);

}

function displaySalesTrend(){
    scrollToNewMessage();
    const inventoryMessage = "Here is your store sales trend summary :";

    const message = document.createElement('div');
    message.classList.add('message', 'received');
    message.innerText = inventoryMessage;  // Add the inventory summary message
    document.querySelector('.messages').appendChild(message);

    // Fetch sales trend from backend
    fetch('http://127.0.0.1:5001/sales_trend', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        }
    })
        .then(response => response.json())
        .then(data => {
            // Display the response data in the chat (as a message)
            let responseMessage = document.createElement('div');
            responseMessage.classList.add('message', 'received');
            responseMessage.innerHTML = `<span class="message-text">${data.reply}</span>`;
            document.querySelector('.messages').appendChild(responseMessage);
            scrollToNewMessage();
        })
        .catch(error => {
            console.error('Error:', error);
            // Optionally handle the error by displaying a message
        });
}



function displaySalesOpportunity(){
    scrollToNewMessage();
    const inventoryMessage = "Here is your store sales opportunity :";

    const message = document.createElement('div');
    message.classList.add('message', 'received');
    message.innerText = inventoryMessage;  // Add the inventory summary message
    document.querySelector('.messages').appendChild(message);
}


function displayOperationalBottleneck(){
    scrollToNewMessage();
    const inventoryMessage = "Here is your store operational bottleneck :";

    const message = document.createElement('div');
    message.classList.add('message', 'received');
    message.innerText = inventoryMessage;  // Add the inventory summary message
    document.querySelector('.messages').appendChild(message);
}


/* Tailored Advice page */

/* for backend */