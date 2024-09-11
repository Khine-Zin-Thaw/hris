import sqlite3
import bcrypt
import datetime

# Function to add sample data to the database
def add_sample_data():
    conn = sqlite3.connect('hrm.db')
    cursor = conn.cursor()

    # Insert sample data into the department table
    cursor.execute("""
    INSERT INTO department (name) 
    VALUES ('IT')
    """)

    # Insert sample data into the position table
    cursor.execute("""
    INSERT INTO position (position_name, dept_id, basic_salary) 
    VALUES ('Developer', 1, 3000)
    """)
    cursor.execute("""
    INSERT INTO position (position_name, dept_id, basic_salary) 
    VALUES ('Senior Developer', 1, 5000)
    """)

    # Insert sample data into the employee table
    cursor.execute("""
    INSERT INTO employee (emp_name, dept_id, job_status, gender, employee_status, join_date, pos_id)
    VALUES ('Alice Johnson', 1, 'Active', 'Female', 'Employed', ?, 1)
    """, (datetime.date(2023, 1, 15),))
    cursor.execute("""
    INSERT INTO employee (emp_name, dept_id, job_status, gender, employee_status, join_date, pos_id)
    VALUES ('Bob Smith', 1, 'Active', 'Male', 'Employed', ?, 2)
    """, (datetime.date(2022, 6, 10),))

    # Insert sample data into the users table (assuming this is the login table)
    hashed_password_1 = bcrypt.hashpw('password123'.encode('utf-8'), bcrypt.gensalt())
    hashed_password_2 = bcrypt.hashpw('password456'.encode('utf-8'), bcrypt.gensalt())
    cursor.execute("""
    INSERT INTO users (emp_id, password, role)
    VALUES (1, ?, 'admin')
    """, (hashed_password_1,))
    cursor.execute("""
    INSERT INTO users (emp_id, password, role)
    VALUES (2, ?, 'employee')
    """, (hashed_password_2,))

    # Insert sample data into attendance table
    cursor.execute("""
    INSERT INTO attendance (emp_id, date, status)
    VALUES (1, ?, 'Present')
    """, (datetime.date(2024, 8, 15),))
    cursor.execute("""
    INSERT INTO attendance (emp_id, date, status)
    VALUES (2, ?, 'Present')
    """, (datetime.date(2024, 8, 15),))

    # Insert sample data into payroll table
    cursor.execute("""
    INSERT INTO payroll (emp_id, basic_salary, tax, ssb, monthly_payout, net_salary, month, year)
    VALUES (1, 3000, 300, 150, 2550, 2400, 'August', '2024')
    """)
    cursor.execute("""
    INSERT INTO payroll (emp_id, basic_salary, tax, ssb, monthly_payout, net_salary, month, year)
    VALUES (2, 5000, 500, 250, 4250, 4000, 'August', '2024')
    """)

    # Insert sample data into career table
    cursor.execute("""
    INSERT INTO career (emp_id, pos_id, dept_id, status, start_date)
    VALUES (1, 1, 1, 'Promoted', ?)
    """, (datetime.date(2023, 1, 15),))
    cursor.execute("""
    INSERT INTO career (emp_id, pos_id, dept_id, status, start_date)
    VALUES (2, 2, 1, 'Hired', ?)
    """, (datetime.date(2022, 6, 10),))

    conn.commit()
    conn.close()

# Function to query and print data from the database
def print_data():
    conn = sqlite3.connect('hrm.db')
    cursor = conn.cursor()

    # Query employee data
    print("Employees:")
    cursor.execute("SELECT * FROM employee")
    for row in cursor.fetchall():
        print(row)

    # Query department data
    print("\nDepartments:")
    cursor.execute("SELECT * FROM department")
    for row in cursor.fetchall():
        print(row)

    # Query position data
    print("\nPositions:")
    cursor.execute("SELECT * FROM position")
    for row in cursor.fetchall():
        print(row)

    # Query payroll data
    print("\nPayroll:")
    cursor.execute("SELECT * FROM payroll")
    for row in cursor.fetchall():
        print(row)

    # Query attendance data
    print("\nAttendance:")
    cursor.execute("SELECT * FROM attendance")
    for row in cursor.fetchall():
        print(row)

    # Query career data
    print("\nCareer:")
    cursor.execute("SELECT * FROM career")
    for row in cursor.fetchall():
        print(row)

    conn.close()

if __name__ == "__main__":

    # Add sample data to the database
    add_sample_data()

    # Print out the data to verify
    print_data()
