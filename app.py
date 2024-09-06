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

@app.route('/userbase')
def userbase():
    if 'role' not in session:
        return redirect(url_for('login'))
    
    return render_template('userbase.html')


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


@app.route('/add_employee', methods=['GET', 'POST'])
def add_employee():
    if 'role' not in session:
        return redirect(url_for('login'))
    
    conn = get_db()
    cursor = conn.cursor()

    if session['role'] == 'staff':
        emp_id = session.get('emp_id')  # Assuming emp_id is stored in the session
        cursor.execute('''
            SELECT e.emp_id, e.emp_name, p.position_name, e.job_status, e.gender, e.termination_date, e.employee_status, e.join_date, d.name AS department_name
            FROM employee e
            JOIN position p ON e.pos_id = p.pos_id
            JOIN department d ON p.dept_id = d.dept_id
            WHERE e.emp_id = ?
        ''', (emp_id,))
    else:
        cursor.execute('''
            SELECT e.emp_id, e.emp_name, p.position_name, e.job_status, e.gender, e.termination_date, e.employee_status, e.join_date, d.name AS department_name
            FROM employee e
            JOIN position p ON e.pos_id = p.pos_id
            JOIN department d ON p.dept_id = d.dept_id
        ''')

    employees = cursor.fetchall()

    if request.method == 'POST':
        # Handle form submission and add employee
        emp_name = request.form['emp_name']
        position_id = request.form['position']
        job_status = request.form['job_status']
        gender = request.form['gender']
        termination_date = request.form['termination_date']
        join_date = request.form['join_date']
        employee_status = request.form['employee_status']

        # Get the position details including the department and basic salary
        cursor.execute('''
            SELECT position_name, dept_id, basic_salary
            FROM position
            WHERE pos_id = ?
        ''', (position_id,))
        position = cursor.fetchone()
        
        if position:
            position_name, department_id, basic_salary = position

            # Insert into the employee table
            cursor.execute('''
                INSERT INTO employee (emp_name, department, pos_id, job_status, gender, termination_date, join_date, employee_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (emp_name, department_id, position_id, job_status, gender, termination_date, join_date, employee_status))

            emp_id = cursor.lastrowid  # Get the last inserted employee ID

            # Get the current month and year
            from datetime import datetime
            current_month = datetime.now().strftime('%Y-%m')
            current_year = datetime.now().strftime('%Y')

            # Insert into the payroll table
            cursor.execute('''
                INSERT INTO payroll (emp_id, basic_salary, month, year)
                VALUES (?, ?, ?, ?)
            ''', (emp_id, basic_salary, current_month, current_year))

            conn.commit()
            conn.close()

            return redirect(url_for('add_employee'))

    # GET request: Render the form to add an employee
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT pos_id, position_name FROM position')
    positions = cursor.fetchall()
    conn.close()

    return render_template('add_employee.html', positions=positions, employees=employees)


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

    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    cursor.execute('''
        SELECT date, status
        FROM attendance
        WHERE emp_id = ? AND date BETWEEN ? AND ?
    ''', (session['emp_id'], start_of_week.strftime('%Y-%m-%d'), end_of_week.strftime('%Y-%m-%d')))
    
    attendance = cursor.fetchall()
    conn.close()
    flash('Check In process complete.')
    return render_template('check_in.html', attendance=attendance)


@app.route('/view_attendance')
def view_attendance():
    if 'role' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()
    
    # Get attendance for this week
    today = datetime.now()

    start_of_month = today.replace(day=1)

    if today.month == 12:  # If it's December, go to January of the next year
        end_of_month = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        end_of_month = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
    
    if session['role'] in ['manager', 'payroll_admin']:
        cursor.execute('''
    SELECT employee.emp_id, employee.emp_name, attendance.date, attendance.status
    FROM attendance
    JOIN employee ON attendance.emp_id = employee.emp_id
    WHERE attendance.date BETWEEN ? AND ?
        ''', (start_of_month.strftime('%Y-%m-%d'), end_of_month.strftime('%Y-%m-%d')))
    else:
        return redirect(url_for('check_in'))
    
    attendance = cursor.fetchall()
    conn.close()

    return render_template('view_attendance.html', attendance=attendance)


@app.route('/payroll_landing', methods=['GET'])
def payroll_landing():
    if 'role' not in session or session['role'] not in ['manager', 'payroll_admin', 'staff', 'recruit_admin']:
        return 'Access denied', 403

    conn = get_db()
    cursor = conn.cursor()

    # Adjust the SQL query to fetch all required fields
    if session['role'] in ['staff', 'recruit_admin']:
        emp_id = session.get('emp_id')  # Ensure emp_id is set in the session

        cursor.execute('''
            SELECT p.emp_id, e.emp_name AS name, p.basic_salary, p.tax, p.ssb, p.monthly_payout, 
                   p.net_salary, p.total_present, p.total_leave, p.edit_reason
            FROM payroll p
            JOIN employee e ON p.emp_id = e.emp_id
            WHERE p.emp_id = ?
        ''', (emp_id,))
    else:
        cursor.execute('''
            SELECT e.emp_id, e.emp_name AS name, p.basic_salary, p.tax, p.ssb, p.monthly_payout, 
                   p.net_salary, p.total_present, p.total_leave, p.edit_reason
            FROM payroll p
            JOIN employee e ON p.emp_id = e.emp_id
        ''')

    payroll_data = cursor.fetchall()
    conn.close()

    return render_template('payroll_landing.html', payroll_data=payroll_data)

@app.route('/calculate_payroll', methods=['POST'])
def calculate_payroll():
    if session.get('role') != 'manager':
        return redirect(url_for('index'))

    db = get_db()

    try:
        # Fetch current payroll settings
        settings = db.execute('SELECT default_ssb, tax_percentage FROM payroll_settings').fetchone()
        ssb_amount = settings['default_ssb']
        tax_percentage = settings['tax_percentage']

        # Get all employees
        employees = db.execute('SELECT emp_id, basic_salary FROM payroll').fetchall()

        for employee in employees:
            emp_id = employee['emp_id']
            basic_salary = employee['basic_salary']

            # Fetch attendance records for the employee
            attendance = db.execute('''
                SELECT status, COUNT(*) AS count
                FROM attendance
                WHERE emp_id = ?
                GROUP BY status
            ''', (emp_id,)).fetchall()

            total_present = next((record['count'] for record in attendance if record['status'] == 'Present'), 0)
            total_leave = next((record['count'] for record in attendance if record['status'] == 'Leave'), 0)

            # Calculate daily salary and monthly payout
            daily_salary = basic_salary / 30
            monthly_payout = (daily_salary * total_present) + (daily_salary * total_leave)
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
                SET monthly_payout = ?, tax = ?, ssb = ?, net_salary = ?, total_present = ?, total_leave = ?
                WHERE emp_id = ?
            ''', (monthly_payout, tax, ssb_amount, net_salary, total_present, total_leave, emp_id))

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
                db.execute('UPDATE payroll_settings SET default_ssb = ?', (default_ssb,))
            if tax_percentage:
                db.execute('UPDATE payroll_settings SET tax_percentage = ?', (tax_percentage,))
            
            # Update existing employee payroll records
            if default_ssb:
                db.execute('UPDATE payroll SET ssb = ?', (default_ssb,))
            if tax_percentage:
                db.execute('UPDATE payroll SET tax = monthly_payout * ? / 100', (tax_percentage,))
            
            db.commit()
            session['success'] = 'Settings updated successfully!'
        except Exception as e:
            session['error'] = f'Error updating settings: {e}'

        return redirect(url_for('payroll_settings'))

    # Fetch current settings from payroll_settings table
    settings = db.execute('SELECT default_ssb, tax_percentage FROM payroll_settings').fetchone()

    # Provide default values if settings are not found
    current_ssb_amount = settings['default_ssb'] if settings else 6000.0
    current_tax_rate = settings['tax_percentage'] if settings else 3.0

    return render_template('payroll_settings.html', current_ssb_amount=current_ssb_amount, current_tax_rate=current_tax_rate)


@app.route('/edit_payroll/<emp_id>', methods=['GET', 'POST'])
def edit_payroll(emp_id):
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
            (basic_salary, tax, ssb, monthly_payout, net_salary, edit_reason, emp_id)
        )
        db.commit()
        session['success'] = 'Payroll updated successfully!'
        return redirect(url_for('payroll_landing'))

    payroll_data = db.execute('SELECT * FROM payroll WHERE emp_id = ?', (emp_id,)).fetchone()
    return render_template('edit_payroll.html', payroll_data=payroll_data)


@app.route('/reset_payroll', methods=['POST'])
def reset_payroll():
    if 'role' not in session or session['role'] not in ['manager', 'payroll_admin']:
        return 'Access denied', 403

    conn = get_db()
    cursor = conn.cursor()

    # Get the current month and year
    from datetime import datetime
    now = datetime.now()
    current_month = now.strftime('%B')
    current_year = now.strftime('%Y')

    try:
        # Step 1: Insert or replace records into payroll_archive, preserving original edit_reason
        cursor.execute('''
            INSERT OR REPLACE INTO payroll_archive (emp_id, basic_salary, tax, ssb, total_present, total_leave, monthly_payout, net_salary, month, year, edit_reason)
            SELECT emp_id, basic_salary, tax, ssb, total_present, total_leave, monthly_payout, net_salary, ?, ?, edit_reason
            FROM payroll
        ''', (current_month, current_year))

        # Step 2: Reset payroll data
        cursor.execute('''
            UPDATE payroll
            SET tax = 0, ssb = 0, monthly_payout = 0, net_salary = 0, total_present = 0, total_leave = 0, edit_reason = ''
        ''')

        # Commit changes
        conn.commit()

        # Set success message
        session['success'] = 'Payroll has been reset and archived successfully.'

    except Exception as e:
        # Rollback in case of error
        conn.rollback()
        # Set error message
        session['error'] = f'Error occurred while resetting payroll: {str(e)}'

    finally:
        conn.close()

    return redirect(url_for('payroll_landing'))

@app.route('/view_archived_payroll', methods=['GET', 'POST'])
def view_archived_payroll():
    if 'role' not in session or session['role'] not in ['manager', 'payroll_admin']:
        return 'Access denied', 403

    conn = get_db()
    cursor = conn.cursor()

    archived_payroll_data = []
    selected_month = None
    selected_year = None

    if request.method == 'POST':
        selected_month = request.form['month']
        selected_year = request.form['year']

        cursor.execute('''
            SELECT pa.emp_id, e.emp_name, pa.basic_salary, pa.tax, pa.ssb, pa.monthly_payout, pa.net_salary, pa.total_present, pa.total_leave, pa.month, pa.year, pa.edit_reason
            FROM payroll_archive pa
            JOIN employee e ON pa.emp_id = e.emp_id
            WHERE pa.month = ? AND pa.year = ?
            ORDER BY e.emp_name ASC
        ''', (selected_month, selected_year))

        archived_payroll_data = cursor.fetchall()

    return render_template('view_archived_payroll.html', archived_payroll_data=archived_payroll_data, selected_month=selected_month, selected_year=selected_year)


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
        SELECT emp_id, basic_salary, tax, ssb, monthly_payout, net_salary, total_present, total_leave, month, year
        FROM payroll_archive
        WHERE emp_id = ? AND year = ?
        ORDER BY month ASC
    ''', (emp_id, current_year))

    payroll_data = cursor.fetchall()

    # Convert the rows to a list of dictionaries
    payroll_data_list = []
    month_names = {
        '01': 'January', '02': 'February', '03': 'March', '04': 'April',
        '05': 'May', '06': 'June', '07': 'July', '08': 'August',
        '09': 'September', '10': 'October', '11': 'November', '12': 'December'
    }
    for row in payroll_data:
        record = dict(row)  # Convert sqlite3.Row to a dictionary
        record['month'] = month_names.get(record['month'], record['month'])  # Default to numeric month if not found
        payroll_data_list.append(record)

    return render_template('my_payroll.html', payroll_data=payroll_data_list, current_year=current_year)

if __name__ == "__main__":
    app.run(debug=True)

