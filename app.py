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
            SELECT * FROM users WHERE emp_id = ? AND role = ?
        ''', (emp_id, input_role))
        user = cursor.fetchone()

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
            session['emp_id'] = user['emp_id']
            session['role'] = user['role']
            return redirect(url_for('index'))
        else:
            session['error'] = 'Invalid login credentials or role'

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
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT dept_id, name FROM department')
    departments = cursor.fetchall()
    
    cursor.execute('''
        SELECT p.pos_id, p.position_name, d.name AS department, p.basic_salary
        FROM position p
        JOIN department d ON p.dept_id = d.dept_id
    ''')
    positions = cursor.fetchall()
    
    conn.close()
    return render_template('organization.html', departments=departments, positions=positions)

@app.route('/add_department', methods=['GET', 'POST'])
def add_department():
    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        name = request.form['department_name']
        cursor.execute('INSERT INTO department (name) VALUES (?)', (name,))
        conn.commit()
        return redirect(url_for('add_department'))

    # Fetch all departments to display them before the form
    cursor.execute('SELECT dept_id, name FROM department')
    departments = cursor.fetchall()  # Get all department records

    conn.close()
    return render_template('add_department.html', departments=departments)

@app.route('/edit_department/<int:dept_id>', methods=['GET', 'POST'])
def edit_department(dept_id):
    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        department_name = request.form['department_name']

        # Check if this department is associated with any positions
        cursor.execute('SELECT COUNT(*) FROM position WHERE dept_id = ?', (dept_id,))
        position_count = cursor.fetchone()[0]

        if position_count > 0:
            # If positions are associated, do not allow update
            flash('Cannot update department because it is associated with existing positions.')
            conn.close()
            return redirect(url_for('add_department'))

        # Update the department's name if no positions are associated
        cursor.execute('UPDATE department SET name = ? WHERE dept_id = ?', (department_name, dept_id))
        conn.commit()
        conn.close()
        return redirect(url_for('add_department'))

    # GET request: Fetch the department details
    cursor.execute('SELECT dept_id, name FROM department WHERE dept_id = ?', (dept_id,))
    department = cursor.fetchone()

    conn.close()
    return render_template('edit_department.html', department=department)

@app.route('/delete_department/<int:dept_id>', methods=['POST'])
def delete_department(dept_id):
    conn = get_db()
    cursor = conn.cursor()

    # Check if there are any positions associated with the department
    cursor.execute('SELECT COUNT(*) FROM position WHERE dept_id = ?', (dept_id,))
    position_count = cursor.fetchone()[0]

    if position_count > 0:
        flash('Cannot delete department as there are positions associated with it.')
        conn.close()
        return redirect(url_for('add_department'))

    # If no positions are associated, delete the department
    cursor.execute('DELETE FROM department WHERE dept_id = ?', (dept_id,))
    conn.commit()
    conn.close()
    flash('Department deleted successfully!')
    return redirect(url_for('add_department'))


@app.route('/add_position', methods=['GET', 'POST'])
def add_position():
    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        position_name = request.form.get('position_name')
        department_id = request.form.get('department')
        basic_salary = request.form.get('basic_salary')

        # Validate form fields
        if not position_name or not department_id or not basic_salary:
            flash('All fields are required!')
            return redirect(url_for('add_position'))

        try:
            # Insert new position into the database
            cursor.execute('''
                INSERT INTO position (position_name, dept_id, basic_salary)
                VALUES (?, ?, ?)
            ''', (position_name, department_id, basic_salary))
            conn.commit()
            flash('Position added successfully!')

            # Update payroll table (if needed)
            cursor.execute('''
                UPDATE payroll
                SET basic_salary = ?
                WHERE emp_id IN (
                    SELECT emp_id
                    FROM employee
                    WHERE pos_id = (
                        SELECT pos_id
                        FROM position
                        WHERE position_name = ?
                    )
                )
            ''', (basic_salary, position_name))
            conn.commit()

        except sqlite3.Error as e:
            flash(f'An error occurred: {e}')
            return redirect(url_for('add_position'))

        finally:
            conn.close()
        return redirect(url_for('add_position'))

    # Fetch all departments for the form dropdown
    cursor.execute('SELECT dept_id, name FROM department')
    departments = cursor.fetchall()

    # Fetch all positions to display in the table
    cursor.execute('''
        SELECT p.pos_id, p.position_name, d.name, p.basic_salary
        FROM position p
        JOIN department d ON p.dept_id = d.dept_id
    ''')
    positions = cursor.fetchall()

    conn.close()

    return render_template('add_position.html', departments=departments, positions=positions)


@app.route('/edit_position/<int:pos_id>', methods=['GET', 'POST'])
def edit_position(pos_id):
    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        position_name = request.form['position_name']
        department_id = request.form['department']
        basic_salary = request.form['basic_salary']
        
        # Update the position's details
        cursor.execute('''
        UPDATE position
        SET position_name = ?, dept_id = ?, basic_salary = ?
        WHERE pos_id = ?
        ''', (position_name, department_id, basic_salary, pos_id))
        conn.commit()

        # You can update related tables as necessary, like the payroll table
        # ...

        conn.close()
        return redirect(url_for('add_position'))

    # GET request: Fetch the current position details and list of departments
    cursor.execute('SELECT pos_id, position_name, dept_id, basic_salary FROM position WHERE pos_id = ?', (pos_id,))
    position = cursor.fetchone()

    cursor.execute('SELECT dept_id, name FROM department')
    departments = cursor.fetchall()

    conn.close()
    return render_template('edit_position.html', position=position, departments=departments)


@app.route('/delete_position/<int:pos_id>', methods=['POST'])
def delete_position(pos_id):
    pos_id = request.form.get('pos_id')  # Extract the pos_id from the form data
    conn = get_db()
    cursor = conn.cursor()

    try:
        # Check if any employees are assigned to this position
        cursor.execute('SELECT COUNT(*) FROM employee WHERE pos_id = ?', (pos_id,))
        employee_count = cursor.fetchone()[0]
        
        if employee_count > 0:
            flash('Cannot delete position as it is assigned to one or more employees.')
            conn.close()
            return redirect(url_for('organization'))

        # Check if the position exists before trying to delete it
        cursor.execute('SELECT * FROM position WHERE pos_id = ?', (pos_id,))
        position = cursor.fetchone()

        if not position:
            flash('Position not found.')
            conn.close()
            return redirect(url_for('organization'))

        # Delete the position if no employees are assigned and it exists
        cursor.execute('DELETE FROM position WHERE pos_id = ?', (pos_id,))
        conn.commit()
        flash('Position deleted successfully!')

    except Exception as e:
        conn.rollback()
        flash(f'An error occurred: {e}')
    finally:
        conn.close()

    return redirect(url_for('add_position'))

    
@app.route('/edit_user/<int:user_id>/<string:role>', methods=['GET', 'POST'])
def edit_user(user_id, role):
    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        emp_name = request.form['emp_name']
        new_role = request.form['role']

        cursor.execute('''
            UPDATE users
            SET emp_id = (SELECT emp_id FROM employee WHERE emp_name = ?), role = ?
            WHERE user_id = ? AND role = ?
        ''', (emp_name, new_role, user_id, role))
        conn.commit()

        return redirect(url_for('check_employee_accounts'))

    cursor.execute('''
        SELECT u.user_id, e.emp_name, u.role
        FROM users u
        JOIN employee e ON u.emp_id = e.emp_id
        WHERE u.user_id = ? AND u.role = ?
    ''', (user_id, role))
    user = cursor.fetchone()

    conn.close()
    return render_template('edit_user.html', user=user)

@app.route('/delete_user/<int:user_id>/<string:role>', methods=['POST'])
def delete_user(user_id, role):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('DELETE FROM users WHERE user_id = ? AND role = ?', (user_id, role))
    conn.commit()

    conn.close()
    return redirect(url_for('check_employee_accounts'))


@app.route('/check_employee_accounts')
def check_employee_accounts():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT 
        u.user_id, 
        e.emp_name, 
        u.role
    FROM 
        users u
    JOIN 
        employee e 
    ON 
        u.emp_id = e.emp_id
    ''')
    users_with_name = cursor.fetchall()
    current_emp_id = session.get('emp_id')


    # Fetch employees with accounts
    cursor.execute('''
        SELECT e.emp_id, e.emp_name, u.role
        FROM employee e
        JOIN users u ON e.emp_id = u.emp_id
    ''')
    employees_with_accounts = cursor.fetchall()

    # Fetch employees without accounts
    cursor.execute('''
        SELECT e.emp_id, e.emp_name
        FROM employee e
        LEFT JOIN users u ON e.emp_id = u.emp_id
        WHERE u.emp_id IS NULL
    ''')
    employees_without_accounts = cursor.fetchall()

    conn.close()
    return render_template('check_employee_accounts.html',
                           employees_with_accounts=employees_with_accounts,
                           employees_without_accounts=employees_without_accounts,
                           users_with_name=users_with_name, current_emp_id=current_emp_id
                           )


@app.route('/add_users', methods=['POST'])
def add_users():
    selected_employees = request.form.getlist('emp_ids')  # List of selected employee IDs
    password = request.form.get('password')
    role = request.form.get('role')

    if not selected_employees:
        flash('No employees selected for account creation.')
        return redirect(url_for('check_employee_accounts'))

    if not password or not role:
        flash('Password and role are required.')
        return redirect(url_for('check_employee_accounts'))

    conn = get_db()
    cursor = conn.cursor()

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    for emp_id in selected_employees:
        # Check if the employee already has an account
        cursor.execute('SELECT * FROM users WHERE emp_id = ?', (emp_id,))
        existing_user = cursor.fetchone()

        if not existing_user:
            # Create a new user account
            cursor.execute('''
                INSERT INTO users (emp_id, password, role)
                VALUES (?, ?, ?)
            ''', (emp_id, hashed_password, role))

    conn.commit()
    conn.close()

    flash('User accounts created successfully!')
    return redirect(url_for('check_employee_accounts'))


if __name__ == "__main__":
    app.run(debug=True)

