from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import pymssql
from collections import deque

app = Flask(__name__)
app.secret_key = 'your secret key'

CC23_DB_USERNAME = os.getenv('CC23_DB_USERNAME')
CC23_DB_PASSWORD = os.getenv('CC23_DB_PASSWORD')

# Connect to SQL Server
conn = pymssql.connect(server='cc23-team4-5-mssql-server.database.windows.net', user='{}@cc23-team4-5-mssql-server'.format(CC23_DB_USERNAME), password=CC23_DB_PASSWORD, database='cc23-team4-5-mssql-database')
cursor = conn.cursor()

MODEL_SERVICE_URL = os.environ.get("MODEL_HOST", "http://localhost:8081")
MICROTASK_NAMES = deque([("Extract"), ("Produce"), ("Verify")])

task_descriptions = deque()
additional_infos = deque()

user_answers = {}

@app.route("/login", methods=["GET", "POST"])
def login():
    global task_descriptions, additional_infos
    
    task_descriptions.clear()
    additional_infos.clear()

    if request.method == "POST":
        user_id = request.form.get("user_id")

        cursor.execute("SELECT user_id FROM users WHERE user_id=%s", user_id)
        user = cursor.fetchone()    
        
        if user:
            session["user_id"] = user[0]

            cursor.execute("SELECT task_id, user_id, task_description FROM task_descriptions WHERE user_id=%s", user_id)
            task_descriptions.extend(cursor.fetchall())
            cursor.execute("SELECT info_id, user_id, additional_info FROM additional_info WHERE user_id=%s", user_id)
            additional_infos.extend(cursor.fetchall())

            cursor.execute("SELECT task_id, user_id, user_answer FROM user_answers WHERE user_id=%s", user_id)
            answers = cursor.fetchall()

            # populate the user_answers dictionary with fetched data
            for answer in answers:
                user_answers[answer[0]] = answer[2]

            return redirect(url_for("index"))
        return "User not found", 400
    return render_template("login.html")

@app.route("/logout")
def logout():
    user_id = session.get("user_id")
    cursor.execute("SELECT questionare_url FROM users WHERE user_id=%s", user_id)
    url = cursor.fetchone()[0]
    session.clear()  # Clear the session
    return render_template("logout.html", user_id=user_id, url=url)

@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    print('Microtask names: ', MICROTASK_NAMES)
    print('-' * 50)
    print('Task descriptions: ', task_descriptions)
    print('-' * 50)
    print('Additional infos: ', additional_infos)

    microtask_name = MICROTASK_NAMES[0]
    task_id = task_descriptions[0][0]
    task_description = task_descriptions[0][2]
    additional_info = additional_infos[0][2]
    user_answer = user_answers.get(task_id, '')

    return render_template("index.html", task_description=task_description, additional_info=additional_info, microtask_name=microtask_name, user_answer=user_answer)

@app.route("/next_task")
def next_task():
    task_descriptions.rotate(-1)
    additional_infos.rotate(-1)
    MICROTASK_NAMES.rotate(-1)
    task_id = task_descriptions[0][0]
    user_answer = user_answers.get(task_id, '')
    print(task_descriptions[0][2], additional_infos[0][2], MICROTASK_NAMES[0])
    return jsonify({"task_description": task_descriptions[0][2], 
                    "additional_info": additional_infos[0][2],
                    "microtask_name": MICROTASK_NAMES[0],
                    "user_answer": user_answer})

@app.route("/submit", methods=["POST"])
def submit():
    review = request.form.get("review") 
    if not review:
        return jsonify({"error": "Review is empty."}), 400

    user_id = session["user_id"]
    task_id = task_descriptions[0][0]

    cursor.execute("""
        MERGE INTO user_answers AS Target
        USING (SELECT %s as user_id, %s as task_id) AS Source
        ON Target.user_id = Source.user_id AND Target.task_id = Source.task_id
        WHEN MATCHED THEN
            UPDATE SET user_answer = %s
        WHEN NOT MATCHED THEN
            INSERT (user_id, task_id, user_answer) VALUES (Source.user_id, Source.task_id, %s);
        """, (user_id, task_id, review, review))
    conn.commit()

    return jsonify({"message": "Success"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
