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


@app.route('/organization')
def organization():
    conn = sqlite3.connect('hrm.db')
    cursor = conn.cursor()
    
    # Fetch departments
    cursor.execute('SELECT dept_id, name FROM department')
    departments = cursor.fetchall()
    
    # Fetch positions with department names
    cursor.execute('''
        SELECT p.pos_id, p.position_name, d.name AS department, p.basic_salary
        FROM position p
        JOIN department d ON p.dept_id = d.dept_id
    ''')
    positions = cursor.fetchall()
    
    conn.close()
    return render_template('organization.html', departments=departments, positions=positions)


# Route for adding a department
@app.route('/add_department', methods=['GET', 'POST'])
def add_department():
    if request.method == 'POST':
        name = request.form['department_name']
        conn = sqlite3.connect('hrm.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO department (name) VALUES (?)', (name,))
        conn.commit()
        conn.close()
        return redirect(url_for('organization'))
    return render_template('add_department.html')


@app.route('/add_position', methods=['GET', 'POST'])
def add_position():
    if request.method == 'POST':
        position_name = request.form.get('position_name')
        department_id = request.form.get('department')
        basic_salary = request.form.get('basic_salary')

        if not position_name or not department_id or not basic_salary:
            flash('All fields are required!')
            return redirect(url_for('add_position'))

        try:
            conn = sqlite3.connect('hrm.db')
            cursor = conn.cursor()
            # Insert new position into the database
            cursor.execute('''
            INSERT INTO position (position_name, dept_id, basic_salary) 
            VALUES (?, ?, ?)
            ''', (position_name, department_id, basic_salary))
            conn.commit()
            conn.close()
            flash('Position added successfully!')

            # Optional: Update the employee payroll table with the new position's basic salary
            # Assuming you want to update existing employees with this position
            # This code assumes that you will be updating the basic_salary for existing employees in that position
            conn = sqlite3.connect('hrm.db')
            cursor = conn.cursor()
            cursor.execute('''
            UPDATE payroll
            SET basic_salary = ?
            WHERE emp_id IN (
                SELECT emp_id
                FROM employee
                WHERE pos_id = (SELECT pos_id FROM position WHERE position_name = ?)
            )
            ''', (basic_salary, position_name))
            conn.commit()
            conn.close()

        except sqlite3.Error as e:
            flash(f'An error occurred: {e}')
            return redirect(url_for('add_position'))

        return redirect(url_for('organization'))

    # GET request: Render the form
    conn = sqlite3.connect('hrm.db')
    cursor = conn.cursor()
    cursor.execute('SELECT dept_id, name FROM department')
    departments = cursor.fetchall()
    conn.close()

    return render_template('add_position.html', departments=departments)


if __name__ == "__main__":
    app.run(debug=True)
