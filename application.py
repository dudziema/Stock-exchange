import os
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from decimal import Decimal

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/index")
@login_required
def index():

    # Get user details
    idUser= session["user_id"]
    shares = db.execute("SELECT * FROM stockbuy WHERE id_user=? GROUP BY symbol", idUser)[0]["shares"]
    symbols= db.execute("SELECT symbol FROM stockbuy WHERE id_user=? GROUP BY symbol", idUser)

    for symbol in symbols:

        get_data=lookup(symbol["symbol"])
        price= get_data["price"]
        share_quantity= db.execute("SELECT SUM(shares) FROM stockbuy WHERE id_user=? AND symbol=? GROUP BY symbol", idUser, symbol["symbol"])
        total= price* shares["share"]
    return render_template("index.html", shares= symbols)



@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":


        # Get from user symbol and quantity of shares which want to buy
        symbol =request.form.get("symbol")
        shares =int(request.form.get("shares"))

        # Check current price of stock
        get_data = lookup(symbol)


        # Show apology if data provided is incorrect.
        if get_data == None:
            return apology("Stock not found. Please, provide correct symbol.")
        if shares <= 0 or None:
            return apology("Amount equal or less than zero. Provide positive quantity of shares.")


        # Get data from user
        idUser= session["user_id"]
        user_name= db.execute("SELECT username FROM users WHERE id=?", idUser)[0]["username"]
        cash = db.execute("SELECT cash FROM users WHERE id= ? LIMIT 1", idUser)[0]["cash"]


        # take data from transaction
        share_price= get_data["price"]
        total_price= share_price * shares
        company= get_data["name"]


        # Check if user has enough cash
        if cash < total_price:
            return apology("You don't have enough money.")
        else:
            now= datetime.now()
            date_time= now.strftime("%d/%m/%Y %H:%M:%S")
            new_cash= cash- total_price
            insert_new_line= db.execute("INSERT INTO stockbuy (id_user, username, symbol, company, shares, price, date, total) VALUES(?,?,?,?,?,?,?,?)",idUser, user_name, symbol, company,shares, share_price, date_time, total_price)
            update_cash= db.execute("UPDATE users SET cash= ? WHERE id=?", new_cash, idUser)
            return redirect ("/index")
    return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    return apology("TODO")



@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/index")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method =="POST":
        symbol = request.form.get("symbol")
        get_data = lookup(symbol)
        if get_data != None:
            return render_template("quoted.html", company= get_data["name"], price= usd(get_data["price"]))
        else:
            return render_template(("quote.html"), not_found= "Stock not found. Please, provide correct symbol.")

    return render_template(("quote.html"), not_found="")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Forget any user_id
    session.clear()

    #User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        #Ensure username was submitted
        if not request.form.get("username"):
            return apology("You must provide username!", 403)

        #Ensure password was submitted
        elif not request.form.get("password"):
            return apology("You must provide password!", 403)

        #Ensure confirmation password was submitted and equal to password
        if request.form.get("confirmation") != request.form.get("password"):
            return apology("Confirmation must equal password!", 403)

        #Ensure username doesn't exist
        rows = db.execute("SELECT * FROM users WHERE username = :username", username= request.form.get("username"))
        if len(rows) == 1:
            return apology("The username already exists!")

        # Generate password hash
        hash_password = generate_password_hash(request.form.get("password"), method='pbkdf2:sha256', salt_length=8)

        # Query database for insert username and hash password
        rows = db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash) ", username= request.form.get("username"), hash= hash_password)

        #Check if register went succesful
        rows = db.execute("SELECT * FROM users WHERE username = :username", username= request.form.get("username"))

        if len(rows) != 1:
            return apology("Sorry something went wrong, please try again.")

        else:
            return redirect("/login")

    return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    return apology("TODO")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
