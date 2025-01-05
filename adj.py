import mysql
import spacy
from flask import Flask, jsonify
from collections import Counter
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk

# Initialize Flask app
app = Flask(__name__)

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Download VADER lexicon for sentiment analysis
nltk.download('vader_lexicon')
sentiment_analyzer = SentimentIntensityAnalyzer()

# Database connection
def get_connection():
    return mysql.connector.connect(
        host='sql110.infinityfree.com',
        user='if0_38043876',
        password='if0_38043876_epes',
        database='TdfUn0F2CX3M'
    )

# Extract adjectives from text
def extract_adjectives(text):
    doc = nlp(text)
    
    return [token.text for token in doc if token.pos_ == "ADJ"]

# Categorize adjectives into positive and negative using VADER sentiment analysis
def categorize_adjectives(adjectives, text):
    positive = []
    negative = []
    tokens = nlp(text)

    for token in tokens:
        # Check if the token is an adjective
        if token.pos_ == "ADJ":
            # Look for negation words in a 2-word window before the adjective
            negation = [t.text.lower() for t in token.lefts if t.text.lower() in ["not", "never", "no"]]
            
            sentiment_score = sentiment_analyzer.polarity_scores(token.text)
            if negation:
                # Reverse sentiment if negation is found
                sentiment_score['compound'] = -sentiment_score['compound']
                # Combine negation with the adjective to form the full phrase
                phrase = f"{' '.join(negation)} {token.text}"
            else:
                # If no negation, the phrase is just the adjective
                phrase = token.text

            # Categorize the phrase
            if sentiment_score['compound'] > 0.05:
                positive.append(phrase)
            elif sentiment_score['compound'] < -0.05:
                negative.append(phrase)

    return positive, negative



# Store results in a new table
def store_adjective_counts(faculty_id, positive_counts, negative_counts):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            # Ensure table exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS employee_adjectives (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    faculty_id INT,
                    adjective_type VARCHAR(255),
                    adjective VARCHAR(255),
                    count INT,
                    UNIQUE (faculty_id, adjective_type, adjective), -- Ensure uniqueness
                    FOREIGN KEY (faculty_id) REFERENCES faculty(id)
                )""")

            # Insert or update positive adjectives
            for adjective, count in positive_counts.items():
                cursor.execute(
                    """INSERT INTO employee_adjectives (faculty_id, adjective_type, adjective, count)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE count = count + VALUES(count)""",
                    (faculty_id, "positive", adjective, count)
                )

            # Insert or update negative adjectives
            for adjective, count in negative_counts.items():
                cursor.execute(
                    """INSERT INTO employee_adjectives (faculty_id, adjective_type, adjective, count)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE count = count + VALUES(count)""",
                    (faculty_id, "negative", adjective, count)
                )

            connection.commit()
    finally:
        connection.close()


@app.route("/highlight-feedback", methods=["GET"])
def highlight_feedback():
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            # Fetch only unprocessed feedback
            cursor.execute("SELECT faculty_id, subjective_feedback FROM parent_feedback WHERE is_processed = 0")
            parent_feedback = cursor.fetchall()

            cursor.execute("SELECT faculty_id, subjective_feedback FROM student_feedback WHERE is_processed = 0")
            student_feedback = cursor.fetchall()
            if student_feedback==():
                student_feedback=[]
            if parent_feedback==():
                parent_feedback=[]
        # Combine feedback into a dictionary by faculty_id
        feedback_by_faculty = {}
        for row in parent_feedback + student_feedback:
            faculty_id = row['faculty_id']
            feedback = row['subjective_feedback']
            if faculty_id not in feedback_by_faculty:
                feedback_by_faculty[faculty_id] = []
            if feedback:
                feedback_by_faculty[faculty_id].append(feedback)

        # Process feedback for each faculty
        for faculty_id, feedback_list in feedback_by_faculty.items():
            positive_adjectives = []
            negative_adjectives = []

            for feedback in feedback_list:
                adjectives = extract_adjectives(feedback)
                positive, negative = categorize_adjectives(adjectives, feedback)
                positive_adjectives.extend(positive)
                negative_adjectives.extend(negative)

            # Count frequency of each adjective
            positive_counts = Counter(positive_adjectives)
            negative_counts = Counter(negative_adjectives)

            # Store results in the database
            store_adjective_counts(faculty_id, positive_counts, negative_counts)

        # Mark feedback as processed
        with connection.cursor() as cursor:
            cursor.execute("UPDATE parent_feedback SET is_processed = 1 WHERE is_processed = 0")
            cursor.execute("UPDATE student_feedback SET is_processed = 1 WHERE is_processed = 0")
            connection.commit()

        return jsonify({"message": "Adjective counts processed and stored successfully."})

    finally:
        connection.close()

if __name__ == "__main__":
    app.run(debug=True)
