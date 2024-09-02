// script.js

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('checkInButton').addEventListener('click', function() {
        sendCheckInRequest();
    });

    document.getElementById('checkOutButton').addEventListener('click', function() {
        sendCheckOutRequest();
    });
});

function sendCheckInRequest() {
    fetch('/api/checkin', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        body: JSON.stringify({
            action: 'checkin',
            timestamp: new Date().toISOString()
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Checked in successfully!');
        } else {
            alert('Error checking in.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function sendCheckOutRequest() {
    fetch('/api/checkout', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        body: JSON.stringify({
            action: 'checkout',
            timestamp: new Date().toISOString()
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Checked out successfully!');
        } else {
            alert('Error checking out.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}
