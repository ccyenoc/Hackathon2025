window.onload = function () {
            setTimeout(function () {
                var typingMessage = document.querySelector('.typing');
                if (typingMessage) {
                    typingMessage.innerHTML = `<span class="message-text">${defaultMessage}</span>`; // Ensure `defaultMessage` is defined
                    typingMessage.classList.remove('typing');
                    typingMessage.classList.add('received');

                    // Scroll the messages container to the bottom
                    const messagesContainer = document.querySelector('.messages');
                    if (messagesContainer) {
                        messagesContainer.scrollTop = messagesContainer.scrollHeight;
                    }

                    // Check if we are on the FAQ page
                    if (window.location.pathname.includes('FAQ.html')) {
                        generateFAQButtons(); // Make sure this function is defined
                        console.log("This is the FAQ page.");
                    }
                    else if(window.location.pathname.includes('BusinessInsight.html')){
                        generateBusinessInsightbuttons();
                        console.log("This is Business Insight page.");
                    }
                    else if(window.location.pathname.includes('TailoredAdvice.html')){
                        generateGetAdviceBtn();
                        console.log("This is Business Insight page.");
                    }
                }
            }, 2000);

    const userInputField = document.getElementById('userMessage');  // Assuming your input field has this id
    if (userInputField) {
        userInputField.addEventListener('keypress', function(event) {
            if (event.key === 'Enter') {
                event.preventDefault();  // Prevent default Enter key behavior (e.g., form submission)
                sendMessage();  // Call the sendMessage function
            }
        });
    }

};

/* format  the message given */
function formatGenericMessage(rawMessage) {
    console.log("Message formatted.")
    return rawMessage
        // Format bold **text**
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')

        // Format emojis and labels with spacing
        .replace(/(📊|🔥|🔍|💡|✅)/g, '<br><br>$1')

        // Format numbered lists (e.g., 1. Keyword - views)
        .replace(/(\d+\.\s[\w\s\-]+-\s\d+\sviews)/g, '<br>$1')

        // Format opportunities and recommendations as bullet points
        .replace(/(\d+\.\s)(.*?)(?=\d+\.|$)/gs, (match, num, content) => {
            return `<br>${num}<span>${content.trim()}</span>`;
        })

        // Add line breaks for newlines
        .replace(/\n{2,}/g, '<br><br>')
        .replace(/\n/g, '<br>');
}

function confirmLogin() {
    const merchantInput = document.getElementById("merchant-id");
    const inputMerchantId = merchantInput ? merchantInput.value.trim() : '';
    console.log("Input Merchant ID:", inputMerchantId);

    if (inputMerchantId) {
        localStorage.setItem('merchantID', inputMerchantId);

        // Send the merchant ID to the backend
        sendMerchantIdToBackend(inputMerchantId);

        // Send a message confirming the login, and pass inputMerchantId
        sendMessage("Confirming your login...", inputMerchantId, true);

        // Redirect after 2 seconds (or adjust timing as needed)
        setTimeout(function () {
            window.location.href = 'General.html';
        }, 2000);
    } else {
        console.log("Merchant ID is empty!");
    }
}
// Function to send merchant ID to the Python backend
function sendMerchantIdToBackend(merchantId) {
    fetch('http://127.0.0.1:5001/api/save_merchant_id', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            merchant_id: merchantId ,
        })
    })
        .then(response => response.json())
        .then(data => {
            console.log('Merchant ID saved:', data);
        })
        .catch(error => {
            console.error('Error saving merchant ID:', error);
        });
}

async function sendMessage(message, merchantId = null, isAuto = false) {
    const userInput = document.getElementById('userMessage');
    const userMessage = message || userInput.value;

    if (userMessage.trim() === "") return;

    if (!merchantId) {
        merchantId = localStorage.getItem('merchantID');
        console.log("Retrieved merchantId from localStorage:", merchantId);
    }

    // If still no merchantId, log error and return
    if (!merchantId) {
        console.error("No merchant ID available. Please log in first.");
        const errorMessage = document.createElement('div');
        errorMessage.classList.add('message', 'received', 'error');
        errorMessage.innerHTML = `Error: Please log in first to establish your merchant ID.`;
        document.querySelector('.messages').appendChild(errorMessage);
        return;
    }

    // Display the user's message in the chat
    if (!isAuto) {
        const messageContainer = document.createElement('div');
        messageContainer.classList.add('message', 'sent');
        messageContainer.innerHTML = `${userMessage}`;
        document.querySelector('.messages').appendChild(messageContainer);
        userInput.value = "";
    }

    document.querySelector('.messages').scrollTop = document.querySelector('.messages').scrollHeight;

    // Show typing indicator
    const typingMessage = document.createElement('div');
    typingMessage.classList.add('message', 'typing');
    typingMessage.innerHTML = '<span class="dot"></span><span class="dot"></span><span class="dot"></span>';
    document.querySelector('.messages').appendChild(typingMessage);

    try {
        console.log("merchantId:", merchantId);
        console.log("userMessage:", userMessage);
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

        // Remove typing message if it's still in the DOM
        if (document.querySelector('.messages').contains(typingMessage)) {
            document.querySelector('.messages').removeChild(typingMessage);
        }

        const responseMessage = document.createElement('div');
        responseMessage.classList.add('message', 'received', 'backend-message'); // Added 'backend-message' class

        if (response.ok) {
            // Format the response before displaying it
            const formattedResponse = formatGenericMessage(data.response);
            responseMessage.innerHTML = formattedResponse;
        } else {
            responseMessage.classList.add('error');
            responseMessage.innerHTML = `Error: ${data.error || "Unexpected error"}`;
        }

        document.querySelector('.messages').appendChild(responseMessage);
        document.querySelector('.messages').scrollTop = document.querySelector('.messages').scrollHeight;

    } catch (error) {
        console.error('Network error:', error);

        // Remove typing message if it's still in the DOM
        if (document.querySelector('.messages').contains(typingMessage)) {
            document.querySelector('.messages').removeChild(typingMessage);
        }

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
        displaySalesOpportunity();
        scrollToNewMessage();
    };

    document.querySelector('.messages').appendChild(button);
}


/* Business Insight page */
/* Generate buttons for Business Insight */
function generateBusinessInsightbuttons() {
    // Create the button container and add a unique ID to the container
    var buttonContainer = document.createElement('div');
    buttonContainer.classList.add('btnContainer');
    buttonContainer.id = 'business-insight-buttons';  // Assigning an ID to the container

    // Array of button texts
    var buttons = [
        "Sales Trend",
        "Sales Opportunity",
        "Inventory Status",
        "Operational Bottleneck"
    ];

    // Loop over the buttons array to create each button
    buttons.forEach(function (text, index) {
        const button = document.createElement('button');
        button.classList.add('btn');
        button.innerHTML = text;  // Set the button's inner HTML (text)

        // Set the ID for each button using text (replace spaces with hyphens and convert to lowercase)
        button.id = 'button-' + text.replace(/\s+/g, '-').toLowerCase();

        // Handle the click event based on button text
        button.onclick = function () {
            console.log("Button clicked: " + text);

            // Check the button text to decide which function to call
            if (text.includes("Sales Trend")) {
                displaySalesTrend();
            } else if (text.includes("Sales Opportunity")) {
                displaySalesOpportunity();
            } else if (text.includes("Inventory Status")) {
                console.log("Buttons contain WORD Inventory Status.");
                displayInventoryStatus();
            } else if (text.toLowerCase().includes("operational bottleneck")) {
                displayOperationalBottleneck();
            }

            // Optionally scroll to the new message
            scrollToNewMessage();
        };

        // Append the button to the container
        buttonContainer.appendChild(button);
    });

    // Append the button container to the messages container
    document.querySelector('.messages').appendChild(buttonContainer);
}


document.addEventListener("DOMContentLoaded", () => {
    const buttonContainer = document.querySelector('.button-container');

    if (buttonContainer) {
        buttonContainer.addEventListener('click', (event) => {
            const target = event.target;

            if (target.tagName === 'BUTTON') {
                const messageText = target.textContent.trim();
                const dataAction = target.getAttribute('data-action');

                // Display user's message
                const userMessage = document.createElement('div');
                userMessage.classList.add('message', 'sent');
                userMessage.innerHTML = `<span class="message-text">${messageText}</span>`;
                document.querySelector('.messages').appendChild(userMessage);
                scrollToNewMessage();

                // Debug log
                console.log("Button clicked: " + messageText);

                // Display simulated AI response
                const simulatedMessage = `📊 Analysis based on 527 relevant keywords for your store...`;
                const formatted = formatGenericMessage(simulatedMessage);

                const responseMessage = document.createElement('div');
                responseMessage.classList.add('message', 'received');
                responseMessage.innerHTML = formatted;
                document.querySelector('.messages').appendChild(responseMessage);
                document.querySelector('.messages').scrollTop = document.querySelector('.messages').scrollHeight;

                // Handle button action
                if (dataAction) {
                    switch (dataAction) {
                        case 'sales_trend':
                            displaySalesTrend();
                            break;
                        case 'sales_opportunity':
                            displaySalesOpportunity();
                            break;
                        case 'inventory_status':
                            displayInventoryStatus();
                            break;
                        case 'operational_bottleneck':
                            displayOperationalBottleneck();
                            break;
                        default:
                            console.warn(`Unrecognized action: ${dataAction}`);
                            sendMessage(messageText);
                            break;
                    }
                } else {
                    sendMessage(messageText);
                }
            }
        });
    }
});




function displayInventoryStatus() {
    console.log('displayInventoryStatus() function executed')
    scrollToNewMessage();


    let merchantId = localStorage.getItem('merchantID');
    console.log('MerchantId : ', merchantId);
    if (!merchantId) {
        console.error('Merchant ID is not available');
        return;
    }

    const inventoryMessage = document.createElement('div');
    inventoryMessage.classList.add('message', 'received');
    inventoryMessage.style.backgroundColor = '#c1e2be'; // Light green background
    inventoryMessage.innerHTML = "Here is your store inventory status:";
    document.querySelector('.messages').appendChild(inventoryMessage);

    const typingMessage = document.createElement('div');
    typingMessage.classList.add('message', 'typing');
    typingMessage.innerHTML = '<span class="dot"></span><span class="dot"></span><span class="dot"></span>';
    document.querySelector('.messages').appendChild(typingMessage);

    fetch('http://127.0.0.1:5001/inventory_status', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'merchant-id': merchantId
        }
    })
        .then(response => response.json())
        .then(data => {
            document.querySelector('.messages').removeChild(typingMessage);

            const responseMessage = document.createElement('div');
            responseMessage.classList.add('message', 'received', 'backend-message'); // Add 'backend-message' here

            if (data.reply) {
                responseMessage.innerHTML = `<span class="message-text">${data.reply}</span>`;
            } else if (data.error) {
                responseMessage.innerHTML = `<span class="message-text">⚠️ ${data.error}</span>`;
            } else {
                responseMessage.innerHTML = `<span class="message-text">Unexpected error occurred.</span>`;
            }

            document.querySelector('.messages').appendChild(responseMessage);
            scrollToNewMessage();
        })
        .catch(error => {
            console.error('Error fetching sales trend:', error);
            document.querySelector('.messages').removeChild(typingMessage);

            const errorMessage = document.createElement('div');
            errorMessage.classList.add('message', 'received', 'error');
            errorMessage.innerText = "Sorry, I couldn't fetch the sales trend chart.";
            document.querySelector('.messages').appendChild(errorMessage);
            scrollToNewMessage();
        });

}

function displaySalesTrend() {
    scrollToNewMessage();
    console.log("displaySalesTrend() executed")

    let merchantId = localStorage.getItem('merchantID');
    console.log('MerchantId : ', merchantId);
    if (!merchantId) {
        console.error('Merchant ID is not available');
        return;
    }

    const inventoryMessage = document.createElement('div');
    inventoryMessage.classList.add('message', 'received');
    inventoryMessage.style.backgroundColor = '#c1e2be'; // Light green background
    inventoryMessage.innerHTML = "Here is your store sales trend summary:";
    document.querySelector('.messages').appendChild(inventoryMessage);

    const typingMessage = document.createElement('div');
    typingMessage.classList.add('message', 'typing');
    typingMessage.innerHTML = '<span class="dot"></span><span class="dot"></span><span class="dot"></span>';
    document.querySelector('.messages').appendChild(typingMessage);

    fetch('http://127.0.0.1:5001/sales_trend', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'merchant-id': merchantId
        }
    })
        .then(response => response.json())
        .then(data => {
            document.querySelector('.messages').removeChild(typingMessage);

            const responseMessage = document.createElement('div');
            responseMessage.classList.add('message', 'received', 'backend-message'); // Add 'backend-message' here

            responseMessage.innerHTML = `
                <span class="message-text">${data.reply}</span>
            `;
            document.querySelector('.messages').appendChild(responseMessage);
            scrollToNewMessage();
        })
        .catch(error => {
            console.error('Error fetching sales trend:', error);
            document.querySelector('.messages').removeChild(typingMessage);

            const errorMessage = document.createElement('div');
            errorMessage.classList.add('message', 'received', 'error');
            errorMessage.innerText = "Sorry, I couldn't fetch the sales trend.";
            document.querySelector('.messages').appendChild(errorMessage);
            scrollToNewMessage();
        });
}

function displaySalesOpportunity(){
    scrollToNewMessage();
    console.log("displaySalesOpportunity() executed")
    let merchantId = localStorage.getItem('merchantID');
    console.log('MerchantId : ', merchantId);
    if (!merchantId) {
        console.error('Merchant ID is not available');
        return;
    }

    const inventoryMessage = document.createElement('div');
    inventoryMessage.classList.add('message', 'received');
    inventoryMessage.style.backgroundColor = '#c1e2be'; // Light green background
    inventoryMessage.innerHTML = "Here is your store Sales Opportunity:";
    document.querySelector('.messages').appendChild(inventoryMessage);

    // Optional: Add a temporary typing indicator
    const typingMessage = document.createElement('div');
    typingMessage.classList.add('message', 'typing');
    typingMessage.innerHTML = '<span class="dot"></span><span class="dot"></span><span class="dot"></span>';
    document.querySelector('.messages').appendChild(typingMessage);

    fetch('http://127.0.0.1:5001/sales_opportunity', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'merchant-id': merchantId
        }
    })
        .then(response => response.json())
        .then(data => {
            document.querySelector('.messages').removeChild(typingMessage);

            const responseMessage = document.createElement('div');
            responseMessage.classList.add('message', 'received', 'backend-message'); // Add 'backend-message' here

            responseMessage.innerHTML = `
                <span class="message-text">${data.reply}</span>
            `;
            document.querySelector('.messages').appendChild(responseMessage);
            scrollToNewMessage();
        })
        .catch(error => {
            console.error('Error fetching sales trend:', error);
            document.querySelector('.messages').removeChild(typingMessage);

            const errorMessage = document.createElement('div');
            errorMessage.classList.add('message', 'received', 'error');
            errorMessage.innerText = "Sorry, I couldn't fetch the sales opportunity.";
            document.querySelector('.messages').appendChild(errorMessage);
            scrollToNewMessage();
        });
}


function displayOperationalBottleneck() {
    scrollToNewMessage()
    console.log("displayOperationalBottleneck() executed")

    let merchantId = localStorage.getItem('merchantID');
    console.log('MerchantId : ', merchantId);
    if (!merchantId) {
        console.error('Merchant ID is not available');
        return;
    }

    const inventoryMessage = document.createElement('div');
    inventoryMessage.classList.add('message', 'received');
    inventoryMessage.style.backgroundColor = '#c1e2be'; // Light green background
    inventoryMessage.innerHTML = "Here is your store Operational Bottleneck:";
    document.querySelector('.messages').appendChild(inventoryMessage);

    // Optional: Add a temporary typing indicator
    const typingMessage = document.createElement('div');
    typingMessage.classList.add('message', 'typing');
    typingMessage.innerHTML = '<span class="dot"></span><span class="dot"></span><span class="dot"></span>';
    document.querySelector('.messages').appendChild(typingMessage);

    fetch('http://127.0.0.1:5001/operational_bottleneck', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'merchant-id': merchantId
        }
    })
        .then(response => {
            console.log('Response Status:', response.status);  // Log status code
            return response.json();
        })
        .then(data => {
            console.log('API Response:', data);  // Log the entire response
            document.querySelector('.messages').removeChild(typingMessage);

            const responseMessage = document.createElement('div');
            responseMessage.classList.add('message', 'received', 'backend-message'); // Add 'backend-message' here

            responseMessage.innerHTML = `
        <span class="message-text">${data.reply || data.error || 'Unexpected error'}</span>
    `;
            document.querySelector('.messages').appendChild(responseMessage);
            scrollToNewMessage();
        })
        .catch(error => {
            console.error('Error fetching operational bottleneck:', error);
            document.querySelector('.messages').removeChild(typingMessage);

            const errorMessage = document.createElement('div');
            errorMessage.classList.add('message', 'received', 'error');
            errorMessage.innerText = "Sorry, I couldn't fetch the operational bottleneck.";
            document.querySelector('.messages').appendChild(errorMessage);
            scrollToNewMessage();
        });
}

/* for Tailored Advice */
function generateGetAdviceBtn() {
    console.log('generateGetAdviceBtn function called');

    // Create a container for the button (optional)
    var buttonContainer = document.createElement('div');
    buttonContainer.classList.add('btnContainer');  // Optional class for styling

    // Create the "Get Advice" button
    const button = document.createElement('button');
    button.classList.add('get_advice_btn');  // Add class to style the button
    button.innerHTML = "Get Advice";  // Button text

    // Attach the click event to the button
    button.onclick = function () {
        console.log("Get Advice button clicked");
        get_advice();  // Call the get_advice function when the button is clicked
    };

    // Append the button to the button container
    buttonContainer.appendChild(button);

    // Append the button container to a specific place in the DOM (e.g., .messages or .button-container)
    document.querySelector('.messages').appendChild(buttonContainer);
}

function get_advice(){
    console.log("get_advice() executed.")
    let merchantId = localStorage.getItem('merchantID');
    sendMessage("I want advice.", null, true)
}
