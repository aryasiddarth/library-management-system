from flask import Flask, request, render_template, send_from_directory, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Function to serve static files
def safe_send_from_directory(directory, filename):
    directory_path = os.path.join(app.root_path, directory)
    if os.path.exists(os.path.join(directory_path, filename)):
        return send_from_directory(directory_path, filename)
    return "File not found", 404

@app.route('/css/<path:filename>')
def serve_css(filename):
    return safe_send_from_directory('css', filename)

@app.route('/images/<path:filename>')
def serve_images(filename):
    return safe_send_from_directory('images', filename)

@app.route('/webfonts/<path:filename>')
def serve_webfonts(filename):
    return safe_send_from_directory('webfonts', filename)

@app.route('/')
def home():
    return render_template("index.html")

def check_credentials(user_id, password, role):
    db_path = os.path.abspath("scms.db")  # Get absolute path
    conn = sqlite3.connect(db_path)

    cursor = conn.cursor()

    if role == "student":
        cursor.execute("SELECT * FROM students WHERE student_id = ? AND password = ?", (user_id, password))
    elif role == "faculty":
        cursor.execute("SELECT * FROM faculty WHERE faculty_id = ? AND password = ?", (user_id, password))
    elif role == "admin":
        cursor.execute("SELECT * FROM admin WHERE id = ? AND password = ?", (user_id, password))
    else:
        return None

    user = cursor.fetchone()
    conn.close()
    return user

@app.route('/login', methods=['POST'])
def login():
    user_id = request.form['user_id']
    password = request.form['password']
    role = request.form['role']

    if check_credentials(user_id, password, role):
        session['user_id'] = user_id
        session['role'] = role
        
        if role == "student":
            return redirect(url_for('student_dashboard'))
        elif role == "faculty":
            return redirect(url_for('faculty_dashboard'))
        elif role == "admin":
            return redirect(url_for('admin_dashboard'))
    else:
        return "Invalid credentials. Try again."

@app.route('/student_dashboard')
def student_dashboard():
    if 'user_id' in session and session['role'] == 'student':
        return render_template("student_dashboard.html")
    else:
        return redirect(url_for('home'))
    
@app.route('/view_courses')
def view_courses():
    if 'user_id' not in session or session['role'] != 'student':
        return redirect(url_for('home'))

    student_id = session['user_id']
    db_path = os.path.abspath("scms.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT books.course_id, books.name, faculty.name AS instructor_name
    FROM borrows
    JOIN books ON borrows.course_id = books.course_id
    JOIN faculty ON books.instructor = faculty.faculty_id
    WHERE borrows.student_id = ?
""", (student_id,))

    
    courses = cursor.fetchall()
    conn.close()

    return render_template("view_courses.html", courses=courses)

@app.route('/view_grades')
def view_grades():
    if 'user_id' not in session or session['role'] != 'student':
        return redirect(url_for('home'))

    student_id = session['user_id']
    db_path = os.path.abspath("scms.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT books.course_id, books.name, grades.grade 
        FROM grades 
        JOIN books ON grades.course_id = books.course_id 
        WHERE grades.student_id = ?
    """, (student_id,))

    grades = cursor.fetchall()
    conn.close()

    return render_template("view_grades.html", grades=grades)

@app.route('/view_attendance')
def view_attendance():
    if 'user_id' not in session or session['role'] != 'student':
        return redirect(url_for('home'))

    student_id = session['user_id']
    db_path = os.path.abspath("scms.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT books.course_id, books.name, attendance.date, attendance.status 
        FROM attendance 
        JOIN books ON attendance.course_id = books.course_id 
        WHERE attendance.student_id = ?
        ORDER BY attendance.date DESC
    """, (student_id,))

    attendance = cursor.fetchall()
    conn.close()

    return render_template("view_attendance.html", attendance=attendance)

@app.route('/view_profile')
def view_profile():
    if 'user_id' not in session or session['role'] != 'student':
        return redirect(url_for('home'))

    student_id = session['user_id']
    db_path = os.path.abspath("scms.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name, student_id, contact, academic_history 
        FROM students 
        WHERE student_id = ?
    """, (student_id,))

    student = cursor.fetchone()
    conn.close()

    if not student:
        return "Student profile not found.", 404

    return render_template("view_profile.html", student=student)

@app.route('/faculty_dashboard')
def faculty_dashboard():
    if 'user_id' in session and session['role'] == 'faculty':
        return render_template("faculty_dashboard.html")
    else:
        return redirect(url_for('home'))

@app.route('/faculty_profile')
def faculty_profile():
    if 'user_id' not in session or session['role'] != 'faculty':
        return redirect(url_for('home'))

    faculty_id = session['user_id']
    db_path = os.path.abspath("scms.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name, faculty_id, email 
        FROM faculty 
        WHERE faculty_id = ?
    """, (faculty_id,))

    faculty = cursor.fetchone()
    conn.close()

    if not faculty:
        return "Faculty profile not found.", 404

    return render_template("faculty_profile.html", faculty=faculty)

@app.route('/faculty_subjects')
def faculty_subjects():
    if 'user_id' not in session or session['role'] != 'faculty':
        return redirect(url_for('home'))

    faculty_id = session['user_id']
    db_path = os.path.abspath("scms.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT course_id, name 
        FROM books 
        WHERE instructor = ?
    """, (faculty_id,))

    subjects = cursor.fetchall()
    conn.close()

    return render_template("faculty_subjects.html", subjects=subjects)

@app.route('/view_subject/<subject_id>')
def view_subject(subject_id):
    # Check if the user is logged in and has a faculty role
    if 'user_id' not in session or session['role'] != 'faculty':
        return redirect(url_for('home'))  # Redirect to home if not logged in as faculty

    db_path = os.path.abspath("scms.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Fetch subject details based on the course_id (subject_id here)
    cursor.execute("""
        SELECT course_id, name, credits, schedule, instructor
        FROM books
        WHERE course_id = ?
    """, (subject_id,))  # Use course_id here instead of the id field

    subject = cursor.fetchone()

    # If subject not found
    if subject is None:
        return "Subject not found", 404

    # Fetch instructor name using the faculty_id from the 'faculty' table
    cursor.execute("""
        SELECT name FROM faculty WHERE faculty_id = ?
    """, (subject[4],))  # subject[4] is the instructor's faculty_id
    instructor = cursor.fetchone()

    # Close the connection to the database
    conn.close()

    if instructor:
        instructor_name = instructor[0]
    else:
        instructor_name = "Unknown Instructor"

    # Render the template and pass subject details to it
    return render_template("view_subject.html", subject=subject, instructor_name=instructor_name)

@app.route('/add_enrollment', methods=['GET', 'POST'])
def add_enrollment():
    if 'user_id' not in session or session['role'] != 'faculty':
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        student_id = request.form['student_id']
        course_id = request.form['course_id']
        enrollment_date = request.form['enrollment_date']
        
        try:
            db_path = os.path.abspath("scms.db")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if student and course exist
            cursor.execute("SELECT 1 FROM students WHERE student_id = ?", (student_id,))
            if not cursor.fetchone():
                return "Student not found", 400
                
            cursor.execute("SELECT 1 FROM books WHERE course_id = ?", (course_id,))
            if not cursor.fetchone():
                return "Course not found", 400
            
            # Insert new enrollment
            cursor.execute("""
                INSERT INTO borrows (student_id, course_id, enrollment_date)
                VALUES (?, ?, ?)
            """, (student_id, course_id, enrollment_date))
            
            conn.commit()
            conn.close()
            
            return redirect(url_for('faculty_dashboard'))
            
        except sqlite3.Error as e:
            return f"An error occurred: {str(e)}", 500
    
    return render_template("add_enrollment.html")

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user_id' in session and session['role'] == 'admin':
        return render_template("admin_dashboard.html")
    else:
        return redirect(url_for('home'))
    
@app.route('/view_students')
def view_students():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('home'))

    db_path = os.path.abspath("scms.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()

    conn.close()

    return render_template("view_students.html", students=students)

@app.route('/view_enrollments')
def view_enrollments():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('home'))

    db_path = os.path.abspath("scms.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    SELECT students.name, borrows.id, borrows.student_id, borrows.course_id, borrows.enrollment_date
    FROM borrows 
    JOIN students ON borrows.student_id = students.student_id
""")

    enrollments = cursor.fetchall()

    conn.close()

    return render_template("view_enrollments.html", enrollments=enrollments)

@app.route('/view_faculty')
def view_faculty():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('home'))

    db_path = os.path.abspath("scms.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Fetching all faculty records
    cursor.execute("SELECT * FROM faculty")
    faculty_list = cursor.fetchall()

    conn.close()

    return render_template("view_faculty.html", faculty_list=faculty_list)

@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if 'user_id' not in session or session['role'] not in ['admin', 'faculty']:
        return redirect(url_for('home'))

    if request.method == 'POST':
        name = request.form['name']
        student_id = request.form['student_id']
        contact = request.form['contact']
        academic_history = request.form['academic_history']
        password = request.form['password']

        # Connect to the database
        db_path = os.path.abspath("scms.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Insert new student into the students table
        cursor.execute("""
            INSERT INTO students (name, student_id, contact, academic_history, password)
            VALUES (?, ?, ?, ?, ?)
        """, (name, student_id, contact, academic_history, password))

        # Commit the transaction and close the connection
        conn.commit()
        conn.close()

        # Redirect to view students page or any other page after adding the student
        return redirect(url_for('view_students'))

    return render_template('add_student.html')

@app.route('/add_faculty', methods=['GET', 'POST'])
def add_faculty():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('home'))

    if request.method == 'POST':
        faculty_id = request.form['faculty_id']
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        # Connect to the database
        db_path = os.path.abspath("scms.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Insert the new faculty into the database
        cursor.execute("""
            INSERT INTO faculty (faculty_id, name, email, password) 
            VALUES (?, ?, ?, ?)
        """, (faculty_id, name, email, password))
        
        conn.commit()
        conn.close()

        # Redirect to the faculty list after adding the new faculty
        return redirect(url_for('view_faculty'))

    return render_template('add_faculty.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
