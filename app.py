from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import requests
import csv
from collections import deque

app = Flask(__name__)
app.secret_key = 'your secret key'

MODEL_SERVICE_URL = os.environ.get("MODEL_HOST", "http://localhost:8081")

task_descriptions = deque()
additional_infos = deque()

@app.route("/login", methods=["GET", "POST"])
def login():
    global task_descriptions, additional_infos

    if request.method == "POST":
        user_id = request.form.get("user_id")
        with open('./data/users.csv', 'r') as file:
            reader = csv.reader(file, delimiter=';')
            next(reader)  # Skip the header row
            for row in reader:
                if row[0] == user_id:
                    session["user_id"] = user_id
                    session["task_description_file"] = row[1].strip()
                    session["additional_info_file"] = row[2].strip()
                    
                    # Pick appropriate user-files
                    with open(session["task_description_file"], 'r') as file:
                        reader = csv.reader(file, delimiter=';')
                        task_descriptions = deque(list(reader))

                    with open(session["additional_info_file"], 'r') as file:
                        reader = csv.reader(file, delimiter=';')
                        additional_infos = deque(list(reader))

                    return redirect(url_for("index"))
        return "User not found", 400
    return render_template("login.html")

@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))
    with open(session["task_description_file"], 'r') as file:
        reader = csv.reader(file, delimiter=';')
        task_description = next(reader)[0]
    with open(session["additional_info_file"], 'r') as file:
        reader = csv.reader(file, delimiter=';')
        additional_info = next(reader)[0]
    return render_template("index.html", task_description=task_description, additional_info=additional_info)

@app.route("/next_task")
def next_task():
    task_descriptions.rotate(-1)
    print(task_descriptions)
    return jsonify({"task_description": task_descriptions[0][0]})

@app.route("/next_info")
def next_info():
    additional_infos.rotate(-1)
    return jsonify({"additional_info": additional_infos[0][0]})

@app.route("/submit", methods=["POST"])
def submit():
    review = request.form.get("review") 
    if not review:
        return jsonify({"error": "Review is empty."}), 400
    
    task_description = task_descriptions[0][0]
    user_id = session["user_id"]
    output_file = f'./data/user_data/{user_id}/user_output.csv'

    # Read existing records
    with open(output_file, 'r', newline='') as file:
        reader = csv.reader(file)
        records = list(reader)

    # Update the relevant record
    for record in records:
        if record[0] == user_id and record[1] == task_description:
            record[2] = review
            break
    else:
        # If no existing record was found, add a new one
        records.append([user_id, task_description, review])

    # Write all records back to the file
    with open(output_file, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(records)
    
    return jsonify({"message": "Success"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)