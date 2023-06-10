from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import pymssql
from collections import deque
from random import randint

app = Flask(__name__)
app.secret_key = "your secret key"

CC23_DB_USERNAME = os.getenv("CC23_DB_USERNAME")
CC23_DB_PASSWORD = os.getenv("CC23_DB_PASSWORD")

# Connect to SQL Server
conn = pymssql.connect(
    server="cc23-team4-5-mssql-server.database.windows.net",
    user="{}@cc23-team4-5-mssql-server".format(CC23_DB_USERNAME),
    password=CC23_DB_PASSWORD,
    database="cc23-team4-5-mssql-database",
)
cursor = conn.cursor()

MODEL_SERVICE_URL = os.environ.get("MODEL_HOST", "http://localhost:8081")
MICROTASK_NAMES = deque([("Extract"), ("Produce"), ("Verify")])


# original_texts = deque()
additional_infos = deque()

original_texts = {}


def read_original_texts():
    global original_texts

    for i in range(1, 23):
        file_path = "./data/original_texts/{}/original_text.txt".format(str(i))
        with open(file_path, "r") as file:
            original_texts[i] = file.read()


@app.route("/extract")
def extract():
    return perform_task("Extract")


@app.route("/produce")
def produce():
    return perform_task("Produce")


@app.route("/verify")
def verify():
    return perform_task("Verify")


def perform_task(task_name):
    global original_texts

    if "user_id" not in session:
        return redirect(url_for("login"))

    if task_name == "Extract":
        return render_template(
            "extract.html",
            microtask_name=session["task_id"],
            original_text=original_texts[session["text_id"]],
            user_answer="User Answer",
        )
    elif task_name == "Produce":
        return render_template(
            "produce.html",
            microtask_name=session["task_id"],
            original_text=original_texts[session["text_id"]],
            key_features=session["key_features"],
            user_answer="User Answer",
        )
    else:
        return render_template(
            "verify.html",
            microtask_name=session["task_id"],
            original_text=original_texts[session["text_id"]],
            key_features=session["key_features"],
            summary=session["summary"],
            user_answer="User Answer",
        )


@app.route("/login", methods=["GET", "POST"])
def login():
    global original_texts

    if request.method == "POST":
        user_id = request.form.get("user_id")

        cursor.execute(
            "SELECT user_id, task_id, text_id FROM users WHERE user_id=%s", user_id
        )
        user = cursor.fetchone()

        if user:
            print("***************** USER *****************")
            print(user)

            session["user_id"] = user[0]
            session["task_id"] = user[1]
            session["text_id"] = user[2]

            # Fetch Key Features
            cursor.execute(
                "SELECT kf_id, key_features FROM key_features WHERE text_id=%s",
                session["text_id"],
            )
            res = cursor.fetchall()
            idx = randint(0, len(res) - 1)
            session["kf_id"] = res[idx][0]
            session["key_features"] = res[idx][1]

            # Fetch Summaries
            cursor.execute(
                "SELECT summary_id, summary FROM summaries WHERE kf_id=%s",
                session["kf_id"],
            )
            res = cursor.fetchall()
            idx = randint(0, len(res) - 1)
            session["summary_id"] = res[idx][0]
            session["summary"] = res[idx][1]

            if "consent_given" not in session:
                return redirect(url_for("consent_form"))

            return redirect(url_for(session["task_id"]))

        return "User not found", 400
    return render_template("login.html")


@app.route("/logout")
def logout():
    user_id = session.get("user_id")
    cursor.execute("SELECT questionare_url FROM users WHERE user_id=%s", user_id)
    url = cursor.fetchone()[0]
    session.clear()  # Clear the session
    return render_template("logout.html", user_id=user_id, url=url)


def remove_user_data(user_id):
    cursor.execute("DELETE FROM key_features WHERE user_id=%s", user_id)
    cursor.execute("DELETE FROM summaries WHERE user_id=%s", user_id)
    cursor.execute("DELETE FROM validations WHERE user_id=%s", user_id)
    conn.commit()


@app.route("/revoke-consent")
def revoke_consent():
    # Store the user_id to clear session later
    user_id = session["user_id"]

    cursor.execute(
        "UPDATE users SET consent_given = 0 WHERE user_id=%s", session["user_id"]
    )
    conn.commit()
    
    remove_user_data(session["user_id"])
    session.clear()

    return render_template("revoked.html", user_id=user_id)


@app.route("/give-consent")
def give_consent():
    cursor.execute(
        "UPDATE users SET consent_given = 1 WHERE user_id=%s", session["user_id"]
    )
    conn.commit()
    return redirect(url_for(session["task_id"]))


@app.route("/consent-form", methods=["GET", "POST"])
def consent_form():
    if request.method == "POST":
        # handle the post request here, such as saving consent form data
        return redirect(
            url_for("task_route")
        )  # redirect to the first task after consent
    return render_template("consent_form.html")


@app.route("/")
def index():
    read_original_texts()

    if "user_id" not in session:
        return redirect(url_for("login"))

    return redirect(url_for(session["task_id"]))


@app.route("/next_task")
def next_task():
    original_texts.rotate(-1)
    additional_infos.rotate(-1)
    MICROTASK_NAMES.rotate(-1)
    task_id = original_texts[0][0]
    user_answer = user_answers.get(task_id, "")
    print(original_texts[0][2], additional_infos[0][2], MICROTASK_NAMES[0])
    return jsonify(
        {
            "task_description": original_texts[0][2],
            "additional_info": additional_infos[0][2],
            "microtask_name": MICROTASK_NAMES[0],
            "user_answer": user_answer,
        }
    )


@app.route("/submit", methods=["POST"])
def submit():
    answer = request.form.get("answer")
    if not answer:
        return jsonify({"error": "Answer not provided."}), 401

    print("============ ANSWER ============")
    print(answer)
    print(session["task_id"])

    if session["task_id"] == "extract":
        cursor.execute(
            """
            MERGE INTO key_features AS Target
            USING (SELECT %s as text_id, %s as user_id) AS Source
            ON Target.text_id = Source.text_id AND Target.user_id = Source.user_id 
            WHEN MATCHED THEN
                UPDATE SET key_features = %s
            WHEN NOT MATCHED THEN
                INSERT (text_id, user_id, key_features) VALUES (Source.text_id, Source.user_id, %s);
            """,
            (session["text_id"], session["user_id"], answer, answer),
        )
        conn.commit()
    elif session["task_id"] == "produce":
        cursor.execute(
            """
            MERGE INTO summaries AS Target
            USING (SELECT %s as text_id, %s as user_id, %s as kf_id) AS Source
            ON Target.text_id = Source.text_id AND Target.user_id = Source.user_id AND Target.kf_id = Source.kf_id
            WHEN MATCHED THEN
                UPDATE SET summary = %s
            WHEN NOT MATCHED THEN
                INSERT (text_id, user_id, kf_id, summary) VALUES (Source.text_id, Source.user_id, Source.kf_id, %s);
            """,
            (session["text_id"], session["user_id"], session["kf_id"], answer, answer),
        )
        conn.commit()
    elif session["task_id"] == "verify":
        cursor.execute(
            """
            MERGE INTO validations AS Target
            USING (SELECT %s as text_id, %s as user_id, %s as kf_id, %s as summary_id) AS Source
            ON Target.text_id = Source.text_id AND Target.user_id = Source.user_id AND Target.kf_id = Source.kf_id AND Target.summary_id = Source.summary_id
            WHEN MATCHED THEN
                UPDATE SET validation = %s
            WHEN NOT MATCHED THEN
                INSERT (text_id, user_id, kf_id, summary_id, validation) VALUES (Source.text_id, Source.user_id, Source.kf_id, Source.summary_id, %s);
            """,
            (
                session["text_id"],
                session["user_id"],
                session["kf_id"],
                session["summary_id"],
                answer,
                answer,
            ),
        )
        conn.commit()
    else:
        return jsonify({"error": "task_id not recognized."}), 402

    return jsonify({"message": "Success"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
