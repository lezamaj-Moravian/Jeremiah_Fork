from flask import Flask, jsonify, render_template
from collector import init_db, add_example_data
from database import get_athletes_activities

app = Flask(__name__)

@app.route("/")
def website():
    return render_template("index.html")

@app.route("/data")
def get_data():
    try:
        data = get_athletes_activities()
        return jsonify(data)
    except Exception as e:
        return jsonify({"Error": str(e)}), 500

if __name__ == "__main__":
    init_db()
    add_example_data()
    print("Database started")
    app.run(debug=True,port=8000)
