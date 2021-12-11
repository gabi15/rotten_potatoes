from flask import Flask, redirect, url_for, render_template, request, session, flash, jsonify
from datetime import timedelta
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
import jyserver.Flask as jsf

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


@jsf.use(app)
class App:

    def flash_info(self, message):
        self.js.document.getElementById("info").style.visibility = "visible"
        self.js.document.getElementById("info_text").innerText = message

    def add_to_watched(self, title):
        id_unwatch_name = title+"_unwatch"
        id_rate_name = title + "_rate"
        self.js.document.getElementById(id_unwatch_name).disabled = False
        self.flash_info(f"Successfully rated {title}")
        rate = self.js.document.getElementById(id_rate_name).value
        rate = str(rate)
        rate = int(rate)
        email = session["email"]
        watched_query = """match (u:User{email:$email}),(m:Movie{title:$title}) merge (u)-[r:WATCHED]->(m) SET r.rate = $rate return type(r)""" #merge so i dont create node if already connected
        watched_map = {"email": email, "title": title, "rate": rate}
        try:
            create = driver_session.run(watched_query, watched_map)
            return create.data()
        except Exception as e:
            print("occured an exception")
            print(e)
            return "sth went wrong"

    def delete_from_watched(self, title):
        print('delete')
        id_unwatch_name = title+"_unwatch"
        self.js.document.getElementById(id_unwatch_name).disabled = True
        print(title)
        email = session["email"]
        watched_query = """match (u:User{email:$email})-[r:WATCHED]->(m:Movie{title:$title}) delete r"""
        watched_map = {"email": email, "title": title}
        try:
            driver_session.run(watched_query, watched_map)
            return f"employee node is created"
        except Exception as e:
            return "sth went wrong"

    def delete_from_want_to_watch(self, title, id_unwant_name, id_want_name):
        print('dont want to!')
        self.js.document.getElementById(id_unwant_name).disabled = True
        self.js.document.getElementById(id_want_name).disabled = False
        print(title)
        email = session["email"]
        want_query = """match (u:User{email:$email})-[r:WANT_TO_WATCH]->(m:Movie{title:$title}) delete r"""
        want_map = {"email": email, "title": title}
        try:
            driver_session.run(want_query, want_map)
            return f"employee node is created"
        except Exception as e:
            return "sth went wrong"

    def add_to_want_to_watch(self, title, id_unwant_name, id_want_name):
        print('want to!')
        self.js.document.getElementById(id_unwant_name).disabled = False
        self.js.document.getElementById(id_want_name).disabled = True
        print(title)
        email = session["email"]
        want_query = """match (u:User{email:$email}),(m:Movie{title:$title}) merge (u)-[r:WANT_TO_WATCH]->(m) return type(r)"""
        want_map = {"email": email, "title": title}
        try:
            driver_session.run(want_query, want_map)
            return f"employee node is created"
        except Exception as e:
            return "sth went wrong"


@app.route("/")
def home():
    return App.render(render_template("index.html"))


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
    if "email" in session:
        email = session["email"]
        if request.method == "GET":
            title = request.args.get('title')
            if title:
                title = f'(?i).*{title}.*'
                get_movies_query = '''match(m:Movie) WHERE m.title =~ $title return m.title, m.released, m.tagline'''
                get_watched_movies_query = '''match(m:Movie)-[r:WATCHED]-(u:User{email:$email}) WHERE m.title =~ $title return m.title, r.rate'''
                get_want_to_watch_movies_query = '''match(m:Movie)-[r:WANT_TO_WATCH]-(u:User{email:$email}) WHERE m.title =~ $title return m.title'''
                found_movies = driver_session.run(get_movies_query, {'title': title})
                found_watched_movies = driver_session.run(get_watched_movies_query, {'title': title, 'email': email})
                found_want_to_watch_movies = driver_session.run(get_want_to_watch_movies_query, {'title': title, 'email': email})
                found_want_to_watch_movies_data = found_want_to_watch_movies.data()
                found_movies_data = found_movies.data()
                found_watched_movies_data = found_watched_movies.data()
                found_watched_list = [val['m.title'] for val in found_watched_movies_data]
                fount_want_to_watch_list = [val['m.title'] for val in found_want_to_watch_movies_data]
                print(found_watched_movies_data)
                print(found_watched_list)
                if found_movies_data:
                    return App.render(render_template("movies.html", movies=found_movies_data, watched=found_watched_list,
                                                      want_to_watch=fount_want_to_watch_list, email=email))
                else:
                    flash("There are no movies containing this phrase")
            return App.render(render_template("movies.html", email=email))
    return redirect(url_for("home"))


@app.route("/watched_movies")
def watched_movies():
    if request.method == "GET":
        email = session['email']
        watched_movies_query = """match (u:User{email: $email})-[r:WATCHED]->(m:Movie) return m.title, m.tagline, m.released, r.rate"""
        found_watched_movies = driver_session.run(watched_movies_query, {'email': email})
        found_movies_data = found_watched_movies.data()
        return render_template("watched_movies.html", movies=found_movies_data)


@app.route("/want_to_watch")
def want_to_watch():
    if request.method == "GET":
        email = session['email']
        want_to_watch_query = """match (u:User{email: $email})-[r:WATCHED]->(m:Movie) return m.title, m.tagline, m.released"""
        found_movies = driver_session.run(want_to_watch_query, {'email': email})
        found_movies_data = found_movies.data()
        return render_template("want_to_watch.html", movies=found_movies_data)


@app.route("/logout")
def logout():
    flash("You have been logged out", "info")
    session.pop("email", None)
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)

