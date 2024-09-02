// server.js
const express = require('express');
const bodyParser = require('body-parser');
const mysql = require('mysql'); // You can use other databases as needed

const app = express();
app.use(bodyParser.json());

const connection = mysql.createConnection({
    host: 'localhost',
    user: 'root',
    password: 'password',
    database: 'employee_db'
});

connection.connect();

app.post('/api/checkin', (req, res) => {
    const { action, timestamp } = req.body;
    if (action === 'checkin') {
        const query = 'INSERT INTO checkin_checkout (employee_id, action, timestamp) VALUES (?, ?, ?)';
        connection.query(query, [1, 'checkin', timestamp], (error, results) => {
            if (error) {
                console.error('Database error:', error);
                return res.status(500).json({ success: false });
            }
            res.json({ success: true });
        });
    }
});

app.post('/api/checkout', (req, res) => {
    const { action, timestamp } = req.body;
    if (action === 'checkout') {
        const query = 'INSERT INTO checkin_checkout (employee_id, action, timestamp) VALUES (?, ?, ?)';
        connection.query(query, [1, 'checkout', timestamp], (error, results) => {
            if (error) {
                console.error('Database error:', error);
                return res.status(500).json({ success: false });
            }
            res.json({ success: true });
        });
    }
});

app.listen(3000, () => {
    console.log('Server running on http://localhost:3000');
});
