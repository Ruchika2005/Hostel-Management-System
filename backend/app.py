from flask import Flask, render_template, request, redirect, session, url_for
from datetime import timedelta
from db_config import get_connection
import pymysql


app = Flask(__name__)
app.secret_key = "supersecretkey"
app.permanent_session_lifetime = timedelta(hours=1)

@app.route('/')
def home():
    return render_template('index.html')

# ✅ Admin Login
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        name = request.form.get('name')
        password = request.form.get('password')

        if not name or not password:
            return render_template('admin_login.html', error='All fields are required')

        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM admins WHERE name=%s AND password=%s", (name, password))
            admin = cursor.fetchone()
        conn.close()

        if admin:
            session['admin_logged_in'] = True
            session['admin_name'] = name
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error='Invalid credentials')

    return render_template('admin_login.html')




# ✅ Applicant dashboard
@app.route('/applicant/dashboard')
def applicant_dashboard():
    if not session.get('student_logged_in') or session.get('student_type') != 'applicant':
        return redirect(url_for('student_login'))

    roll_no = session['roll_no']
    conn = get_connection()
    with conn.cursor(cursor=pymysql.cursors.DictCursor) as cursor:
        cursor.execute("SELECT * FROM applications WHERE roll_no=%s", (roll_no,))
        applicant = cursor.fetchone()
    conn.close()

    if not applicant:
        return redirect(url_for('student_login'))

    return render_template("applicant_dashboard.html", applicant=applicant)


# ✅ Admin Logout
@app.route('/admin/logout', methods=['POST'])
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_name', None)
    return redirect(url_for('admin_login'))

# ✅ Apply
@app.route('/apply', methods=['GET', 'POST'])
def apply_page():
    if request.method == 'POST':
        roll_no = request.form['roll_no']
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        branch = request.form['branch']
        year = request.form['year']
        gender = request.form['gender']
        password = request.form['password']

        conn = get_connection()
        with conn.cursor() as cursor:
            # Check if already applied or exists
            cursor.execute("SELECT * FROM applications WHERE roll_no = %s", (roll_no,))
            if cursor.fetchone():
                return render_template('apply.html', error='Application already exists.')

            cursor.execute("SELECT * FROM students WHERE roll_no = %s", (roll_no,))
            if cursor.fetchone():
                return render_template('apply.html', error='Already registered as a student.')

            # Insert into applications table
            cursor.execute("""
                INSERT INTO applications (roll_no, name, email, phone, branch, year, gender, password)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (roll_no, name, email, phone, branch, year, gender, password))

            conn.commit()

        conn.close()
        return render_template('student_login.html', success='Application submitted successfully!')

    return render_template('apply.html')

# ✅ Admin dashboard

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    conn = get_connection()
    with conn.cursor(pymysql.cursors.DictCursor) as cursor:
        # ✅ Get all students and their rooms
        cursor.execute("SELECT name, roll_no, branch, year, room_id FROM students")
        students = cursor.fetchall()

        # ✅ Get total number of rooms
        cursor.execute("SELECT COUNT(*) AS total_rooms FROM rooms")
        total_rooms = cursor.fetchone()['total_rooms']

        # ✅ Get capacity and occupied info for each room
        cursor.execute("""
            SELECT r.room_id, r.capacity, COUNT(s.roll_no) AS occupied
            FROM rooms r
            LEFT JOIN students s ON r.room_id = s.room_id
            GROUP BY r.room_id, r.capacity
        """)
        room_status = cursor.fetchall()

        # ✅ Calculate total seats
        cursor.execute("SELECT SUM(capacity) AS total_capacity FROM rooms")
        total_seats = cursor.fetchone()['total_capacity']

    conn.close()

    # ✅ Calculate vacant seats
    vacant_seats = sum(room['capacity'] - room['occupied'] for room in room_status)

    # ✅ Organize room data for display
    room_data = {}
    for stu in students:
        room_id = stu['room_id']
        if not room_id:
            continue  # Skip unassigned students

        wing = room_id[0]        # e.g., 'A' from 'A101'
        floor = int(room_id[1])  # e.g., '1' from 'A101'
        room_no = room_id

        room_data.setdefault(wing, {}).setdefault(floor, {}).setdefault(room_no, []).append(stu)

    return render_template("admin_dashboard.html",
                           name=session['admin_name'],
                           total_rooms=total_rooms,
                           total_seats=total_seats,
                           vacant_seats=vacant_seats,
                           room_data=room_data)



# ✅ Cancel Application
@app.route('/applicant/cancel', methods=['POST'])
def cancel_application():
    if not session.get('student_logged_in') or session.get('student_type') != 'applicant':
        return redirect(url_for('student_login'))

    roll_no = session['roll_no']
    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute("UPDATE applications SET status = 'cancelled' WHERE roll_no = %s", (roll_no,))
        conn.commit()
    conn.close()
    session.clear()
    return redirect(url_for('student_login'))


# ✅ Applicant Logout
@app.route('/applicant/logout', methods=['POST'])
def applicant_logout():
    session.pop('student_logged_in', None)
    session.pop('student_type', None)
    session.pop('roll_no', None)
    return redirect(url_for('student_login'))

# ✅ Admin Applications
@app.route('/admin/applications')
def admin_applications():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    conn = get_connection()
    with conn.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute("SELECT * FROM applications ORDER BY status, year DESC")
        applications = cursor.fetchall()
    conn.close()

    return render_template('admin_applications.html', applications=applications, active_page='applications', name=session['admin_name'])

# ✅ Student Login (checks application → students)
@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        roll_no = request.form.get('roll_no')
        password = request.form.get('password')

        conn = get_connection()
        with conn.cursor() as cursor:
            # First check in students table
            cursor.execute("SELECT * FROM students WHERE roll_no=%s AND password=%s", (roll_no, password))
            student = cursor.fetchone()

            if student:
                session['student_logged_in'] = True
                session['student_type'] = 'resident'
                session['roll_no'] = roll_no
                conn.close()
                return redirect(url_for('student_dashboard'))

            # Else check in applications
            cursor.execute("SELECT * FROM applications WHERE roll_no=%s AND password=%s", (roll_no, password))
            applicant = cursor.fetchone()

            if applicant:
                session['student_logged_in'] = True
                session['student_type'] = 'applicant'
                session['roll_no'] = roll_no
                conn.close()
                return redirect(url_for('applicant_dashboard'))

        conn.close()
        return render_template('student_login.html', error='Invalid credentials')

    return render_template('student_login.html')


# ✅ Student Dashboard
@app.route('/student/dashboard')
def student_dashboard():
    if not session.get('student_logged_in') or session.get('student_type') != 'resident':
        return redirect(url_for('student_login'))

    roll_no = session['roll_no']
    conn = get_connection()
    with conn.cursor(cursor=pymysql.cursors.DictCursor) as cursor:
        cursor.execute("SELECT * FROM students WHERE roll_no = %s", (roll_no,))
        student = cursor.fetchone()

        cursor.execute("SELECT roll_no, name, branch, year FROM students WHERE room_id = %s AND roll_no != %s", 
                       (student['room_id'], roll_no))
        roommates = cursor.fetchall()
    conn.close()

    return render_template('student_dashboard.html', student=student, roommates=roommates)

# ✅ Student Logout
@app.route('/student/logout', methods=['POST'])
def student_logout():
    session.clear()
    return redirect(url_for('student_login'))

# ✅ 1. START allotment logic route
# ✅ 1. START allotment logic route
@app.route('/admin/start_allotment')
def start_allotment():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    conn = get_connection()
    with conn.cursor(cursor=pymysql.cursors.DictCursor) as cursor:

        # 1. Get pending applicants
        cursor.execute("SELECT * FROM applications WHERE status='pending'")
        applicants = cursor.fetchall()
        print("Pending applicants:", len(applicants))
        if not applicants:
            return redirect(url_for('admin_allotment'))

        # 2. Get room info using occupants field
        cursor.execute("SELECT room_id, capacity, occupants, gender FROM rooms ORDER BY room_id")
        rooms = cursor.fetchall()
        print("Rooms fetched:", len(rooms))

        # 3. Track room status (but DO NOT UPDATE it in DB)
        room_status = {
            room['room_id']: {
                'capacity': room['capacity'],
                'occupied': room['occupants'],
                'gender': room['gender']
            }
            for room in rooms
        }

        # 4. Allocation logic
        allocations = []
        for app in applicants:
            roll_no = app['roll_no']
            gender = app['gender']
            allocated = False

            for room_id, info in room_status.items():
                if info['occupied'] < info['capacity'] and info['gender'] == gender:
                    allocations.append((roll_no, room_id))
                    room_status[room_id]['occupied'] += 1  # local increment only
                    print(f"✅ Allocating {roll_no} to {room_id}")
                    allocated = True
                    break

            if not allocated:
                print(f"❌ No room available for {roll_no}")

        # 5. Update applications and insert into allotments (ONLY these two tables)
        for roll_no, room_id in allocations:
            try:
                # Update application status
                cursor.execute("UPDATE applications SET status='accepted' WHERE roll_no=%s", (roll_no,))

                # Insert into allotments
                cursor.execute("""
                    INSERT INTO allotments (student_roll_no, room_id, status)
                    VALUES (%s, %s, 'accepted')
                """, (roll_no, room_id))

            except Exception as e:
                print(f"❌ Error allocating {roll_no} to {room_id}: {e}")
                conn.rollback()

        conn.commit()
        print(f"✅ Total allocations done: {len(allocations)}")

    conn.close()
    return redirect(url_for('admin_allotment'))

# ✅ 2. ALLOTMENT VIEW PAGE
@app.route('/admin/allotment')
def admin_allotment():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    conn = get_connection()
    with conn.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute("""
            SELECT a.student_roll_no, a.room_id, s.name, s.branch, s.year
            FROM allotments a
            JOIN applications s ON a.student_roll_no = s.roll_no
            
        """)
        students = cursor.fetchall()
    conn.close()

    room_data = {}
    for stu in students:
        room_id = stu['room_id']
        if not room_id:
            continue

        wing = room_id[0]
        floor = int(room_id[1])

        if wing not in room_data:
            room_data[wing] = {}
        if floor not in room_data[wing]:
            room_data[wing][floor] = {}
        if room_id not in room_data[wing][floor]:
            room_data[wing][floor][room_id] = []

        room_data[wing][floor][room_id].append(stu)

    return render_template("admin_allotment.html", room_data=room_data, name=session['admin_name'])

if __name__ == '__main__':
    app.run(debug=True)
