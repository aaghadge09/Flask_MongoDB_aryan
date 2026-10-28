import json
import os

from flask import Flask, jsonify, redirect, render_template, request, url_for
from pymongo import MongoClient
from pymongo.errors import PyMongoError

app = Flask(__name__)
DATA_FILE = os.path.join(app.root_path, "data.json")


@app.route("/api")
def api():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, list):
            raise ValueError("data.json must contain a list.")

        return jsonify(data)

    except (OSError, json.JSONDecodeError, ValueError):
        app.logger.exception("Could not read data.json")
        return jsonify({"error": "Could not read the backend data file."}), 500


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        message = request.form.get("message", "").strip()

        if not name or not message:
            return render_template(
                "index.html",
                error="Please enter both your name and message.",
                name=name,
                message=message,
            ), 400

        mongo_uri = os.environ.get("MONGODB_URI")
        if not mongo_uri:
            return render_template(
                "index.html",
                error="MongoDB is not configured. Set MONGODB_URI and try again.",
                name=name,
                message=message,
            ), 500

        try:
            with MongoClient(mongo_uri, serverSelectionTimeoutMS=5000) as client:
                client.admin.command("ping")
                database_name = os.environ.get("MONGODB_DB", "assignment3")
                collection = client[database_name]["submissions"]
                collection.insert_one({"name": name, "message": message})

        except PyMongoError:
            app.logger.exception("MongoDB Atlas submission failed")
            return render_template(
                "index.html",
                error="Could not save your data. Check the MongoDB Atlas connection and try again.",
                name=name,
                message=message,
            ), 500

        return redirect(url_for("success"))

    return render_template("index.html")


@app.route("/success")
def success():
    return render_template("success.html")

@app.route("/todo", methods=["GET"])
def todo_page():
    return render_template("todo.html")

@app.route("/submittodoitem", methods=["POST"])
def submit_todo_item():
    item_name = request.form.get("itemName", "").strip()
    item_description = request.form.get("itemDescription", "").strip()

    if not item_name or not item_description:
        return render_template(
            "todo.html",
            error="Please provide both an item name and description."
        ), 400

    mongo_uri = os.environ.get("MONGODB_URI")
    if not mongo_uri:
        return render_template(
            "todo.html",
            error="MongoDB is not configured. Set MONGODB_URI and try again."
        ), 500

    try:
        with MongoClient(mongo_uri, serverSelectionTimeoutMS=5000) as client:
            client.admin.command("ping")
            database_name = os.environ.get("MONGODB_DB", "assignment3")
            client[database_name]["todo_items"].insert_one({
                "itemName": item_name,
                "itemDescription": item_description
            })
    except PyMongoError:
        app.logger.exception("Could not save the To-Do item")
        return render_template(
            "todo.html",
            error="Could not save the item. Check the MongoDB connection and try again."
        ), 500

    return redirect(url_for("success"))

if __name__ == "__main__":
    app.run(debug=True)
