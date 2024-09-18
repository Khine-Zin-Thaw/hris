# Reference for sqlite database set up:
# Source: https://docs.python.org/3/library/sqlite3.html
# Source: https://www.sqlite.org/doclist.html
# Reference for Flask:
# Source: https://flask.palletsprojects.com/en/3.0.x/
# Reference for the opensource 
# Source: https://github.com/orangehrm/orangehrm
# Reference for html template
# Source: https://themewagon.com/themes/free-responsive-bootstrap-5-html5-admin-template-sneat/
# Other Reference:
# Sources
# https://youtu.be/TM7VPOjM7zk
# https://youtu.be/nwj9Rf7qDDI


from datetime import datetime, timedelta
import sqlite3
import os
import bcrypt
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'secret'

# Define the upload folder and allowed extensions
photo_folder = os.path.join('static', 'uploads')  # Ensure this folder exists
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = photo_folder


if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])


def allowed_file(filename):
    """ Checking for the file extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_db():
    """ Set Up connection to database"""
    conn = sqlite3.connect('hrm.db')
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
@app.route('/index')
def index():
    """ For the displaying of the admin dashboard"""
    if 'role' not in session:
        return redirect(url_for('login'))

    if session['role'] == 'staff':
        return redirect(url_for('check_in'))

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM employee")
    total_employees = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM employee WHERE join_date >= date('now', 'start of month')")
    new_employees_this_month = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM department")
    total_departments = cursor.fetchone()[0]

    cursor.execute(
        "SELECT employee_status, COUNT(*) FROM employee GROUP BY employee_status")
    employee_status_overview = cursor.fetchall()

    cursor.execute('''
        SELECT date, COUNT(*) 
        FROM attendance 
        WHERE date >= date('now', 'start of month') 
        GROUP BY date
    ''')
    attendance_trends = cursor.fetchall()

    conn.close()

    return render_template('index.html',
                           total_employees=total_employees,
                           new_employees_this_month=new_employees_this_month,
                           total_departments=total_departments,
                           employee_status_overview=employee_status_overview,
                           attendance_trends=attendance_trends)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """ Log In page"""
    if request.method == 'POST':
        emp_id = request.form.get('emp_id')
        password = request.form.get('password')
        input_role = request.form.get('role')

        conn = get_db()
        cursor = conn.cursor()

        # Fetch the user with the given emp_id and role
        cursor.execute('''
            SELECT * FROM users WHERE emp_id = ? AND role = ?
        ''', (emp_id, input_role))
        user = cursor.fetchone()

        # Check if the user exists and the password matches
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
            session['emp_id'] = user['emp_id']
            session['role'] = user['role']

            # Fetch the employee's name and photo from the employee table
            cursor.execute(
                'SELECT emp_name, photo FROM employee WHERE emp_id = ?', (emp_id,))
            result = cursor.fetchone()

            if result:
                # Store employee name in session
                session['username'] = result['emp_name']
                # Handle photo
                session['photo'] = result['photo'] if result['photo'] else 'default-avatar.jpg'
            else:
                session['username'] = 'Unknown User'
                # Use default photo if no photo is found
                session['photo'] = 'default-avatar.jpg'

            conn.close()

            # Redirect based on the role
            if session['role'] == 'staff':
                # Redirect staff to check-in page
                return redirect(url_for('check_in'))
            else:
                # Redirect others to index or dashboard
                return redirect(url_for('index'))

        else:
            # Set error message if login fails
            session['error'] = 'Invalid login credentials or role'
            conn.close()

    return render_template('login.html')


@app.route('/logout')
def logout():
    """ Log out page""" 
    session.pop('emp_id', None)
    session.pop('role', None)
    return redirect(url_for('login'))


@app.route('/add_department', methods=['GET', 'POST'])
def add_department():
    if 'role' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        name = request.form['department_name']
        # Use .get() to handle missing values
        leader_id = request.form.get('leader_id')

        try:
            # Insert the new department with the selected leader (or NULL if no leader is selected)
            cursor.execute('INSERT INTO department (name, leader_id) VALUES (?, ?)',
                           (name, leader_id if leader_id else None))

            # Update the employee table to set the selected leader as a department leader
            if leader_id:
                cursor.execute(
                    'UPDATE employee SET is_dept_leader = 1 WHERE emp_id = ?', (leader_id,))

            # Commit the transaction
            conn.commit()

            flash('Department added successfully!')
        except Exception as e:
            conn.rollback()  # Rollback in case of error
            flash(f'Error adding department: {e}')
        finally:
            conn.close()

        return redirect(url_for('add_department'))

    # Pagination setup
    per_page = 5  # Departments per page
    page = request.args.get('page', 1, type=int)
    offset = (page - 1) * per_page

    # Fetch the total department count for pagination
    cursor.execute('SELECT COUNT(*) FROM department')
    total = cursor.fetchone()[0]

    # Fetch the departments for the current page along with their leaders
    cursor.execute('''
        SELECT d.dept_id, d.name, e.emp_name
        FROM department d
        LEFT JOIN employee e ON d.leader_id = e.emp_id
        LIMIT ? OFFSET ?
    ''', (per_page, offset))
    departments = cursor.fetchall()

    # Fetch all employees for the leader selection dropdown
    cursor.execute(
        '''SELECT emp_id, emp_name FROM employee WHERE emp_id NOT IN
        (SELECT leader_id FROM department WHERE leader_id IS NOT NULL)''')
    employees = cursor.fetchall()

    conn.close()

    # Calculate the total number of pages
    total_pages = (total + per_page - 1) // per_page

    # Pass the departments and employees to the template
    return render_template('add_department.html', departments=departments,
                           employees=employees, page=page,
                           total_pages=total_pages)


@app.route('/edit_department/<int:dept_id>', methods=['GET', 'POST'])
def edit_department(dept_id):
    if 'role' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        department_name = request.form['department_name']
        new_leader_id = request.form['leader_id'] if request.form.get(
            'leader_id') else None

        try:
            # Get the current leader's ID (before the update)
            cursor.execute(
                'SELECT leader_id FROM department WHERE dept_id = ?', (dept_id,))
            current_leader_id = cursor.fetchone()[0]

            # Update the department's name and leader
            cursor.execute('UPDATE department SET name = ?, leader_id = ? WHERE dept_id = ?',
                           (department_name, new_leader_id, dept_id))

            # Update the employee table
            # 1. Remove the `is_dept_leader` flag from the previous leader
            if current_leader_id:
                cursor.execute(
                    'UPDATE employee SET is_dept_leader = 0 WHERE emp_id = ?',
                    (current_leader_id,))

            # 2. Set the `is_dept_leader` flag for the new leader
            if new_leader_id:
                cursor.execute(
                    'UPDATE employee SET is_dept_leader = 1 WHERE emp_id = ?',
                    (new_leader_id,))

            conn.commit()
            flash('Department updated successfully!')
        except Exception as e:
            conn.rollback()
            flash(f'Error updating department: {e}')
        finally:
            conn.close()

        return redirect(url_for('add_department'))

    # GET request: Fetch the department details
    cursor.execute(
        'SELECT dept_id, name, leader_id FROM department WHERE dept_id = ?',
        (dept_id,))
    department = cursor.fetchone()

    # Fetch all employees (excluding current leaders or the current leader of
    # this department)
    cursor.execute('''
        SELECT emp_id, emp_name FROM employee
        WHERE emp_id NOT IN (SELECT leader_id FROM department WHERE leader_id
        IS NOT NULL AND leader_id != ?)
        OR emp_id = ?
    ''', (department[2], department[2]))
    employees = cursor.fetchall()

    conn.close()
    return render_template('edit_department.html', department=department,
                           employees=employees)


@app.route('/delete_department/<int:dept_id>', methods=['POST'])
def delete_department(dept_id):
    if 'role' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()

    try:
        # Check if there are any positions associated with the department
        cursor.execute(
            'SELECT COUNT(*) FROM position WHERE dept_id = ?', (dept_id,))
        position_count = cursor.fetchone()[0]

        if position_count > 0:
            flash('Cannot delete department as there are positions associated with it.')
            return redirect(url_for('add_department'))

        # If no positions are associated, delete the department
        cursor.execute('DELETE FROM department WHERE dept_id = ?', (dept_id,))
        conn.commit()
        flash('Department deleted successfully!')
    except Exception as e:
        conn.rollback()
        flash(f'Error deleting department: {e}')
    finally:
        conn.close()

    return redirect(url_for('add_department'))


@app.route('/add_position', methods=['GET', 'POST'])
def add_position():
    conn = get_db()
    cursor = conn.cursor()

    # Check if the user is a manager
    if session.get('role') != 'manager':
        flash('You do not have permission to add positions.')
        return redirect(url_for('index'))

    if request.method == 'POST':
        position_name = request.form.get('position_name')
        team_id = request.form.get('team')  # Fetch the selected team
        basic_salary = request.form.get('basic_salary')

        # Validate form fields
        if not position_name or not team_id or not basic_salary:
            flash('All fields are required!')
            return redirect(url_for('add_position'))

        # Validate that basic_salary is numeric
        try:
            basic_salary = float(basic_salary)
            if basic_salary <= 0:
                raise ValueError
        except ValueError:
            flash('Basic salary must be a positive number!')
            return redirect(url_for('add_position'))

        try:
            # Fetch department based on the selected team
            cursor.execute(
                'SELECT dept_id FROM team WHERE team_id = ?', (team_id,))
            department_id = cursor.fetchone()[0]

            # Insert new position into the database with the inferred department
            cursor.execute('''
                INSERT INTO position 
                (position_name, dept_id, team_id, basic_salary)
                VALUES (?, ?, ?, ?)
            ''', (position_name, department_id, team_id, basic_salary))
            conn.commit()
            flash('Position added successfully!')

        except sqlite3.Error as e:
            conn.rollback()  # Rollback in case of error
            flash(f'An error occurred: {e}')
        finally:
            conn.close()

        return redirect(url_for('add_position'))

    # Fetch all teams for the form dropdown
    cursor.execute('SELECT team_id, team_name FROM team')
    teams = cursor.fetchall()

    # Pagination logic
    # Get current page, default is 1
    page = request.args.get('page', 1, type=int)
    per_page = 5  # Number of positions to display per page
    offset = (page - 1) * per_page

    # Fetch positions with pagination
    cursor.execute('''
        SELECT p.pos_id, p.position_name, d.name AS
        department_name, t.team_name, p.basic_salary
        FROM position p
        LEFT JOIN department d ON p.dept_id = d.dept_id
        LEFT JOIN team t ON p.team_id = t.team_id
        LIMIT ? OFFSET ?
    ''', (per_page, offset))
    positions = cursor.fetchall()

    # Count total number of positions for pagination
    cursor.execute('SELECT COUNT(*) FROM position')
    total_positions = cursor.fetchone()[0]
    total_pages = (total_positions + per_page -
                   1) // per_page  # Calculate total pages

    conn.close()

    return render_template('add_position.html', teams=teams,
                           positions=positions, page=page,
                           total_pages=total_pages)


@app.route('/edit_position/<int:pos_id>', methods=['GET', 'POST'])
def edit_position(pos_id):
    if 'role' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        position_name = request.form['position_name']
        department_id = request.form['department']
        basic_salary = request.form['basic_salary']
        # Handle no team case
        team_id = request.form['team'] if request.form['team'] else None

        try:
            # Update the position's details
            cursor.execute('''
            UPDATE position
            SET position_name = ?, dept_id = ?, team_id = ?, basic_salary = ?
            WHERE pos_id = ?
            ''', (position_name, department_id, team_id, basic_salary, pos_id))
            conn.commit()

        except Exception as e:
            conn.rollback()
            flash(f'An error occurred: {e}')
        finally:
            conn.close()

        return redirect(url_for('add_position'))

    # GET request: Fetch the current position details, list of departments, and teams
    cursor.execute(
        'SELECT pos_id, position_name, dept_id, basic_salary, team_id FROM position WHERE pos_id = ?', (pos_id,))
    position = cursor.fetchone()

    cursor.execute('SELECT dept_id, name FROM department')
    departments = cursor.fetchall()

    cursor.execute('SELECT team_id, team_name FROM team')
    teams = cursor.fetchall()  # Fetching the list of teams

    conn.close()

    return render_template('edit_position.html', position=position,
                           departments=departments, teams=teams)


@app.route('/delete_position/<int:pos_id>', methods=['POST'])
def delete_position(pos_id):
    if 'role' not in session:
        return redirect(url_for('login'))

    # Extract the pos_id from the form data
    pos_id = request.form.get('pos_id')
    conn = get_db()
    cursor = conn.cursor()

    try:
        # Check if any employees are assigned to this position
        cursor.execute(
            'SELECT COUNT(*) FROM employee WHERE pos_id = ?', (pos_id,))
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
    if 'role' not in session:
        return redirect(url_for('login'))

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
    if 'role' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        'DELETE FROM users WHERE user_id = ? AND role = ?', (user_id, role))
    conn.commit()

    conn.close()
    return redirect(url_for('check_employee_accounts'))


@app.route('/check_employee_accounts')
def check_employee_accounts():
    if 'role' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()

    # Pagination setup for the users with accounts
    page_users = request.args.get('page_users', 1, type=int)
    per_page_users = 10
    offset_users = (page_users - 1) * per_page_users

    # Fetch paginated users with name
    cursor.execute('''
    SELECT u.user_id, e.emp_id, e.emp_name, u.role
    FROM users u
    JOIN employee e ON u.emp_id = e.emp_id
    LIMIT ? OFFSET ?
    ''', (per_page_users, offset_users))
    users_with_name = cursor.fetchall()

    # Count total number of users
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]
    total_pages_users = (total_users + per_page_users - 1) // per_page_users

    current_emp_id = session.get('emp_id')

    # Pagination setup for employees with accounts
    page_employees = request.args.get('page_employees', 1, type=int)
    per_page_employees = 10
    offset_employees = (page_employees - 1) * per_page_employees

    # Fetch paginated employees with accounts
    cursor.execute('''
        SELECT e.emp_id, e.emp_name, u.role
        FROM employee e
        JOIN users u ON e.emp_id = u.emp_id
        LIMIT ? OFFSET ?
    ''', (per_page_employees, offset_employees))
    employees_with_accounts = cursor.fetchall()

    # Count total number of employees with accounts
    cursor.execute(
        'SELECT COUNT(*) FROM employee e JOIN users u ON e.emp_id = u.emp_id')
    total_employees_with_accounts = cursor.fetchone()[0]
    total_pages_employees = (
        total_employees_with_accounts + per_page_employees - 1) // per_page_employees

    # Fetch employees without accounts (no pagination)
    cursor.execute('''
        SELECT e.emp_id, e.emp_name
        FROM employee e
        LEFT JOIN users u ON e.emp_id = u.emp_id
        WHERE u.emp_id IS NULL
    ''')
    employees_without_accounts = cursor.fetchall()

    conn.close()

    return render_template(
        'check_employee_accounts.html',
        users_with_name=users_with_name,
        employees_with_accounts=employees_with_accounts,
        employees_without_accounts=employees_without_accounts,
        current_emp_id=current_emp_id,
        page_users=page_users,
        total_pages_users=total_pages_users,
        page_employees=page_employees,
        total_pages_employees=total_pages_employees
    )


@app.route('/reset_password/<int:user_id>', methods=['GET', 'POST'])
def reset_password(user_id):
    if 'role' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()

    # Ensure the SQL query fetches the correct columns, including user_id
    cursor.execute('''
        SELECT e.emp_name, u.user_id  -- Ensure user_id is selected
        FROM users u 
        JOIN employee e ON u.emp_id = e.emp_id 
        WHERE u.user_id = ?
    ''', (user_id,))
    user = cursor.fetchone()

    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('check_employee_accounts'))

    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if not new_password or not confirm_password:
            flash('Both password fields are required.', 'danger')
            return redirect(url_for('reset_password', user_id=user_id))

        if new_password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('reset_password', user_id=user_id))

        # Hash the new password using bcrypt
        hashed_password = bcrypt.hashpw(
            new_password.encode('utf-8'), bcrypt.gensalt())

        try:
            cursor.execute('''
                UPDATE users
                SET password = ?
                WHERE user_id = ?
            ''', (hashed_password, user_id))

            conn.commit()
            flash('Password reset successfully!', 'success')

        except sqlite3.Error as e:
            conn.rollback()
            flash(f'An error occurred while resetting the password: {
                  e}', 'danger')

        finally:
            conn.close()

        return redirect(url_for('check_employee_accounts'))

    conn.close()

    return render_template('reset_password.html', user=user)


@app.route('/add_users', methods=['POST'])
def add_users():
    if 'role' not in session:
        return redirect(url_for('login'))

    selected_employees = request.form.getlist(
        'emp_ids')  # List of selected employee IDs
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


@app.route('/myinfo')
def myinfo():
    if 'role' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()
    emp_id = session.get('emp_id')  # Assuming emp_id is stored in the session

    # Fetch employee information including phone_number and photo
    cursor.execute('''
        SELECT e.emp_id, e.emp_name, e.phone_number, e.photo, p.position_name, e.job_status, e.gender, 
               e.termination_date, e.employee_status, e.join_date, d.name
               AS department_name, t.team_name
        FROM employee e
        JOIN position p ON e.pos_id = p.pos_id
        JOIN department d ON p.dept_id = d.dept_id
        LEFT JOIN team t ON d.leader_id = t.team_id  -- Joining the team table to get team details
        WHERE e.emp_id = ?
    ''', (emp_id,))

    employee = cursor.fetchone()  # Fetch one record for the specific employee

    conn.close()

    if not employee:
        return "Employee not found", 404  # Handle case if employee is not found

    return render_template('myinfo.html', employee=employee)


@app.route('/add_employee', methods=['GET', 'POST'])
def add_employee():
    if 'role' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()

    # Pagination setup
    # Get current page, default to 1
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Number of employees to display per page
    offset = (page - 1) * per_page  # Calculate the offset for SQL query

    # Fetch employee data including email, phone, and photo with pagination
    emp_id = session.get('emp_id')  # Assuming emp_id is stored in the session
    if session.get('role') == 'staff':
        cursor.execute('''
            SELECT
            e.emp_id, e.emp_name, e.email, e.phone_number, p.position_name,
            e.job_status, e.gender, e.termination_date, 
            e.employee_status, e.join_date, d.name AS department_name, e.photo
            FROM employee e
            JOIN position p ON e.pos_id = p.pos_id
            JOIN department d ON p.dept_id = d.dept_id
            WHERE e.emp_id = ?
            LIMIT ? OFFSET ?
        ''', (emp_id, per_page, offset))
    else:
        cursor.execute('''
            SELECT
            e.emp_id, e.emp_name, e.email, e.phone_number,
            p.position_name, e.job_status, e.gender, e.termination_date,
            e.employee_status, e.join_date, d.name AS department_name, e.photo
            FROM employee e
            JOIN position p ON e.pos_id = p.pos_id
            JOIN department d ON p.dept_id = d.dept_id
            LIMIT ? OFFSET ?
        ''', (per_page, offset))

    employees = cursor.fetchall()

    # Count total employees for pagination
    cursor.execute('SELECT COUNT(*) FROM employee')
    total_employees = cursor.fetchone()[0]
    total_pages = (total_employees + per_page -
                   1) // per_page  # Calculate total pages

    if request.method == 'POST':
        # Capture form data
        emp_name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        position_id = request.form.get('position')
        job_status = request.form.get('job_status')
        gender = request.form.get('gender')
        join_date = request.form.get('join_date')
        employee_status = request.form.get('employee_status')
        termination_date = request.form.get('termination_date') or None

        # File upload handling
        photo = request.files.get('photo')  # Profile photo upload
        if not emp_name or not email or not phone or not position_id or not job_status or not join_date or not employee_status:
            flash('All fields are required!')
            return redirect(url_for('add_employee'))

        # Handle photo upload
        photo_filename = None  # Default if no photo is uploaded
        if photo and photo.filename != '':  # Check if the file exists
            if allowed_file(photo.filename):
                photo_filename = secure_filename(photo.filename)
                photo.save(os.path.join(
                    app.config['UPLOAD_FOLDER'], photo_filename))
            else:
                flash('Invalid photo format or no photo uploaded.')
                return redirect(url_for('add_employee'))

        try:
            # Get the position details including the department and basic salary
            cursor.execute('''
                SELECT position_name, dept_id, basic_salary
                FROM position
                WHERE pos_id = ?
            ''', (position_id,))
            position = cursor.fetchone()

            if position:
                position_name, department_id, basic_salary = position

                # Insert the new employee into the employee table
                cursor.execute('''
                    INSERT INTO employee 
                    (emp_name, email, phone_number, dept_id, pos_id,
                    job_status, gender, termination_date, join_date,
                    employee_status, photo)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (emp_name, email, phone, department_id, position_id,
                      job_status, gender, termination_date, join_date,
                      employee_status, photo_filename))

                emp_id = cursor.lastrowid  # Get the last inserted employee ID

                # Insert into the payroll table
                from datetime import datetime
                current_month = datetime.now().strftime('%Y-%m')
                current_year = datetime.now().strftime('%Y')

                cursor.execute('''
                    INSERT INTO payroll (emp_id, basic_salary, month, year)
                    VALUES (?, ?, ?, ?)
                ''', (emp_id, basic_salary, current_month, current_year))

                # Insert the employee's career information into the career table
                cursor.execute('''
                    INSERT INTO career 
                    (emp_id, pos_id, dept_id, team_id, status, start_date)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (emp_id, position_id, department_id, None, 'new_join',
                      join_date))  # Assuming team_id is None initially

                conn.commit()
                flash(
                    'Employee added successfully with photo!' if photo_filename else 'Employee added successfully without photo!')

        except sqlite3.Error as e:
            conn.rollback()
            flash(f'An error occurred: {e}')

        finally:
            conn.close()

        return redirect(url_for('add_employee'))

    # GET request: Fetch the positions
    cursor.execute('SELECT pos_id, position_name FROM position')
    positions = cursor.fetchall()

    conn.close()

    return render_template('add_employee.html', positions=positions,
                           employees=employees, page=page,
                           total_pages=total_pages)


@app.route('/edit_employee/<int:emp_id>', methods=['GET', 'POST'])
def edit_employee(emp_id):
    if 'role' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()

    # Fetch the employee data to pre-fill the form
    cursor.execute('''
        SELECT
        e.emp_id, e.emp_name, e.email, e.phone_number,
        p.pos_id, e.job_status, e.gender, e.join_date, e.employee_status,
        e.termination_date, e.photo
        FROM employee e
        JOIN position p ON e.pos_id = p.pos_id
        WHERE e.emp_id = ?
    ''', (emp_id,))
    employee = cursor.fetchone()

    # Fetch positions for the dropdown
    cursor.execute('SELECT pos_id, position_name, basic_salary FROM position')
    positions = cursor.fetchall()

    if request.method == 'POST':
        # Capture form data
        emp_name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        position_id = request.form.get('position')
        job_status = request.form.get('job_status')
        gender = request.form.get('gender')
        join_date = request.form.get('join_date')
        employee_status = request.form.get('employee_status')
        termination_date = request.form.get('termination_date') or None

        # Handle profile picture upload
        photo = request.files.get('photo')
        if photo and photo.filename != '':
            # Assuming you have a function 'allowed_file' to validate file types
            if allowed_file(photo.filename):
                photo_filename = secure_filename(photo.filename)
                photo.save(os.path.join(
                    app.config['UPLOAD_FOLDER'], photo_filename))
            else:
                flash('Invalid photo format', 'danger')
                return redirect(url_for('edit_employee', emp_id=emp_id))
        else:
            # Keep old photo if no new one is uploaded
            photo_filename = employee[10]

        # Fetch the new position's basic salary
        cursor.execute(
            'SELECT basic_salary FROM position WHERE pos_id = ?', (position_id,))
        basic_salary = cursor.fetchone()[0]

        try:
            # Update the employee data along with the new salary if the position changes
            cursor.execute('''
                UPDATE employee 
                SET emp_name = ?, email = ?, phone_number = ?, pos_id = ?,
                job_status = ?, gender = ?, join_date = ?, employee_status = ?,
                termination_date = ?, photo = ?
                WHERE emp_id = ?
            ''', (emp_name, email, phone, position_id, job_status, gender,
                  join_date, employee_status, termination_date, photo_filename,
                  emp_id))

            # Update the basic salary in the payroll table
            cursor.execute('''
                UPDATE payroll 
                SET basic_salary = ?
                WHERE emp_id = ?
            ''', (basic_salary, emp_id))

            conn.commit()
            flash(
                'Employee updated successfully, including new salary based on position!', 'success')
        except sqlite3.Error as e:
            conn.rollback()
            flash(f'An error occurred: {e}', 'danger')

        return redirect(url_for('add_employee'))

    conn.close()
    return render_template('edit_employee.html', employee=employee,
                           positions=positions)


@app.route('/delete_employee/<int:emp_id>', methods=['POST'])
def delete_employee(emp_id):
    if 'role' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()

    try:
        # Delete the employee from the database
        cursor.execute('DELETE FROM employee WHERE emp_id = ?', (emp_id,))
        conn.commit()
        flash('Employee deleted successfully!', 'success')
    except sqlite3.Error as e:
        conn.rollback()
        flash(f'An error occurred: {e}', 'danger')

    conn.close()
    return redirect(url_for('add_employee'))


@app.route('/check_in', methods=['GET', 'POST'])
def check_in():
    if 'role' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        status = request.form['status']
        emp_id = session['emp_id']
        today = datetime.now().strftime('%Y-%m-%d')

        # Check if a record for today already exists
        cursor.execute('''
            SELECT attendance_id FROM attendance
            WHERE emp_id = ? AND date = ?
        ''', (emp_id, today))
        existing_record = cursor.fetchone()

        if existing_record:
            # Update the existing record
            cursor.execute('''
                UPDATE attendance
                SET status = ?
                WHERE emp_id = ? AND date = ?
            ''', (status, emp_id, today))
        else:
            # Insert a new record
            cursor.execute('''
                INSERT INTO attendance (emp_id, date, status)
                VALUES (?, ?, ?)
            ''', (emp_id, today, status))

        conn.commit()

    # Fetch attendance records for the current week
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    cursor.execute('''
        SELECT date, status
        FROM attendance
        WHERE emp_id = ? AND date BETWEEN ? AND ?
    ''', (session['emp_id'], start_of_week.strftime('%Y-%m-%d'),
          end_of_week.strftime('%Y-%m-%d')))

    attendance = cursor.fetchall()

    conn.close()
    return render_template('check_in.html', attendance=attendance)


@app.route('/view_attendance', methods=['GET', 'POST'])
def view_attendance():
    if 'role' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()

    # Manually add attendance (if the form is submitted)
    if request.method == 'POST':
        emp_id = request.form.get('emp_id')
        date = request.form.get('date')
        status = request.form.get('status')

        # Check if the attendance record already exists
        cursor.execute('''
            SELECT attendance_id FROM attendance
            WHERE emp_id = ? AND date = ?
        ''', (emp_id, date))
        existing_record = cursor.fetchone()

        if existing_record:
            flash('Attendance for this date already exists.', 'danger')
        else:
            # Insert the new attendance record
            cursor.execute('''
                INSERT INTO attendance (emp_id, date, status)
                VALUES (?, ?, ?)
            ''', (emp_id, date, status))
            conn.commit()
            flash('Attendance added successfully!', 'success')

    # Pagination setup
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Show 10 records per page
    offset = (page - 1) * per_page

    # Get the current month
    today = datetime.now()
    start_of_month = today.replace(day=1)
    end_of_month = (start_of_month + timedelta(days=32)
                    ).replace(day=1) - timedelta(days=1)

    # Fetch attendance records for the whole month with pagination
    cursor.execute('''
        SELECT a.emp_id, e.emp_name, a.date, a.status
        FROM attendance a
        JOIN employee e ON a.emp_id = e.emp_id
        WHERE a.date BETWEEN ? AND ?
        ORDER BY a.date DESC
        LIMIT ? OFFSET ?
    ''', (start_of_month.strftime('%Y-%m-%d'),
          end_of_month.strftime('%Y-%m-%d'), per_page, offset))

    attendance = cursor.fetchall()

    # Count total attendance records for pagination
    cursor.execute('''
        SELECT COUNT(*) FROM attendance
        WHERE date BETWEEN ? AND ?
    ''', (start_of_month.strftime('%Y-%m-%d'),
          end_of_month.strftime('%Y-%m-%d')))
    total_records = cursor.fetchone()[0]

    conn.close()

    # Pass total pages count and current page for pagination
    total_pages = (total_records + per_page - 1) // per_page

    return render_template('view_attendance.html', attendance=attendance,
                           page=page, total_pages=total_pages)


@app.route('/edit_attendance/<int:emp_id>/<date>', methods=['GET', 'POST'])
def edit_attendance(emp_id, date):
    if 'role' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()

    # Fetch the existing attendance record
    cursor.execute('''
        SELECT status FROM attendance
        WHERE emp_id = ? AND date = ?
    ''', (emp_id, date))
    attendance_record = cursor.fetchone()

    if request.method == 'POST':
        status = request.form.get('status')

        # Update attendance status
        cursor.execute('''
            UPDATE attendance
            SET status = ?
            WHERE emp_id = ? AND date = ?
        ''', (status, emp_id, date))

        conn.commit()
        conn.close()

        flash('Attendance updated successfully!', 'success')
        return redirect(url_for('view_attendance'))

    conn.close()
    return render_template('edit_attendance.html', emp_id=emp_id, date=date,
                           status=attendance_record['status'])


@app.route('/delete_attendance/<int:emp_id>/<date>', methods=['POST'])
def delete_attendance(emp_id, date):
    if 'role' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()

    # Delete the attendance record
    cursor.execute('''
        DELETE FROM attendance
        WHERE emp_id = ? AND date = ?
    ''', (emp_id, date))

    conn.commit()
    conn.close()

    flash('Attendance record deleted successfully!', 'success')
    return redirect(url_for('view_attendance'))


@app.route('/payroll_landing', methods=['GET'])
def payroll_landing():
    if 'role' not in session or session['role'] not in ['manager',
                                                        'payroll_admin',
                                                        'staff',
                                                        'recruit_admin']:
        return 'Access denied', 403

    conn = get_db()
    cursor = conn.cursor()

    # Pagination variables
    # Get current page, default to 1
    page = request.args.get('page', 1, type=int)
    per_page = 5  # Records per page
    offset = (page - 1) * per_page  # Calculate offset

    if session['role'] in ['staff', 'recruit_admin']:
        emp_id = session.get('emp_id')  # Ensure emp_id is set in the session

        # Count total records for pagination
        cursor.execute(
            'SELECT COUNT(*) FROM payroll WHERE emp_id = ?', (emp_id,))
        total_records = cursor.fetchone()[0]

        # Fetch paginated records
        cursor.execute('''
            SELECT p.emp_id, e.emp_name AS name, p.basic_salary, p.tax, p.ssb, p.monthly_payout, 
                   p.net_salary, p.total_present, p.total_leave, p.edit_reason
            FROM payroll p
            JOIN employee e ON p.emp_id = e.emp_id
            WHERE p.emp_id = ?
            LIMIT ? OFFSET ?
        ''', (emp_id, per_page, offset))

    else:
        # Count total records for pagination
        cursor.execute('SELECT COUNT(*) FROM payroll')
        total_records = cursor.fetchone()[0]

        # Fetch paginated records
        cursor.execute('''
            SELECT e.emp_id, e.emp_name AS name, p.basic_salary, p.tax, p.ssb,
            p.monthly_payout,
            p.net_salary, p.total_present, p.total_leave, p.edit_reason
            FROM payroll p
            JOIN employee e ON p.emp_id = e.emp_id
            LIMIT ? OFFSET ?
        ''', (per_page, offset))

    payroll_data = cursor.fetchall()

    # Calculate total pages
    total_pages = (total_records + per_page - 1) // per_page

    conn.close()

    return render_template('payroll_landing.html', payroll_data=payroll_data,
                           page=page, total_pages=total_pages)


@app.route('/calculate_payroll', methods=['POST'])
def calculate_payroll():
    if session.get('role') != 'manager':
        return redirect(url_for('index'))

    db = get_db()

    try:
        # Fetch current payroll settings
        settings = db.execute(
            'SELECT default_ssb, tax_percentage FROM payroll_settings').fetchone()
        ssb_amount = settings['default_ssb']
        tax_percentage = settings['tax_percentage']

        # Get all employees
        employees = db.execute(
            'SELECT emp_id, basic_salary, edit_reason FROM payroll').fetchall()

        for employee in employees:
            emp_id = employee['emp_id']
            basic_salary = employee['basic_salary']
            edit_reason = employee['edit_reason'] if employee['edit_reason'] else ""

            # Fetch attendance records for the employee
            attendance = db.execute('''
                SELECT status, COUNT(*) AS count
                FROM attendance
                WHERE emp_id = ?
                GROUP BY status
            ''', (emp_id,)).fetchall()

            total_present = next(
                (record['count'] for record in attendance if record['status'] == 'Present'), 0)
            total_leave = next(
                (record['count'] for record in attendance if record['status'] == 'Leave'), 0)

            # Calculate daily salary and monthly payout
            daily_salary = basic_salary / 30
            monthly_payout = (daily_salary * total_present) + \
                (daily_salary * total_leave)
            monthly_payout = round(monthly_payout, 2)

            # Calculate tax
            tax = (tax_percentage / 100) * monthly_payout
            tax = round(tax, 2)

            # Calculate net salary
            net_salary = monthly_payout - tax - ssb_amount
            net_salary = round(net_salary, 2)

            # Format SSB amount
            ssb_amount = round(ssb_amount, 2)

            # Update payroll records
            db.execute('''
                UPDATE payroll
                SET monthly_payout = ?, tax = ?, ssb = ?, net_salary = ?,
                total_present = ?, total_leave = ?, edit_reason = ?
                WHERE emp_id = ?
            ''', (monthly_payout, tax, ssb_amount, net_salary, total_present,
                  total_leave, edit_reason, emp_id))

        db.commit()
        session['success'] = 'Payroll calculated and updated successfully!'
    except Exception as e:
        session['error'] = f'Error calculating payroll: {e}'

    return redirect(url_for('payroll_landing'))


@app.route('/payroll_settings', methods=['GET', 'POST'])
def payroll_settings():
    if session.get('role') != 'manager':
        return redirect(url_for('index'))

    db = get_db()

    if request.method == 'POST':
        default_ssb = request.form.get('default_ssb')
        tax_percentage = request.form.get('tax_percentage')

        try:
            # Update payroll settings in the database
            if default_ssb:
                db.execute(
                    'UPDATE payroll_settings SET default_ssb = ?',
                    (default_ssb,))
            if tax_percentage:
                db.execute(
                    'UPDATE payroll_settings SET tax_percentage = ?',
                    (tax_percentage,))

            # Update existing employee payroll records
            if default_ssb:
                db.execute('UPDATE payroll SET ssb = ?', (default_ssb,))
            if tax_percentage:
                db.execute(
                    'UPDATE payroll SET tax = monthly_payout * ? / 100',
                    (tax_percentage,))

            db.commit()
            session['success'] = 'Settings updated successfully!'
        except Exception as e:
            session['error'] = f'Error updating settings: {e}'

        return redirect(url_for('payroll_settings'))

    # Fetch current settings from payroll_settings table
    settings = db.execute(
        'SELECT default_ssb, tax_percentage FROM payroll_settings').fetchone()

    # Provide default values if settings are not found
    current_ssb_amount = settings['default_ssb'] if settings else 6000.0
    current_tax_rate = settings['tax_percentage'] if settings else 3.0

    return render_template('payroll_settings.html',
                           current_ssb_amount=current_ssb_amount,
                           current_tax_rate=current_tax_rate)


@app.route('/edit_payroll/<emp_id>', methods=['GET', 'POST'])
def edit_payroll(emp_id):
    if 'role' not in session:
        return redirect(url_for('login'))

    db = get_db()
    if request.method == 'POST':
        # Fetch form data
        basic_salary = request.form['basic_salary']
        tax = request.form['tax']
        ssb = request.form['ssb']
        monthly_payout = request.form['monthly_payout']
        net_salary = request.form['net_salary']
        edit_reason = request.form['edit_reason']

        # Update payroll with edit reason
        db.execute(
            'UPDATE payroll SET basic_salary = ?, tax = ?, ssb = ?, monthly_payout = ?, net_salary = ?, edit_reason = ? WHERE emp_id = ?',
            (basic_salary, tax, ssb, monthly_payout,
             net_salary, edit_reason, emp_id)
        )
        db.commit()
        session['success'] = 'Payroll updated successfully!'
        return redirect(url_for('payroll_landing'))

    payroll_data = db.execute(
        'SELECT * FROM payroll WHERE emp_id = ?', (emp_id,)).fetchone()
    return render_template('edit_payroll.html', payroll_data=payroll_data)


@app.route('/reset_payroll', methods=['POST'])
def reset_payroll():
    if 'role' not in session or session['role'] not in ['manager', 'payroll_admin']:
        return 'Access denied', 403
        return redirect(url_for('login'))
    conn = get_db()
    cursor = conn.cursor()

    from datetime import datetime
    now = datetime.now()
    current_month = now.strftime('%B')
    current_year = now.strftime('%Y')

    try:

        employees = cursor.execute('SELECT emp_id, basic_salary, tax, ssb, total_present, total_leave, monthly_payout, net_salary, edit_reason FROM payroll').fetchall()

        for employee in employees:
            emp_id, basic_salary, tax, ssb, total_present, total_leave, monthly_payout, net_salary, edit_reason = employee

            cursor.execute('''
                UPDATE payroll_archive
                SET basic_salary = ?, tax = ?, ssb = ?, total_present = ?,
                total_leave = ?, monthly_payout = ?, net_salary = ?,
                edit_reason = ?, archived_date = CURRENT_TIMESTAMP
                WHERE emp_id = ? AND month = ? AND year = ?
            ''', (basic_salary, tax, ssb, total_present, total_leave,
                  monthly_payout, net_salary, edit_reason, emp_id,
                  current_month, current_year))

            if cursor.rowcount == 0:
                cursor.execute('''
                    INSERT INTO payroll_archive
                    (emp_id, basic_salary, tax, ssb, total_present,
                    total_leave, monthly_payout, net_salary, month, year,
                    archived_date, edit_reason)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
                ''', (emp_id, basic_salary, tax, ssb, total_present,
                      total_leave, monthly_payout, net_salary, current_month,
                      current_year, edit_reason))

        # Step 4: Reset the payroll data after archiving
        cursor.execute('''
            UPDATE payroll
            SET tax = 0, ssb = 0, monthly_payout = 0, net_salary = 0,
            total_present = 0, total_leave = 0, edit_reason = ''
        ''')

        conn.commit()

    except Exception:
        conn.rollback()

    finally:
        conn.close()

    return redirect(url_for('payroll_landing'))


@app.route('/view_archived_payroll', methods=['GET', 'POST'])
def view_archived_payroll():
    if 'role' not in session or session['role'] not in ['manager',
                                                        'payroll_admin']:
        return 'Access denied', 403

    conn = get_db()
    cursor = conn.cursor()

    archived_payroll_data = []
    # Get selected month from the query params
    selected_month = request.args.get('month')
    # Get selected year from the query params
    selected_year = request.args.get('year')
    # Get current page, default to 1
    page = request.args.get('page', 1, type=int)
    per_page = 5  # Records per page

    if request.method == 'POST':
        selected_month = request.form['month']
        selected_year = request.form['year']
        return redirect(url_for('view_archived_payroll', month=selected_month,
                                year=selected_year, page=1))

    if selected_month and selected_year:
        # Count total records for pagination
        cursor.execute('''
            SELECT COUNT(*)
            FROM payroll_archive pa
            JOIN employee e ON pa.emp_id = e.emp_id
            WHERE pa.month = ? AND pa.year = ?
        ''', (selected_month, selected_year))
        total_records = cursor.fetchone()[0]

        # Calculate offset for pagination
        offset = (page - 1) * per_page

        # Fetch paginated data
        cursor.execute('''
            SELECT
            pa.emp_id, e.emp_name, pa.basic_salary, pa.tax, pa.ssb,
            pa.monthly_payout, pa.net_salary, pa.total_present, pa.total_leave,
            pa.month, pa.year, pa.edit_reason
            FROM payroll_archive pa
            JOIN employee e ON pa.emp_id = e.emp_id
            WHERE pa.month = ? AND pa.year = ?
            ORDER BY e.emp_name ASC
            LIMIT ? OFFSET ?
        ''', (selected_month, selected_year, per_page, offset))

        archived_payroll_data = cursor.fetchall()

        # Calculate total pages
        total_pages = (total_records + per_page - 1) // per_page

    else:
        total_pages = 0

    conn.close()

    return render_template(
        'view_archived_payroll.html',
        archived_payroll_data=archived_payroll_data,
        selected_month=selected_month,
        selected_year=selected_year,
        page=page,
        total_pages=total_pages
    )


@app.route('/my_payroll', methods=['GET'])
def my_payroll():
    if 'emp_id' not in session:
        return redirect(url_for('login'))

    emp_id = session['emp_id']
    conn = get_db()
    cursor = conn.cursor()

    # Get the current year
    from datetime import datetime
    now = datetime.now()
    current_year = now.strftime('%Y')

    # Fetch archived payroll data for the current year
    cursor.execute('''
        SELECT 
        emp_id, basic_salary, tax, ssb, monthly_payout, net_salary,
        total_present, total_leave, month, year
        FROM payroll_archive
        WHERE emp_id = ? AND year = ?
        ORDER BY month ASC
    ''', (emp_id, current_year))

    payroll_data = cursor.fetchall()

    # Convert the rows to a list of dictionaries since we will only get the number of the month for datetime
    payroll_data_list = []
    month_names = {
        '01': 'January', '02': 'February', '03': 'March', '04': 'April',
        '05': 'May', '06': 'June', '07': 'July', '08': 'August',
        '09': 'September', '10': 'October', '11': 'November', '12': 'December'
    }
    for row in payroll_data:
        record = dict(row)  # Convert sqlite3.Row to a dictionary
        # Default to numeric month if not found
        record['month'] = month_names.get(record['month'], record['month'])
        payroll_data_list.append(record)

    return render_template('my_payroll.html', payroll_data=payroll_data_list,
                           current_year=current_year)


@app.route('/teams', methods=['GET', 'POST'])
def teams():
    if 'role' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()

    # Handle form submission for adding a team
    if request.method == 'POST':
        team_name = request.form.get('team_name')
        department_id = request.form.get('department_id')
        team_leader_id = request.form.get('leader_id')

        if not team_name or not department_id:
            flash('Team name and department are required!')
            return redirect(url_for('teams'))

        try:
            if team_leader_id:
                cursor.execute('''
                    INSERT INTO team (team_name, dept_id, leader_id) 
                    VALUES (?, ?, ?)
                ''', (team_name, department_id, team_leader_id))
                cursor.execute(
                    'UPDATE employee SET is_team_leader = 1 WHERE emp_id = ?', (team_leader_id,))
            else:
                cursor.execute('''
                    INSERT INTO team (team_name, dept_id, leader_id) 
                    VALUES (?, ?, NULL)
                ''', (team_name, department_id))

            conn.commit()
            flash('Team added successfully!')

        except sqlite3.Error as e:
            conn.rollback()
            flash(f'An error occurred: {e}')

    # Pagination settings
    per_page = 5  # Number of teams per page
    # Get the current page from query params, default to 1
    page = request.args.get('page', 1, type=int)
    offset = (page - 1) * per_page  # Calculate the offset

    # Fetch total number of teams for pagination
    cursor.execute('SELECT COUNT(*) FROM team')
    total_teams = cursor.fetchone()[0]

    # Fetch teams with departments and leaders for the current page
    cursor.execute('''
        SELECT t.team_id, t.team_name, d.name AS department_name, e.emp_name AS leader_name
        FROM team t
        LEFT JOIN department d ON t.dept_id = d.dept_id
        LEFT JOIN employee e ON t.leader_id = e.emp_id
        LIMIT ? OFFSET ?
    ''', (per_page, offset))
    teams = cursor.fetchall()

    # Fetch departments for the dropdown
    cursor.execute('SELECT dept_id, name FROM department')
    departments = cursor.fetchall()

    # Fetch employees who are not yet team leaders
    cursor.execute('''
        SELECT emp_id, emp_name FROM employee
        WHERE emp_id NOT IN (SELECT leader_id FROM team WHERE leader_id IS NOT NULL)
    ''')
    employees = cursor.fetchall()

    # Calculate total pages for pagination
    total_pages = (total_teams + per_page - 1) // per_page

    conn.close()

    return render_template('teams.html',
                           teams=teams,
                           departments=departments,
                           employees=employees,
                           page=page,
                           total_pages=total_pages)


@app.route('/delete_team/<int:team_id>', methods=['POST'])
def delete_team(team_id):
    if 'role' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()

    try:
        # Delete the team
        cursor.execute('DELETE FROM team WHERE team_id = ?', (team_id,))
        conn.commit()
        flash('Team deleted successfully!', 'success')
    except sqlite3.Error as e:
        flash(f'An error occurred while deleting the team: {e}', 'danger')
        conn.rollback()

    conn.close()
    return redirect(url_for('teams'))


@app.route('/edit_team/<int:team_id>', methods=['GET', 'POST'])
def edit_team(team_id):
    if 'role' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()

    try:
        if request.method == 'POST':
            team_name = request.form.get('team_name')
            department_id = request.form.get('department_id')
            new_team_leader_id = request.form.get('team_leader_id')

            if not team_name or not department_id:
                flash('Team name and department are required.', 'danger')
                return redirect(url_for('edit_team', team_id=team_id))

            # Get the current leader's ID (before the update)
            cursor.execute(
                'SELECT leader_id FROM team WHERE team_id = ?', (team_id,))
            current_team_leader = cursor.fetchone()

            current_team_leader_id = current_team_leader[0] if current_team_leader else None

            # Update the team with the new details
            cursor.execute('''
                UPDATE team
                SET team_name = ?, dept_id = ?, leader_id = ?
                WHERE team_id = ?
            ''', (team_name, department_id, new_team_leader_id, team_id))

            # Reset the `is_team_leader` flag for the current leader if it is changing
            if current_team_leader_id and current_team_leader_id != new_team_leader_id:
                cursor.execute(
                    'UPDATE employee SET is_team_leader = 0 WHERE emp_id = ?',
                    (current_team_leader_id,))

            # Set the `is_team_leader` flag for the new leader
            if new_team_leader_id:
                cursor.execute(
                    'UPDATE employee SET is_team_leader = 1 WHERE emp_id = ?',
                    (new_team_leader_id,))

            conn.commit()
            flash('Team updated successfully!', 'success')

            return redirect(url_for('teams'))

        # GET request: Fetch the current team details to display in the form
        cursor.execute(
            'SELECT team_id, team_name, dept_id, leader_id FROM team WHERE team_id = ?', (team_id,))
        team = cursor.fetchone()

        if not team:
            flash('Team not found.', 'danger')
            return redirect(url_for('teams'))

        cursor.execute('SELECT dept_id, name FROM department')
        departments = cursor.fetchall()

        cursor.execute('''
            SELECT emp_id, emp_name 
            FROM employee 
            WHERE emp_id NOT IN (SELECT leader_id FROM team WHERE leader_id
            IS NOT NULL) 
            OR emp_id = ?
        ''', (team[3],))
        employees = cursor.fetchall()

        conn.close()

        return render_template('edit_teams.html', team=team,
                               departments=departments, employees=employees)

    except Exception as e:
        flash(f"An error occurred: {str(e)}", 'danger')
        conn.rollback()
        return redirect(url_for('teams'))


@app.route('/contact_us')
def contact_us():
    if 'role' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()

    # Query to fetch team information and leader details including the photo from the employee table
    cursor.execute('''
        SELECT t.team_name, e.emp_name as leader_name, e.email, e.phone_number, e.photo as leader_photo, t.team_id
        FROM team t
        JOIN employee e ON t.leader_id = e.emp_id
    ''')

    teams = cursor.fetchall()

    return render_template('contact_us.html', teams=teams)


@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    if 'role' not in session:
        return redirect(url_for('login'))

    staff_name = request.form.get('staff_name')
    problem_description = request.form.get('problem_description')
    team_id = request.form.get('team_id')

    # Get the current date
    submission_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if not staff_name or not problem_description or not team_id:
        flash('All fields are required!', 'danger')
        return redirect(url_for('people_link'))

    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO feedback
            (staff_name, problem_description, team_id, submission_date)
            VALUES (?, ?, ?, ?)
        ''', (staff_name, problem_description, team_id, submission_date))

        conn.commit()
        flash('Feedback submitted successfully!', 'success')

    except sqlite3.Error as e:
        conn.rollback()
        flash(f'An error occurred while submitting feedback: {e}', 'danger')

    finally:
        conn.close()
    return redirect(url_for('contact_us'))


@app.route('/my_attendance')
def my_attendance():
    if 'role' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()
    emp_id = session.get('emp_id')

    # Get the current year and month to filter attendance data for the current month
    current_year = datetime.now().year
    current_month = datetime.now().month

    # Fetch attendance data for the employee for the current month
    cursor.execute('''
        SELECT a.date, a.status
        FROM attendance a
        WHERE a.emp_id = ?
        AND strftime('%Y', a.date) = ?
        AND strftime('%m', a.date) = ?
        ORDER BY a.date
    ''', (emp_id, str(current_year), str(current_month).zfill(2)))
    attendance_records = cursor.fetchall()

    cursor.execute('SELECT pos_id, position_name FROM position')
    positions = cursor.fetchall()

    conn.close()

    return render_template('my_attendance.html',
                           positions=positions,
                           attendance_records=attendance_records)


@app.route('/about_us')
def about_us():
    if 'role' not in session:
        return redirect(url_for('login'))
    return render_template('about_us.html')


if __name__ == "__main__":
    app.run(debug=True)
