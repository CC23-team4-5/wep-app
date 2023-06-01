from flask import Flask, render_template, request, jsonify
import os
import requests
import csv

app = Flask(__name__)

MODEL_SERVICE_URL = os.environ.get("MODEL_HOST", "http://localhost:8081")

@app.route("/")
def index():
    with open('./data/task_description.csv', 'r') as file:
        reader = csv.reader(file, delimiter=';')
        task_description = next(reader)[0]

    with open('./data/additional_info.csv', 'r') as file:
        reader = csv.reader(file, delimiter=';')
        additional_info = next(reader)[0]

    return render_template("index.html", task_description=task_description, additional_info=additional_info)


@app.route("/analyze", methods=["POST"])
def analyze():
    
    review = request.form.get("review")
    print(cookie2dict('some cookie=true; some_other_cookie=false').ToDict())
    if not review:
        return jsonify({"error": "Review is empty."}), 400

    try:
        headers = {"accept": "application/json"}
        payload = {"text": review}
        response = requests.post(f"{MODEL_SERVICE_URL}/predict", json=payload, headers=headers)
        response.raise_for_status()
        prediction = response.json()["prediction"]
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500
    
    return jsonify({"prediction": prediction})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)