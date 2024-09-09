import sqlite3
import bcrypt

def init_db():
    conn = sqlite3.connect('hrm.db')
    cursor = conn.cursor()
    
    # Create department table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS department (
        dept_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    )
    ''')
    
    # Create position table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS position (
        pos_id INTEGER PRIMARY KEY AUTOINCREMENT,
        position_name TEXT NOT NULL,
        dept_id INTEGER NOT NULL,
        basic_salary REAL NOT NULL,
        FOREIGN KEY (dept_id) REFERENCES department (dept_id)
    )
    ''')

    # Create team table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS team (
        team_id INTEGER PRIMARY KEY AUTOINCREMENT,
        team_name TEXT NOT NULL,
        dept_id INTEGER,
        leader_id INTEGER,
        FOREIGN KEY (dept_id) REFERENCES department(dept_id),
        FOREIGN KEY (leader_id) REFERENCES employee(emp_id)
    )
    ''')

    # Create employee table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS employee (
        emp_id INTEGER PRIMARY KEY AUTOINCREMENT,
        emp_name TEXT NOT NULL,
        dept_id INTEGER NOT NULL,
        job_status TEXT NOT NULL,
        gender TEXT NOT NULL,
        termination_date DATE,
        employee_status TEXT NOT NULL,
        join_date DATE NOT NULL,
        pos_id INTEGER NOT NULL,
        FOREIGN KEY (pos_id) REFERENCES position (pos_id),
        FOREIGN KEY (dept_id) REFERENCES department (dept_id)
    )
    ''')

    # Create career table to track employee career changes
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS career (
        career_id INTEGER PRIMARY KEY AUTOINCREMENT,
        emp_id INTEGER NOT NULL,
        pos_id INTEGER,
        dept_id INTEGER,
        team_id INTEGER,
        status TEXT NOT NULL,  -- Promotion, Demotion, Transfer, etc.
        start_date DATE NOT NULL,
        end_date DATE,
        FOREIGN KEY (emp_id) REFERENCES employee (emp_id),
        FOREIGN KEY (pos_id) REFERENCES position (pos_id),
        FOREIGN KEY (dept_id) REFERENCES department (dept_id),
        FOREIGN KEY (team_id) REFERENCES team (team_id)
    )
    ''')

    # Create payroll table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS payroll (
        payroll_id INTEGER PRIMARY KEY AUTOINCREMENT,
        emp_id INTEGER NOT NULL,
        basic_salary REAL,
        tax REAL,
        ssb REAL DEFAULT 6000,
        total_present INTEGER,
        total_leave INTEGER,
        monthly_payout REAL,
        net_salary REAL,
        month TEXT NOT NULL,
        year TEXT NOT NULL,
        FOREIGN KEY (emp_id) REFERENCES employee (emp_id)
    )
    ''')

    # Create payroll_archive table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS payroll_archive (
        archive_id INTEGER PRIMARY KEY AUTOINCREMENT,
        emp_id INTEGER NOT NULL,
        basic_salary REAL,
        tax REAL,
        ssb REAL DEFAULT 6000,
        total_present INTEGER,
        total_leave INTEGER,
        monthly_payout REAL,
        net_salary REAL,
        month TEXT NOT NULL,
        year TEXT NOT NULL,
        archived_date DATE DEFAULT (datetime('now')),
        FOREIGN KEY (emp_id) REFERENCES employee (emp_id)
    )
    ''')

    # Create attendance table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attendance (
        attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
        emp_id INTEGER NOT NULL,
        date DATE NOT NULL,
        status TEXT CHECK(status IN ('Present', 'Leave')) NOT NULL,
        FOREIGN KEY (emp_id) REFERENCES employee (emp_id)
    )
    ''')

    # Create users table for employee logins
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        emp_id INTEGER NOT NULL,
        password BLOB NOT NULL,  -- Hashed password
        role TEXT CHECK(role IN ('manager', 'recruit_admin', 'payroll_admin', 'staff')) NOT NULL,
        FOREIGN KEY (emp_id) REFERENCES employee (emp_id)
    )
    ''')

    # Create payroll_settings table for default payroll settings
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS payroll_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tax_percentage REAL DEFAULT 3.0,  -- Default tax percentage
        default_ssb REAL DEFAULT 6000.0   -- Default SSB amount
    )
    ''')

    # Insert default departments
    cursor.execute('''
    INSERT OR IGNORE INTO department (name) VALUES
    ('HR'), ('Engineering'), ('Marketing')
    ''')

    # Insert default positions
    cursor.execute('''
    INSERT OR IGNORE INTO position (position_name, dept_id, basic_salary) VALUES
    ('HR Manager', 1, 60000), ('Software Engineer', 2, 80000), ('Marketing Specialist', 3, 50000)
    ''')

    # Insert default employees
    cursor.execute('''
    INSERT OR IGNORE INTO employee (emp_name, dept_id, job_status, gender, termination_date, employee_status, join_date, pos_id) VALUES
    ('John Doe', 1, 'Active', 'Male', NULL, 'Active', '2022-01-01', 1),
    ('Jane Smith', 2, 'Active', 'Female', NULL, 'Active', '2022-02-01', 2),
    ('Emily Johnson', 3, 'Active', 'Female', NULL, 'Active', '2022-03-01', 3),
    ('Payroll Admin', 3, 'Active', 'Female', NULL, 'Active', '2022-03-01', 3)
    ''')

    # Insert default users with hashed passwords
    users = [
        ('John Doe', 'password123', 'manager'),
        ('Jane Smith', 'password123', 'staff'),
        ('Emily Johnson', 'password123', 'recruit_admin'),
        ('Payroll Admin', 'password123', 'payroll_admin')
    ]

    for emp_name, plain_password, role in users:
        cursor.execute('''
        SELECT emp_id FROM employee WHERE emp_name = ?
        ''', (emp_name,))
        emp_id = cursor.fetchone()[0]
        
        hashed_password = bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt())

        cursor.execute('''
        INSERT OR IGNORE INTO users (emp_id, password, role) VALUES
        (?, ?, ?)
        ''', (emp_id, hashed_password, role))

    conn.commit()
    conn.close()
    print("Database initialized and default data inserted successfully.")

if __name__ == "__main__":
    init_db()
