from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import pymssql
import datetime
from collections import deque
from random import randint

app = Flask(__name__)
app.secret_key = "your secret key"

CC23_DB_USERNAME = os.getenv("CC23_DB_USERNAME")
CC23_DB_PASSWORD = os.getenv("CC23_DB_PASSWORD")
EXPERIMENT_TASK_NAME = os.getenv("EXPERIMENT_TASK_NAME")

# Connect to SQL Server
global conn, cursor


MODEL_SERVICE_URL = os.environ.get("MODEL_HOST", "http://localhost:8081")
MICROTASK_NAMES = deque([("Extract"), ("Produce"), ("Verify")])


# original_texts = deque()
additional_infos = deque()

original_texts = {}


def open_connections():
    global conn, cursor
    app.logger.debug("Opening MSSQL connection")
    conn = pymssql.connect(
        server="cc23-team4-5-mssql-server.database.windows.net",
        user="{}@cc23-team4-5-mssql-server".format(CC23_DB_USERNAME),
        password=CC23_DB_PASSWORD,
        database="cc23-team4-5-mssql-database",
    )

    cursor = conn.cursor()
    app.logger.debug("MSSQL connection is opened")


def close_connections():
    app.logger.debug("Closing MSSQL connection")
    cursor.close()
    conn.close()
    app.logger.debug("MSSQL connection is closed")


def clear_user_session():
    session.clear()
    app.logger.info("User session is cleared")


def read_original_texts():
    global original_texts
    app.logger.debug("Reading original texts")
    for i in range(1, 23):
        file_path = "./data/original_texts_verify_human/{}/original_text.txt".format(str(i))
        with open(file_path, "r") as file:
            original_texts[i] = file.read()

    app.logger.debug("Original texts are read")


@app.route("/extract")
def extract():
    app.logger.debug("Routing to Extract")
    return perform_task("extract")


@app.route("/produce")
def produce():
    app.logger.debug("Routing to Produce")
    return perform_task("produce")


@app.route("/verify")
def verify():
    app.logger.debug("Routing to Verify")
    return perform_task("verify")


def perform_task(task_name):
    global original_texts

    if "user_id" not in session:
        app.logger.debug("[perform_task] User not in session")
        return redirect(url_for("login"))

    app.logger.info(
        "[perform_task] User {} in session performing task {} on text {}".format(
            session["user_id"], task_name, session["text_id"]
        )
    )

    # Log entrance_timestamp
    entrance_timestamp = datetime.datetime.now()
    cursor.execute("UPDATE users SET entrance_timestamp=%s WHERE user_id=%s", (entrance_timestamp, session["user_id"]))
    conn.commit()
    app.logger.debug("[perform_task] entrance_timestamp: {}".format(entrance_timestamp))

    if task_name == "extract":
        # close_connections()
        app.logger.debug("[perform_task] template {}".format(task_name))
        return render_template(
            "extract.html",
            microtask_name=session["task_id"],
            original_text=original_texts[session["text_id"]],
            user_answer="User Answer",
        )
    elif task_name == "produce":
        # close_connections()
        app.logger.debug("[perform_task] template {}".format(task_name))
        return render_template(
            "produce.html",
            microtask_name=session["task_id"],
            original_text=original_texts[session["text_id"]],
            key_features=session["key_features"],
            user_answer="User Answer",
        )
    else:
        # close_connections()
        app.logger.debug("[perform_task] template {}".format(task_name))
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
        app.logger.debug("UserID {} provided".format(user_id))

        cursor.execute(
            "SELECT text_id FROM users WHERE user_id IS NULL AND task_id=%s", EXPERIMENT_TASK_NAME,
        )
        data = cursor.fetchone()
        app.logger.debug("Fetched text_id: {}".format(data[0]))

        cursor.execute(
            "UPDATE users SET user_id=%s WHERE text_id=%s AND task_id=%s", (user_id, data[0], EXPERIMENT_TASK_NAME)
        )
        conn.commit()
        app.logger.info("User {} saved as the candidate for task {} on text {}".format(user_id, EXPERIMENT_TASK_NAME ,data[0]))


        if data:
            app.logger.info("User {} logged in".format(user_id))

            session["user_id"] = user_id
            session["task_id"] = EXPERIMENT_TASK_NAME
            session["text_id"] = data[0]

            if session["task_id"] == "produce" or session["task_id"] == "verify":
                # Fetch Key Features
                cursor.execute(
                    "SELECT kf_id, key_features FROM key_features WHERE text_id=%s",
                    session["text_id"],
                )

                res = cursor.fetchone()
                app.logger.debug("Fetched Key Features: {}".format(res))
                session["kf_id"] = res[0]
                session["key_features"] = res[1]

            if session["task_id"] == "verify":
                # Fetch Summaries
                cursor.execute(
                    "SELECT summary_id, summary FROM summaries WHERE kf_id=%s",
                    session["kf_id"],
                )

                res = cursor.fetchone()
                app.logger.debug("Fetched Summary: {}".format(res[0]))
                session["summary_id"] = res[0]
                session["summary"] = res[1]

            if "consent_given" not in session:
                app.logger.info("Redirecting to consent form")
                return redirect(url_for("consent_form"))

            return redirect(url_for(session["task_id"]))
        app.logger.error("User {} not found".format(user_id))
        return "User not found", 400
    return render_template("login.html", task_name=EXPERIMENT_TASK_NAME)


@app.route("/early_exit")
def early_exit():
    # open_connections()
    user_id = session["user_id"]
    cursor.execute("SELECT early_exit_code FROM users WHERE user_id=%s", user_id)
    early_exit_code = cursor.fetchone()[0]

    # Log exit_timestamp
    exit_timestamp = datetime.datetime.now()
    cursor.execute("UPDATE users SET exit_timestamp=%s WHERE user_id=%s", (exit_timestamp, session["user_id"]))
    conn.commit()
    app.logger.debug("[early_exit] exit_timestamp: {}".format(exit_timestamp))

    clear_user_session()
    # close_connections()
    app.logger.info("User {} logged out".format(user_id))
    return render_template("early_exit.html", user_id=user_id, early_exit_code=early_exit_code)

@app.route("/wyloguj_user")
def logout():
    user_id = session["user_id"]
    cursor.execute("SELECT questionare_url FROM users WHERE user_id=%s", user_id)
    url = cursor.fetchone()[0]
    clear_user_session()
    # close_connections()
    app.logger.info("User {} logged out".format(user_id))
    return render_template("logout.html", user_id=user_id, url=url)


def remove_user_data(user_id):
    app.logger.warning("Removing user data for user {}".format(user_id))
    cursor.execute("DELETE FROM key_features WHERE user_id=%s", user_id)
    cursor.execute("DELETE FROM summaries WHERE user_id=%s", user_id)
    cursor.execute("DELETE FROM validations WHERE user_id=%s", user_id)
    conn.commit()
    app.logger.warning("User data for user {} removed".format(user_id))


@app.route("/revoke-consent")
def revoke_consent():
    # open_connections()
    # Store the user_id to clear session later
    user_id = session["user_id"]

    app.logger.warning("User {} removed consent".format(user_id))
    cursor.execute(
        "UPDATE users SET consent_given = 0 WHERE user_id=%s", session["user_id"]
    )
    conn.commit()

    cursor.execute("SELECT revoke_consent_code FROM users WHERE user_id=%s", user_id)
    revoke_consent_code = cursor.fetchone()[0]
    app.logger.debug("Revoke consent code: {}".format(revoke_consent_code))

    # Log exit_timestamp
    exit_timestamp = datetime.datetime.now()
    cursor.execute("UPDATE users SET exit_timestamp=%s WHERE user_id=%s", (exit_timestamp, session["user_id"]))
    conn.commit()
    app.logger.debug("[revoke_consent] exit_timestamp: {}".format(exit_timestamp))

    remove_user_data(session["user_id"])
    clear_user_session()
    # close_connections()
    return render_template(
        "revoked.html", user_id=user_id, revoke_consent_code=revoke_consent_code
    )


@app.route("/give-consent")
def give_consent():
    cursor.execute(
        "UPDATE users SET consent_given = 1 WHERE user_id=%s", session["user_id"]
    )
    conn.commit()
    app.logger.info("User {} gave consent".format(session["user_id"]))
    return redirect(url_for(session["task_id"]))


@app.route("/consent-form", methods=["GET", "POST"])
def consent_form():
    if request.method == "POST":
        app.logger.debug("Consent form submitted")
        # handle the post request here, such as saving consent form data
        return redirect(
            url_for("task_route")
        )  # redirect to the first task after consent
    return render_template("consent_form.html")


@app.route("/")
def index():
    app.logger.info("{} App Started!".format(EXPERIMENT_TASK_NAME))
    # open_connections()
    read_original_texts()

    if "user_id" not in session:
        app.logger.debug("User redirected to login page")
        return redirect(url_for("login"))

    return redirect(url_for(session["task_id"]))


@app.route("/next_task")
def next_task():
    original_texts.rotate(-1)
    additional_infos.rotate(-1)
    MICROTASK_NAMES.rotate(-1)
    task_id = original_texts[0][0]
    user_answer = user_answers.get(task_id, "")
    # print(original_texts[0][2], additional_infos[0][2], MICROTASK_NAMES[0])
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
    app.logger.debug("Received POST request to /submit")
    # open_connections()
    answer = request.form.get("answer")
    if not answer:
        app.logger.warning("Answer not provided.")
        return jsonify({"error": "Answer not provided."}), 401
    app.logger.info("User {} submitted answer {}".format(session["user_id"], answer))

    # Log exit_timestamp
    exit_timestamp = datetime.datetime.now()
    cursor.execute("UPDATE users SET exit_timestamp=%s WHERE user_id=%s", (exit_timestamp, session["user_id"]))
    conn.commit()
    app.logger.debug("[submit] exit_timestamp: {}".format(exit_timestamp))

    if session["task_id"] == "extract":
        app.logger.debug("Merging into key_features...")
        app.logger.warning((session["text_id"], session["user_id"], answer, answer))
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
        app.logger.debug("Merge into key_features completed!")
    elif session["task_id"] == "produce":
        app.logger.debug("Merging into summaries...")
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
        app.logger.debug("Merge into summaries completed!")
    elif session["task_id"] == "verify":
        app.logger.debug("Merging into validations...")
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
        app.logger.debug("Merge into validations completed!")
    else:
        return jsonify({"error": "task_id not recognized."}), 402

    return jsonify({"message": "Success"}), 200


if __name__ == "__main__":
    open_connections()
    app.run(host="0.0.0.0", port=8080, debug=True)
