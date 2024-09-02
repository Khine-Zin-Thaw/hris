// shortcuts.js

// Function to add event listeners for keyboard shortcuts
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function(event) {
        // Check if the 'Ctrl' key is pressed
        if (event.ctrlKey) {
            switch (event.key) {
                case 's':
                    event.preventDefault(); // Prevent the default action (e.g., saving the page)
                    saveDocument();
                    break;
                case 'p':
                    event.preventDefault(); // Prevent the default action (e.g., printing the page)
                    printDocument();
                    break;
                case 'h':
                    event.preventDefault(); // Prevent the default action (e.g., navigating to home)
                    navigateHome();
                    break;
                default:
                    break;
            }
        }
    });
}

// Function to save the document (example implementation)
function saveDocument() {
    alert('Document saved!');
    // Implement save functionality here
}

// Function to print the document (example implementation)
function printDocument() {
    window.print();
}

// Function to navigate to the home page (example implementation)
function navigateHome() {
    window.location.href = '/';
}

// Initialize keyboard shortcuts when the document is loaded
document.addEventListener('DOMContentLoaded', function() {
    setupKeyboardShortcuts();
});
