from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

def get_db():
    conn = sqlite3.connect("students.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS grades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        score INTEGER NOT NULL,
        grade TEXT NOT NULL,
        FOREIGN KEY(student_id) REFERENCES students(id)
    )
    """)

    conn.commit()
    conn.close()

init_db()

def calculate_grade(score):
    if 90 <= score <= 100:
        return "excellent"
    elif score >= 70:
        return "good"
    elif score >= 50:
        return "average"
    else:
        return "fail"

@app.route("/")
def home():

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM students
        ORDER BY last_name, first_name
    """)

    students = cursor.fetchall()

    conn.close()

    return render_template("index.html", students=students)


@app.route("/add", methods=["GET", "POST"])
def add():

    if request.method == "POST":

        first_name = request.form["first_name"]
        last_name = request.form["last_name"]

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO students(first_name, last_name)
            VALUES (?, ?)
        """, (first_name, last_name))

        conn.commit()
        conn.close()

        return redirect(url_for("home"))

    return render_template("add.html")


@app.route("/add_grade", methods=["GET", "POST"])
def add_grade():


    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()

    if request.method == "POST":

        student_id = int(request.form["student_id"])
        score = int(request.form["score"])

        grade = calculate_grade(score)

        cursor.execute("""
            INSERT INTO grades(student_id, score, grade)
            VALUES (?, ?, ?)
        """, (student_id, score, grade))

        conn.commit()
        conn.close()

        return redirect(url_for("home"))

    conn.close()

    return render_template("add_grade.html", students=students)


@app.route("/search", methods=["GET", "POST"])
def search():

    student = None
    grades = []

    if request.method == "POST":

        data = request.form["data"]

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM students
            WHERE first_name = ? OR last_name = ?
        """, (data, data))

        student = cursor.fetchone()

        if student:

            cursor.execute("""
                SELECT *
                FROM grades
                WHERE student_id = ?
                ORDER BY score DESC
            """, (student["id"],))

            grades = cursor.fetchall()

        conn.close()

    return render_template(
        "search.html",
        student=student,
        grades=grades
    )


@app.route("/stats")
def stats():


    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM grades
        WHERE grade='fail'
    """)
    fails = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM grades
        WHERE grade='excellent'
    """)
    excellents = cursor.fetchone()[0]

    cursor.execute("""
        SELECT AVG(score)
        FROM grades
    """)
    avg = cursor.fetchone()[0]

    if avg is None:
        avg = 0

    cursor.execute("""
        SELECT
            students.first_name,
            students.last_name,
            grades.score
        FROM grades
        JOIN students
            ON students.id = grades.student_id
        ORDER BY grades.score DESC
        LIMIT 3
    """)

    top3 = cursor.fetchall()

    conn.close()

    return render_template(
        "stats.html",
        excellent=excellents,
        fail=fails,
        avg=round(avg, 2),
        top3=top3
    )


if __name__ == "__main__":
    app.run(debug=True)
