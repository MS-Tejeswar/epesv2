import mysql.connector
from transformers import BartForConditionalGeneration, BartTokenizer

# Initialize BART model and tokenizer
tokenizer = BartTokenizer.from_pretrained('facebook/bart-large-cnn')
model = BartForConditionalGeneration.from_pretrained('facebook/bart-large-cnn')

# Database connection function
def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',  # Replace with your MySQL username
        password='user1234',  # Replace with your MySQL password
        database='epes'
    )

def summarize_feedback():
    db = get_db_connection()
    cursor = db.cursor()

    # Get all faculties (employees)
    cursor.execute("SELECT id FROM faculty")
    faculties = cursor.fetchall()

    for faculty in faculties:
        faculty_id = faculty[0]

        # Get parent feedbacks for the specified faculty
        cursor.execute("SELECT competence, attitude, task_resolution, patience_composure, availability, subjective_feedback FROM parent_feedback WHERE faculty_id = %s", (faculty_id,))
        parent_feedbacks = cursor.fetchall()

        # Get student feedbacks for the specified faculty
        cursor.execute("SELECT competence, attitude, task_resolution, patience_composure, availability, subjective_feedback FROM student_feedback WHERE faculty_id = %s", (faculty_id,))
        student_feedbacks = cursor.fetchall()

        # Summarize parent feedbacks using BART
        if parent_feedbacks:
            parent_feedback_text = " ".join([feedback[5] for feedback in parent_feedbacks])  # Only subjective feedback
            print(faculty_id, parent_feedback_text)
            parent_inputs = tokenizer.encode(parent_feedback_text, return_tensors='pt', max_length=1024, truncation=True)
            parent_summary_ids = model.generate(parent_inputs, max_length=150, min_length=30, length_penalty=2.0, num_beams=4, early_stopping=True)
            parent_summary = tokenizer.decode(parent_summary_ids[0], skip_special_tokens=True)
            print(parent_summary)
            # Calculate average of the 6 parameters for parent feedback
            parent_scores = [feedback[:5] for feedback in parent_feedbacks]
            parent_averages = [sum(score) / len(score) for score in zip(*parent_scores)]  # Calculate averages for each parameter

        else:
            parent_summary = "No feedback available."
            parent_averages = [None] * 5  # No data for averages

        # Summarize student feedbacks using BART
        if student_feedbacks:
            student_feedback_text = " ".join([feedback[5] for feedback in student_feedbacks])  # Only subjective feedback
            student_inputs = tokenizer.encode(student_feedback_text, return_tensors='pt', max_length=1024, truncation=True)
            student_summary_ids = model.generate(student_inputs, max_length=150, min_length=30, length_penalty=2.0, num_beams=4, early_stopping=True)
            student_summary = tokenizer.decode(student_summary_ids[0], skip_special_tokens=True)
            
            # Calculate average of the 6 parameters for student feedback
            student_scores = [feedback[:5] for feedback in student_feedbacks]
            student_averages = [sum(score) / len(score) for score in zip(*student_scores)]  # Calculate averages for each parameter

        else:
            student_summary = "No feedback available."
            student_averages = [None] * 5  # No data for averages

        # Insert or update parent feedback summary in the database
        cursor.execute("""
            INSERT INTO parent_feedback_summary (faculty_id, summary, competence_avg, attitude_avg, task_resolution_avg, patience_composure_avg, availability_avg)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                summary = VALUES(summary),
                competence_avg = VALUES(competence_avg),
                attitude_avg = VALUES(attitude_avg),
                task_resolution_avg = VALUES(task_resolution_avg),
                patience_composure_avg = VALUES(patience_composure_avg),
                availability_avg = VALUES(availability_avg)
        """, (
            faculty_id, 
            parent_summary, 
            parent_averages[0], 
            parent_averages[1], 
            parent_averages[2], 
            parent_averages[3], 
            parent_averages[4]
        ))

        # Insert or update student feedback summary in the database
        cursor.execute("""
            INSERT INTO student_feedback_summary (faculty_id, summary, competence_avg, attitude_avg, task_resolution_avg, patience_composure_avg, availability_avg)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                summary = VALUES(summary),
                competence_avg = VALUES(competence_avg),
                attitude_avg = VALUES(attitude_avg),
                task_resolution_avg = VALUES(task_resolution_avg),
                patience_composure_avg = VALUES(patience_composure_avg),
                availability_avg = VALUES(availability_avg)
        """, (
            faculty_id, 
            student_summary, 
            student_averages[0], 
            student_averages[1], 
            student_averages[2], 
            student_averages[3], 
            student_averages[4]
        ))

    db.commit()
    cursor.close()
    db.close()

if __name__ == '__main__':
    summarize_feedback()