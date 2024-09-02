// def.js

// Utility function to get a DOM element by ID
function $(id) {
    return document.getElementById(id);
}

// Function to toggle the visibility of an element
function toggleVisibility(id) {
    var element = $(id);
    if (element) {
        if (element.style.display === 'none' || element.style.display === '') {
            element.style.display = 'block';
        } else {
            element.style.display = 'none';
        }
    }
}

// Function to validate an email address
function isValidEmail(email) {
    var regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
}

// Function to show an alert message
function showAlert(message) {
    alert(message);
}

// Function to validate a form
function validateForm(formId) {
    var form = $(formId);
    if (!form) return false;

    var isValid = true;
    var emailField = form.querySelector('input[type="email"]');
    if (emailField && !isValidEmail(emailField.value)) {
        showAlert('Please enter a valid email address.');
        isValid = false;
    }

    // Add more validation rules as needed

    return isValid;
}

// Function to set up event listeners for form submission
function setupFormValidation(formId) {
    var form = $(formId);
    if (form) {
        form.addEventListener('submit', function(event) {
            if (!validateForm(formId)) {
                event.preventDefault(); // Prevent form submission if validation fails
            }
        });
    }
}

// Example usage: Set up validation for a form with ID 'myForm'
document.addEventListener('DOMContentLoaded', function() {
    setupFormValidation('myForm');
});
