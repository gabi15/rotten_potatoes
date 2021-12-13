from flask import Flask, redirect, url_for, render_template, request, session, flash, jsonify
from datetime import timedelta
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
import jyserver.Flask as jsf

load_dotenv()

app = Flask(__name__)
app.secret_key = "\xd7\xd6.\xf8\xbe\xf3\xe5\xbdJ\x05/D\xd8\xc8S\xe7(\xb4V2}z\xc3\xe3"

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
        id_rated_name = title + "_rated"
        rate = self.js.document.getElementById(id_rate_name).value
        rate = str(rate)
        rate = int(rate)
        email = session["email"]
        watched_query = """match (u:User{email:$email}),(m:Movie{title:$title}) merge (u)-[r:WATCHED]->(m) SET r.rate = $rate return type(r)""" #merge so i dont create node if already connected
        watched_map = {"email": email, "title": title, "rate": rate}
        try:
            create = driver_session.run(watched_query, watched_map)
            self.js.document.getElementById(id_unwatch_name).disabled = False
            self.flash_info(f"Successfully rated {title}")
            self.js.document.getElementById(id_rated_name).innerText = rate
            self.js.document.getElementById(id_rated_name).style.fontWeight = 'bold'
            return jsonify(create.data())
        except Exception as e:
            print(e)
            return jsonify("sth went wrong")

    def delete_from_watched(self, title):
        id_unwatch_name = title+"_unwatch"
        self.js.document.getElementById(id_unwatch_name).disabled = True
        email = session["email"]
        watched_query = """match (u:User{email:$email})-[r:WATCHED]->(m:Movie{title:$title}) delete r"""
        watched_map = {"email": email, "title": title}
        try:
            driver_session.run(watched_query, watched_map)
            self.flash_info(f"Successfully deleted from watched {title}")
            return jsonify("success")
        except Exception as e:
            print(e)
            return jsonify("sth went wrong")

    def delete_from_want_to_watch(self, title, id_unwant_name, id_want_name):
        self.js.document.getElementById(id_unwant_name).disabled = True
        self.js.document.getElementById(id_want_name).disabled = False
        email = session["email"]
        want_query = """match (u:User{email:$email})-[r:WANT_TO_WATCH]->(m:Movie{title:$title}) delete r"""
        want_map = {"email": email, "title": title}
        try:
            driver_session.run(want_query, want_map)
            self.flash_info(f"Successfully deleted from watchlist {title}")
            return jsonify("success")
        except Exception as e:
            return jsonify("sth went wrong")

    def add_to_want_to_watch(self, title, id_unwant_name, id_want_name):
        self.js.document.getElementById(id_unwant_name).disabled = False
        self.js.document.getElementById(id_want_name).disabled = True
        email = session["email"]
        want_query = """match (u:User{email:$email}),(m:Movie{title:$title}) merge (u)-[r:WANT_TO_WATCH]->(m) return type(r)"""
        want_map = {"email": email, "title": title}
        try:
            driver_session.run(want_query, want_map)
            self.flash_info(f"Successfully added to watchlist {title}")
            return "success"
        except Exception as e:
            print(e)
            return jsonify("sth went wrong")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
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
                return redirect(url_for("movies"))

        except Exception as e:
            print(e)
            return "sth went wrong"
    else:
        return render_template("register.html")


@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        session.permanent = True
        email = request.form["email"]
        password = request.form["password"]
        session["email"] = email

        find_user_query = '''match(u:User {email: $email, password: $password}) return u'''
        found_user = driver_session.run(find_user_query, {'email': email, 'password': password})
        found_user_data = found_user.data()

        if found_user_data:
            session["email"] = email
            return redirect(url_for("movies"))
        else:
            flash("Login unsuccesful!")
            return render_template("login.html")
    else:
        if "email" in session:
            flash("Already logged in!")
            return redirect(url_for("movies"))

        return render_template("login.html")


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
                found_watched_dict = {el['m.title']: el['r.rate'] for el in found_watched_movies_data}
                found_want_to_watch_list = [val['m.title'] for val in found_want_to_watch_movies_data]
                for el in found_movies_data:
                    print(el['m.title'])
                    if el['m.title'] in found_watched_dict.keys():
                        el['r.rate'] = found_watched_dict[el['m.title']]
                    else:
                        el['r.rate'] = '-'
                print(found_movies_data)

                if found_movies_data:
                    return App.render(render_template("movies.html", movies=found_movies_data,
                                                      want_to_watch=found_want_to_watch_list, email=email))
                else:
                    flash("There are no movies containing this phrase")
            return App.render(render_template("movies.html", email=email))
    return redirect(url_for("login"))


@app.route("/watched_movies")
def watched_movies():
    if request.method == "GET":
        email = session['email']
        watched_movies_query = """match (u:User{email: $email})-[r:WATCHED]->(m:Movie) return m.title, m.tagline, m.released, r.rate order by r.rate DESC"""
        found_watched_movies = driver_session.run(watched_movies_query, {'email': email})
        found_movies_data = found_watched_movies.data()
        return render_template("watched_movies.html", movies=found_movies_data, email=email)


@app.route("/want_to_watch")
def want_to_watch():
    if request.method == "GET":
        email = session['email']
        want_to_watch_query = """match (u:User{email: $email})-[r:WANT_TO_WATCH]->(m:Movie) return m.title, m.tagline, m.released"""
        found_movies = driver_session.run(want_to_watch_query, {'email': email})
        found_movies_data = found_movies.data()
        return render_template("want_to_watch.html", movies=found_movies_data, email=email)


@app.route('/recommendations')
def recommendations():
    if request.method == "GET":
        email = session['email']
        movies_query = """MATCH (p1:User {email: $email})-[x:WATCHED]->(m:Movie)<-[y:WATCHED]-(p2:User)
        WITH COUNT(m) AS numbermovies, SUM(x.rate * y.rate) AS xyDotProduct,
        SQRT(REDUCE(xDot = 0.0, a IN COLLECT(x.rate) | xDot + a^2)) AS xLength,
        SQRT(REDUCE(yDot = 0.0, b IN COLLECT(y.rate) | yDot + b^2)) AS yLength,
        p1, p2
        WITH p1, p2, xyDotProduct / (xLength * yLength) AS sim
        ORDER BY sim DESC
        LIMIT 100
        MATCH (p2)-[r:WATCHED]->(m:Movie) WHERE NOT EXISTS( (p1)-[:WATCHED]->(m) )
        
        RETURN m.title, m.released, m.tagline, SUM( sim * r.rate) AS score
        ORDER BY score DESC LIMIT 25"""
        found_movies = driver_session.run(movies_query, {'email': email})
        found_movies_data = found_movies.data()
        titles = [val['m.title'] for val in found_movies_data]
        get_want_to_watch_movies_query = '''match(m:Movie)-[r:WANT_TO_WATCH]-(u:User{email:$email}) WHERE m.title in $titles return m.title'''
        found_want_to_watch_movies = driver_session.run(get_want_to_watch_movies_query, {'email': email, 'titles': titles})
        found_want_to_watch_movies_data = found_want_to_watch_movies.data()
        found_want_to_watch_list = [val['m.title'] for val in found_want_to_watch_movies_data]
        print(titles)
        print(found_want_to_watch_movies_data)

        return App.render(render_template("recommendations.html", movies=found_movies_data, email=email, want_to_watch=found_want_to_watch_list))


@app.route("/related")
def related():
    if request.method == "GET":
        email = session['email']
        title = request.args.get('title')
        people_query = """MATCH (people:Person)-[relatedTo]-(:Movie {title: $title}) RETURN people.name, Type(relatedTo), relatedTo.roles"""
        found_people = driver_session.run(people_query, {'title': title})
        found_people_data = found_people.data()
        return render_template("related.html", people=found_people_data, email=email, title=title)
    return {}


@app.route("/logout")
def logout():
    flash("You have been logged out", "info")
    session.pop("email", None)
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)

