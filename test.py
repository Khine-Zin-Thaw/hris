# Function to add sample data to the database
def add_sample_data():
    conn = sqlite3.connect('hrm.db')
    cursor = conn.cursor()

    # Insert sample data into the organization table
    cursor.execute("""
    INSERT INTO organization (rank, department, basic_salary, position, job_status)
    VALUES ('Junior', 'IT', 3000, 'Developer', 'Active')
    """)
    cursor.execute("""
    INSERT INTO organization (rank, department, basic_salary, position, job_status)
    VALUES ('Senior', 'IT', 5000, 'Senior Developer', 'Active')
    """)

    # Insert sample data into the employee table
    cursor.execute("""
    INSERT INTO employee (emp_name, department, job_status, rank, gender, employee_status, join_date, pos_id)
    VALUES ('Alice Johnson', 'IT', 'Active', 'Junior', 'Female', 'Employed', ?, 1)
    """, (datetime.date(2023, 1, 15),))
    cursor.execute("""
    INSERT INTO employee (emp_name, department, job_status, rank, gender, employee_status, join_date, pos_id)
    VALUES ('Bob Smith', 'IT', 'Active', 'Senior', 'Male', 'Employed', ?, 2)
    """, (datetime.date(2022, 6, 10),))

    # Insert sample data into other tables as needed (login, attendance, payroll, career)
    cursor.execute("""
    INSERT INTO login (emp_id, password, type)
    VALUES (1, 'password123', 'admin')
    """)
    cursor.execute("""
    INSERT INTO login (emp_id, password, type)
    VALUES (2, 'password456', 'employee')
    """)

    cursor.execute("""
    INSERT INTO attendance (emp_id, attendance_status, leave_status, total_attendance, total_leave, date, month, year)
    VALUES (1, 'Present', 'No Leave', 20, 0, ?, 8, 2024)
    """, (datetime.date(2024, 8, 15),))

    cursor.execute("""
    INSERT INTO payroll (emp_id, basic_salary, tax, ssb, monthly_payout)
    VALUES (1, 3000, 300, 150, 2550)
    """)
    cursor.execute("""
    INSERT INTO payroll (emp_id, basic_salary, tax, ssb, monthly_payout)
    VALUES (2, 5000, 500, 250, 4250)
    """)

    cursor.execute("""
    INSERT INTO career (emp_id, status, join_date, termination_date)
    VALUES (1, 'Promoted', ?, NULL)
    """, (datetime.date(2023, 1, 15),))
    cursor.execute("""
    INSERT INTO career (emp_id, status, join_date, termination_date)
    VALUES (2, 'Hired', ?, NULL)
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

    # Query organization data
    print("\nOrganizations:")
    cursor.execute("SELECT * FROM organization")
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
    # Initialize the database and create tables
    init_db()

    # Add sample data to the database
    add_sample_data()

    # Print out the data to verify
    print_data()
