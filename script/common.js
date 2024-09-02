// common.js

// Function to add a class to an element
function addClass(element, className) {
    if (element && !element.classList.contains(className)) {
        element.classList.add(className);
    }
}

// Function to remove a class from an element
function removeClass(element, className) {
    if (element && element.classList.contains(className)) {
        element.classList.remove(className);
    }
}

// Function to toggle a class on an element
function toggleClass(element, className) {
    if (element) {
        element.classList.toggle(className);
    }
}

// Function to get the value of a URL parameter by name
function getURLParameter(name) {
    name = name.replace(/[\[\]]/g, '\\$&');
    var regex = new RegExp('[?&]' + name + '(=([^&#]*)|&|#|$)'),
        results = regex.exec(window.location.href);
    if (!results) return null;
    if (!results[2]) return '';
    return decodeURIComponent(results[2].replace(/\+/g, ' '));
}

// Function to create a new element with optional attributes and content
function createElement(tag, attributes, content) {
    var element = document.createElement(tag);
    if (attributes) {
        for (var key in attributes) {
            if (attributes.hasOwnProperty(key)) {
                element.setAttribute(key, attributes[key]);
            }
        }
    }
    if (content) {
        element.innerHTML = content;
    }
    return element;
}

// Function to handle AJAX requests
function ajaxRequest(url, method, data, callback) {
    var xhr = new XMLHttpRequest();
    xhr.open(method, url, true);
    xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    xhr.onload = function() {
        if (xhr.status >= 200 && xhr.status < 300) {
            callback(null, xhr.responseText);
        } else {
            callback(xhr.statusText, null);
        }
    };
    xhr.onerror = function() {
        callback(xhr.statusText, null);
    };
    xhr.send(data);
}

// Function to set up event listeners for elements
function setupEventListeners(selectors, eventType, callback) {
    var elements = document.querySelectorAll(selectors);
    elements.forEach(function(element) {
        element.addEventListener(eventType, callback);
    });
}

// Example usage: Setup click event listeners for buttons with the class 'btn'
document.addEventListener('DOMContentLoaded', function() {
    setupEventListeners('.btn', 'click', function(event) {
        alert('Button clicked: ' + event.target.id);
    });
});
