from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import bcrypt


app = Flask(__name__)
app.secret_key = '123'


def get_db():
    conn = sqlite3.connect('hrm.db')
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def index():
    if 'role' not in session:
        return redirect(url_for('login'))
    
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        emp_id = request.form.get('emp_id')
        password = request.form.get('password')
        input_role = request.form.get('role')

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM users WHERE emp_id = ?
        ''', (emp_id,))
        user = cursor.fetchone()

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
            correct_role = user['role']
            if correct_role == input_role:
                session['emp_id'] = user['emp_id']
                session['role'] = input_role  # Use the input role here
                return redirect(url_for('index'))
            else:
                session['error'] = 'Incorrect role selected'
        else:
            session['error'] = 'Invalid login credentials'

        conn.close()

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('emp_id', None)
    session.pop('role', None)
    return redirect(url_for('login'))


@app.route('/create_user', methods=['GET', 'POST'])
def create_user():
    if 'role' not in session or session['role'] != 'manager':
        return 'Access denied', 403

    if request.method == 'POST':
        emp_id = request.form.get('emp_id')
        password = request.form.get('password')
        role = request.form.get('role')

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO users (emp_id, password, role)
            VALUES (?, ?, ?)
        ''', (emp_id, hashed_password, role))

        conn.commit()
        conn.close()

        return redirect(url_for('index'))

    return render_template('create_user.html')


if __name__ == "__main__":
    app.run(debug=True)
