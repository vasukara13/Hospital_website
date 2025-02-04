from flask import Flask, render_template, request, redirect, url_for
import os
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)

# ----------------------------------------------------------------------------
# 1. Initialize the database (function only)
# ----------------------------------------------------------------------------
def init_db():
    """
    Create the 'appointments' table if it doesn't already exist.
    """
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT NOT NULL,
            contact_number TEXT NOT NULL,
            email_address TEXT,
            department TEXT NOT NULL,
            appointment_date TEXT NOT NULL,
            appointment_time TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/departments')
def departments():
    return render_template('departments.html')

@app.route('/departments/<department_name>')
def department_detail(department_name):
    # You can add logic here to fetch department details
    return render_template('department_detail.html', department_name=department_name)

@app.route('/facilities')
def facilities():
    return render_template('facilities.html')

@app.route('/facilities/<facility_name>')
def facility_detail(facility_name):
    # You can add logic here to fetch facility details
    return render_template('facility_detail.html', facility_name=facility_name)


@app.route('/submit_appointment', methods=['POST'])
def submit_appointment():
    # Get form data
    patient_name = request.form['patient_name']
    contact_number = request.form['contact_number']
    email_address = request.form.get('email_address', '')
    department = request.form['department']
    appointment_date_str = request.form['appointment_date']

    # Validate appointment date is not in the past
    appointment_date = datetime.strptime(appointment_date_str, '%Y-%m-%d').date()
    today = datetime.today().date()
    if appointment_date < today:
        error_message = "Appointment date cannot be in the past."
        return render_template('error.html', error_message=error_message)

    # Hospital operating hours
    hospital_open_time = datetime.combine(appointment_date, datetime.strptime('09:00', '%H:%M').time())
    hospital_close_time = datetime.combine(appointment_date, datetime.strptime('17:00', '%H:%M').time())
    appointment_duration = timedelta(minutes=10)

    # ----------------------------------------------------------------------------
    # Load existing appointments from the database for the chosen date/department
    # ----------------------------------------------------------------------------
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Fetch existing appointment times for this department on this date
    cursor.execute("""
        SELECT appointment_time 
        FROM appointments 
        WHERE department = ? 
          AND appointment_date = ?
    """, (department, appointment_date_str))
    existing_times = [row[0] for row in cursor.fetchall()]

    # Generate all possible appointment times for the day in 10-minute intervals
    appointment_times = []
    current_time = hospital_open_time
    while current_time < hospital_close_time:
        appointment_times.append(current_time.strftime('%H:%M'))
        current_time += appointment_duration

    # Find the next available appointment time
    available_times = [t for t in appointment_times if t not in existing_times]
    if available_times:
        estimated_time = available_times[0]

        # Insert new appointment into the database
        cursor.execute('''
            INSERT INTO appointments (
                patient_name, contact_number, email_address, department, 
                appointment_date, appointment_time
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (patient_name, contact_number, email_address, department, appointment_date_str, estimated_time))
        
        conn.commit()
        conn.close()

        # Pass the estimated time to the thank you page
        return redirect(url_for('thank_you', estimated_time=estimated_time, appointment_date=appointment_date_str))
    else:
        conn.close()
        # No available appointment times on this date
        return render_template('no_appointments.html', appointment_date=appointment_date_str, department=department)

@app.route('/thank_you')
def thank_you():
    estimated_time = request.args.get('estimated_time')
    appointment_date = request.args.get('appointment_date')
    return render_template('thank_you.html', estimated_time=estimated_time, appointment_date=appointment_date)

@app.route('/no_appointments')
def no_appointments():
    appointment_date = request.args.get('appointment_date')
    department = request.args.get('department')
    return render_template('no_appointments.html', appointment_date=appointment_date, department=department)

@app.route('/error')
def error():
    error_message = request.args.get('error_message')
    return render_template('error.html', error_message=error_message)


if __name__ == '__main__':
    # ----------------------------------------------------------------------------
    # 3. Manually initialize the database before running
    # ----------------------------------------------------------------------------
    init_db()
    app.run(debug=True)
