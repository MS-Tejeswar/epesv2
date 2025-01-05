from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import mysql.connector
from flask_cors import CORS

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = 'your_secret_key'  # Replace with a strong secret key
CORS(app)  # Enable CORS for frontend-backend communication


# Database connection function
def get_db_connection():
    return mysql.connector.connect(
        host='sql110.infinityfree.com',
        user='if0_38043876',
        password='if0_38043876_epes',
        database='TdfUn0F2CX3M'
    )

@app.route('/')
def index():
    return render_template('select_role.html')

@app.route('/select_role', methods=['POST'])
def select_role():
    role = request.form['role']
    if role == 'manager':
        return redirect(url_for('login'))
    elif role == 'feedback_giver':
        return redirect(url_for('role_selection'))  # Go to role selection (parent/student)

@app.route('/role_selection', methods=['GET', 'POST'])
def role_selection():
    if request.method == 'POST':
        role_type = request.form['role_type']
        if role_type == 'parent':
            return redirect(url_for('parent_feedback_form'))
        elif role_type == 'student':
            return redirect(url_for('student_login_form'))

    return render_template('role_selection.html')

@app.route('/parent_feedback', methods=['GET', 'POST'])
def parent_feedback_form():
    session.clear()
    if request.method == 'POST':
        parent_name = request.form['parent_name']
        parent_number = request.form['parent_number']
        ward_name = request.form['ward_name']

        # Store parent data
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("INSERT INTO parents (parent_name, parent_number, ward_name) VALUES (%s, %s, %s)", 
                       (parent_name, parent_number, ward_name))
        db.commit()

        # Store parent ID in session (assuming you have the parent_id in your session after registration)
        cursor.execute("SELECT LAST_INSERT_ID()")
        parent_id = cursor.fetchone()[0]
        session['parent_id'] = parent_id
        session['parent_name'] = parent_name
        session['parent_number'] = parent_number
        session['ward_name'] = ward_name
        db.close()

        # Redirect to faculty list
        return redirect(url_for('faculty_list'))  # Faculty list page

    return render_template('parent_feedback_form.html')

    
@app.route('/faculty_list')
def faculty_list():
    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM faculty")
    faculties = cursor.fetchall()
    db.close()
    return render_template('faculty_list.html', faculties=faculties)



@app.route('/student_login', methods=['GET', 'POST'])
def student_login_form():
    session.clear()
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        if not email.endswith('@gitam.in'):
            return "Invalid email format", 400

        # Authenticate student
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT id, password FROM students WHERE email = %s", (email,))
        student = cursor.fetchone()
        db.close()

        if student and student[1]==password:
            session['student_id'] = student[0]
            session['email']=email
            return redirect(url_for('faculty_list'))
        
        return "Invalid credentials", 401
    
    return render_template('student_login_form.html')



@app.route('/feedback/<int:faculty_id>', methods=['GET', 'POST'])
def feedback(faculty_id):
    if request.method == 'POST':
        if 'parent_id' in session:
            competence = request.form['competence']
            attitude = request.form['attitude']
            task_resolution = request.form['task_resolution']
            patience_composure = request.form['patience_composure']
            availability = request.form['availability']
            subjective_feedback = request.form['subjective_feedback']

            # Assuming parent_id is stored in the session after registration
            parent_id = session.get('parent_id')
            name=session.get('parent_name')
            num=session.get('parent_number')
            ward=session.get('ward_name')
            # Insert feedback into parent_feedback table
            db = get_db_connection()
            cursor = db.cursor()
            cursor.execute(
                """
                INSERT INTO parent_feedback (parent_name, parent_number, ward_name, faculty_id, competence, attitude, task_resolution, patience_composure, availability, subjective_feedback)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    name,
                    num,
                    ward,
                    faculty_id,
                    competence,
                    attitude,
                    task_resolution,
                    patience_composure,
                    availability,
                    subjective_feedback
                )
            )
            db.commit()
            db.close()

            return redirect(url_for('success'))  # Redirect back to the faculty list after submission
        elif 'student_id' in session:
            competence = request.form['competence']
            attitude = request.form['attitude']
            task_resolution = request.form['task_resolution']
            patience_composure = request.form['patience_composure']
            availability = request.form['availability']
            subjective_feedback = request.form['subjective_feedback']

            # Assuming parent_id is stored in the session after registration
            email=session.get('email')
            
            # Insert feedback into parent_feedback table
            db = get_db_connection()
            cursor = db.cursor()
            cursor.execute(
                """
                INSERT INTO student_feedback (student_email, faculty_id, competence, attitude, task_resolution, patience_composure, availability, subjective_feedback)
                VALUES ( %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    email,
                    faculty_id,
                    competence,
                    attitude,
                    task_resolution,
                    patience_composure,
                    availability,
                    subjective_feedback
                )
            )
            db.commit()
            db.close()

            return redirect(url_for('success'))


    return render_template('feedback_form.html', faculty_id=faculty_id)

@app.route('/success',methods=['GET','POST'])
def success():
    return render_template('success.html')



@app.route('/employee_overview')
def employee_overview():
    """Render the employee overview page for the manager."""
    if 'manager_id' not in session:
        return redirect(url_for('login'))

    manager_id = session['manager_id']

    db = get_db_connection()
    cursor = db.cursor()

    # Fetch employees managed by the manager
    cursor.execute("SELECT id, name FROM faculty WHERE manager_id = %s", (manager_id,))
    employees = cursor.fetchall()

    db.close()
    return render_template('employee_overview.html', employees=employees)



@app.route('/employee_feedback/<int:employee_id>', methods=['GET'])
def employee_feedback(employee_id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)  # Enable dictionary mode for named keys

    # Query parent feedback
    cursor.execute("""
        SELECT parent_name, subjective_feedback 
        FROM parent_feedback 
        WHERE faculty_id = %s
    """, (employee_id,))
    parent_feedback = cursor.fetchall()

    # Query student feedback
    cursor.execute("""
        SELECT student_email, subjective_feedback 
        FROM student_feedback 
        WHERE faculty_id = %s
    """, (employee_id,))
    student_feedback = cursor.fetchall()

    db.close()

    return jsonify({
        'parent_feedback': parent_feedback,
        'student_feedback': student_feedback
    })




@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT id, password FROM managers WHERE username = %s", (username,))
        manager = cursor.fetchone()
        db.close()
        if manager and manager[1] == password:
            session['manager_id'] = manager[0]
            return redirect(url_for('employee_overview'))  # Redirect to new page
        return "Invalid credentials", 401
    return render_template('login.html')




@app.route('/dashboard')
def dashboard():
    if 'manager_id' not in session:
        return redirect(url_for('index'))

    manager_id = session['manager_id']

    db = get_db_connection()
    cursor = db.cursor()

    # Get all faculties managed by the logged-in manager
    cursor.execute("SELECT id, name FROM faculty WHERE manager_id = %s", (manager_id,))
    faculties = cursor.fetchall()

    # Retrieve summaries and adjectives for each faculty
    summaries = {}
    for faculty in faculties:
        faculty_id = faculty[0]
        
        # Get parent feedback summary
        cursor.execute("SELECT summary, competence_avg, attitude_avg, task_resolution_avg, patience_composure_avg, availability_avg FROM parent_feedback_summary WHERE faculty_id = %s", (faculty_id,))
        parent_summary_row = cursor.fetchone()

        # Get student feedback summary
        cursor.execute("SELECT summary, competence_avg, attitude_avg, task_resolution_avg, patience_composure_avg, availability_avg FROM student_feedback_summary WHERE faculty_id = %s", (faculty_id,))
        student_summary_row = cursor.fetchone()

        # Get adjectives
        cursor.execute("SELECT adjective_type, adjective, count FROM employee_adjectives WHERE faculty_id = %s", (faculty_id,))
        adjectives = cursor.fetchall()

        # Store data in the summaries dictionary
        summaries[faculty_id] = {
            'name': faculty[1],
            'parent_summary': parent_summary_row if parent_summary_row else None,
            'student_summary': student_summary_row if student_summary_row else None,
            'adjectives': adjectives
        }

    db.close()

    return render_template('dashboard_man.html', faculties=faculties, summaries=summaries)



@app.route('/logout')
def logout():
    session.pop('student_id', None)
    session.pop('parent_id', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
