from flask import Flask, redirect, url_for, render_template, request, session, flash, jsonify
from datetime import timedelta
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()


app = Flask(__name__)
app.secret_key = "hello"

app.permanent_session_lifetime = timedelta(days=5)

# establish the connection

DB_USERNAME = os.getenv('DB_USERNAME')
DB_PASSWORD = os.getenv('DB_PASSWORD')
URI = os.getenv('URI')

driver = GraphDatabase.driver(uri=URI, auth=(DB_USERNAME, DB_PASSWORD))
driver_session = driver.session()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/create", methods=["GET", "POST"])
def create_node():
    data = request.get_json()
    id = data["id"]
    name = data["name"]
    q1 = """create(n:Employee{name:$name, id:$id})"""
    employee_map = {"name": name, "id": id}
    try:
        driver_session.run(q1, employee_map)
        return f"employee node is created"
    except Exception as e:
        return "sth went wrong"


@app.route("/display", methods=["GET"])
def display_employees():
    q2 = "match(e:Employee) return e"
    try:
        results = driver_session.run(q2)
        data = results.data()
        print(data)
        return jsonify(data)
    except Exception as e:
        return "sth went wrong"


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # data = request.get_json()
        # email = data["email"]
        # password = data["password"]
        email = request.form["email"]
        password = request.form["password"]
        create_user_query = """create(u:User{email: $email, password: $password})"""
        check_user_exists_query = """match(u:User{email:$email}) return u.email"""
        try:
            found_user = driver_session.run(check_user_exists_query, {'email': email})
            user_data = found_user.data()
            if user_data:
                flash("user with given email already exists", "info")
                return render_template("register.html")
            else:
                driver_session.run(create_user_query, {'email': email, 'password': password})
                session["email"] = email
                return redirect(url_for("user"))

        except Exception as e:
            return "sth went wrong"
    else:
        return render_template("register.html")


@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        session.permanent = True
        # data = request.get_json()
        # email = data["email"]
        # password = data["password"]
        email = request.form["email"]
        password = request.form["password"]
        session["email"] = email

        find_user_query = '''match(u:User {email: $email, password: $password}) return u'''
        found_user = driver_session.run(find_user_query, {'email': email, 'password': password})
        found_user_data = found_user.data()

        if found_user_data:
            session["email"] = email
            return redirect(url_for("user"))
        else:
            flash("Login unsuccesful!")
            return render_template("login.html")
    else:
        if "email" in session:
            flash("Already logged in!")
            return redirect(url_for("user"))

        return render_template("login.html")


@app.route("/user", methods=["POST", "GET"])
def user():
    if "email" in session:
        email = session["email"]
        return render_template("user.html", email=email)
    return redirect(url_for("home"))


@app.route("/moviesearch", methods=["GET", "POST"])
def movies():
    if request.method == "GET":
        title = request.args.get('title')
        if title:
            title = f'(?i).*{title}.*'
            get_movies_query = '''match(m:Movie) WHERE m.title =~ $title return m.title, m.released, m.tagline'''
            found_movies = driver_session.run(get_movies_query, {'title': title})
            found_movies_data = found_movies.data()
            if found_movies_data:
                return render_template("movies.html", movies=found_movies_data)
            else:
                flash("There are no movies containing this phrase")
        return render_template("movies.html")


# @app.route("/other_users", methods=["GET"])
# def
#
# @app.route("/user", methods=["POST", "GET"])
# def user():
#     email = None
#     if "user" in session:
#         user = session["user"]
#         if request.method == "POST":
#             email = request.form["email"]
#             session["email"] = email
#             found_user = users.query.filter_by(name=user).first()
#             found_user.email = email
#             db.session.commit()
#
#         else:
#             if "email" in session:
#                 email = session["email"]
#         return render_template("user.html", email=email)
#     else:
#         return redirect(url_for("login"))


@app.route("/logout")
def logout():
    flash("You have been logged out", "info")
    session.pop("email", None)
    return redirect(url_for("login"))


def move_forward():
    print('moveeeeee')


if __name__ == "__main__":
    app.run(debug=True)

