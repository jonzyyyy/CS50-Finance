import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    user_id = session.get("user_id")

    # Update current stock prices
    stock_portfolio = db.execute("SELECT symbol FROM transactions WHERE user_id = ?", user_id)
    for stock in stock_portfolio:
        # Updates the current prices of the symbols user owns
        db.execute(
            "UPDATE transactions SET stockprice = ? WHERE user_id = ? AND symbol = ?", lookup(stock["symbol"])['price'], user_id, stock["symbol"])
    holdings = 0
    latest_prices = db.execute(
        "SELECT stockprice, SUM(shares) as numshares FROM transactions GROUP BY user_id, symbol HAVING user_id = ?", user_id)
    for price in latest_prices:
        holdings += price['stockprice'] * price['numshares']

    # Update portfolio value
    cash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)
    total = cash[0]["cash"] + holdings
    db.execute("UPDATE users SET portfolio = ? WHERE id = ?", total, user_id)

    # Display information to user
    transactions = db.execute(
        "SELECT user_id, SUM(shares) as shares, stockname, symbol, sum(cost) as cost, stockprice FROM transactions WHERE user_id = ? GROUP BY user_id, stockname HAVING SUM(shares) > 0 ", user_id)
    users = db.execute("SELECT * FROM users WHERE id = ?", user_id)
    return render_template("index.html", transactions=transactions, users=users, usd=usd)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":

        # Checks if symbol exists
        if lookup(request.form.get("symbol")) == None:
            return apology("Invalid symbol", 400)

        # Checks if user input is an integer
        if not request.form.get("shares").isdigit():
            return apology("Must provide an integer", 400)

        # Ensure positive number of shares
        elif int(request.form.get("shares")) < 1:
            return apology("Value must be greater than 1", 400)

        # Store users input
        symbol = lookup(request.form.get("symbol"))['symbol']
        stock_name = lookup(request.form.get("symbol"))['name']
        stock_price = lookup(request.form.get("symbol"))['price']
        num_shares = request.form.get("shares")
        total_price = float(stock_price) * float(num_shares)

        # Check if user has sufficient funds
        user_funds = db.execute("SELECT cash FROM users WHERE id = ?", session.get("user_id"))
        if user_funds[0]['cash'] < total_price:
            return apology("You do not have sufficient funds", 403)

        # Deduct funds from users cash and update database
        updated_funds = user_funds[0]['cash'] - total_price
        db.execute("UPDATE users SET cash = ? WHERE id = ?", updated_funds, session.get("user_id"))

        # Store transaction information in database
        db.execute("INSERT INTO transactions (user_id, symbol, stockname, stockprice, shares, cost) VALUES (?, ?, ?, ?, ?, ?)",
        session.get("user_id"), symbol, stock_name, stock_price, num_shares, total_price)

        # User feedback
        flash("Bought!", category="info")

        # Redirect user to home page
        return redirect("/")

    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    transactions = db.execute("SELECT * FROM transactions WHERE user_id = ? ORDER BY timestamp", session.get("user_id"))
    return render_template("history.html", transactions=transactions)


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
        return redirect("/")

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
    if request.method == "POST":

        # Checks if symbol exists
        if lookup(request.form.get("symbol")) == None:
            return apology("Invalid symbol", 400)

        # Query stock symbol input from user
        stock_info = lookup(request.form.get("symbol"))
        name = stock_info['name']
        price = usd(stock_info['price'])
        symbol = stock_info['symbol']

        return render_template("quoted.html", name=name, price=price, symbol=symbol)

    # Request stock symbol from user
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    session.clear()

    """Register user"""
    if request.method == "POST":
        # Ensure non blank username was submitted
        if not request.form.get("username") or request.form.get("username").isspace() == True:
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Ensure confirmation password was submitted
        elif not request.form.get("confirmation"):
            return apology("must provide confirmation password", 400)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username does not exist and password is correct
        if len(rows) == 1:
            return apology("Username is taken", 400)

        # Ensure passwords match
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords do not match")

        # Hash password
        hash = generate_password_hash(request.form.get("password"), method='pbkdf2:sha256', salt_length=8)

        # User feedback
        flash("Registered!", category="info")

        # Remember user
        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", request.form.get("username"), hash)
        return redirect("/")

    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":
        user_id = session.get("user_id")

        # Ensure a symbol has been selected
        if not request.form.get("symbol"):
            return apology("please select a share you want to sell", 403)

        # Ensure that user has input in the shares field
        shares = db.execute("SELECT SUM(shares) FROM transactions WHERE user_id = ? GROUP BY symbol HAVING symbol = ?",
        user_id, request.form.get('symbol'))
        if not request.form.get("shares"):
            return apology("please input number of shares")

        # Ensure that user has enough shares to sell
        elif int(request.form.get("shares")) > int(shares[0]["SUM(shares)"]):
            return apology("too many shares", 400)

        # Obtain database information
        information = db.execute("SELECT portfolio, cash FROM users WHERE id = ?", user_id)

        # Update database information
        stock_price = float(lookup(request.form.get("symbol"))['price'])
        selling = float(stock_price) * float(request.form.get("shares"))
        db.execute("UPDATE users SET cash = ?, portfolio = ? WHERE id = ?",
        (information[0]['cash'] + selling), (information[0]['portfolio'] - selling), user_id)

        db.execute("INSERT INTO transactions (user_id, shares, stockprice, cost, symbol, stockname) VALUES (?, ?, ?, ?, ?, ?)",
        user_id, int(request.form.get("shares")) * -1, stock_price, selling * -1, request.form.get("symbol"), lookup(request.form.get("symbol"))['name'])

        # User feedback
        flash("Sold!", category="info")

        return redirect("/")

    else:
        transactions = db.execute("SELECT DISTINCT symbol FROM transactions WHERE user_id = ?", session.get("user_id"))
        return render_template("sell.html", transactions=transactions)

@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    """Change user's password"""
    if request.method == "POST":

        user_id = session.get("user_id")

        # Ensure that all fields has been filled
        if not request.form.get("oldpassword"):
            return apology("old password cannot be blank", 400)
        elif not request.form.get("newpassword") or request.form.get("newpasswordcfm") == False:
            return apology("new password field(s) cannot be blank", 400)

        # Query database for password
        rows = db.execute("SELECT hash FROM users WHERE id = ?", user_id)

        # Ensure that new password matches
        if request.form.get("newpassword") != request.form.get("newpasswordcfm"):
            return apology("new passwords do not match", 400)

        # Ensure old password is correct
        elif not check_password_hash(rows[0]['hash'], request.form.get("oldpassword")):
            return apology("old password is wrong", 403)

        # Change password in database
        hash = generate_password_hash(request.form.get("newpasswordcfm"), method='pbkdf2:sha256', salt_length=8)
        db.execute("UPDATE users SET hash = ? WHERE id = ?", hash, user_id)

        # User feedback
        flash("Password has been changed!", category="info")

        return redirect("/")

    else:
        return render_template("change_password.html")

@app.route("/addcash", methods=["GET","POST"])
@login_required
def addcash():
    """Add funds to user's account"""
    if request.method == "POST":
        if not request.form.get("amount"):
            return apology("Please add an amount", 400)
        rows = db.execute("SELECT cash, portfolio FROM users WHERE id = ?", session.get("user_id"))
        new_cash = float(rows[0]['cash']) + float(request.form.get("amount"))
        new_portfolio = new_cash + float(rows[0]['portfolio'])
        db.execute("UPDATE users SET cash = ?, portfolio = ? WHERE id = ?", new_cash, new_portfolio, session.get("user_id"))
        return redirect("/")
    else:
        return render_template('cash.html')