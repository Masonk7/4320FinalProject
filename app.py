from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
import os
import uuid

app = Flask(__name__)
app.config["SECRET_KEY"] = "root"  
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(BASE_DIR, "reservations.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


def get_cost_matrix():
    return [[100, 75, 50, 100] for _ in range(12)]

COST_MATRIX = get_cost_matrix()

def seat_price(row, col):
    return COST_MATRIX[row - 1][col - 1]


class Reservation(db.Model):
    __tablename__ = "reservations"
    id = db.Column(db.Integer, primary_key=True)
    passengerName = db.Column(db.Text, nullable=False)
    seatRow = db.Column(db.Integer, nullable=False)
    seatColumn = db.Column(db.Integer, nullable=False)
    eTicketNumber = db.Column(db.Text, nullable=False)
    created = db.Column(
        db.DateTime,
        nullable=False,
        server_default=func.current_timestamp()
    )

class Admin(db.Model):
    __tablename__ = "admins"
    username = db.Column(db.Text, primary_key=True)
    password = db.Column(db.Text, nullable=False)

def build_seating_chart():
    chart = []
    reservations = Reservation.query.all()
    taken = {(r.seatRow, r.seatColumn): r for r in reservations}

    for row in range(1, 13):      
        row_list = []
        for col in range(1, 5):   
            r = taken.get((row, col))
            row_list.append({
                "row": row,
                "col": col,
                "reserved": r is not None,
                "name": r.passengerName if r else "",
                "price": seat_price(row, col)
            })
        chart.append(row_list)
    return chart

def calculate_total_sales():
    total = 0
    for r in Reservation.query.all():
        total += seat_price(r.seatRow, r.seatColumn)
    return total

def is_admin_logged_in():
    return "admin_username" in session


@app.route("/")
def main_menu():
    return render_template("index.html")

@app.route("/reserve", methods=["GET", "POST"])
def reserve():
    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        seat_row = request.form.get("seat_row", "").strip()
        seat_col = request.form.get("seat_col", "").strip()

        if not first_name or not last_name or not seat_row or not seat_col:
            flash("All fields are required.", "error")
            return redirect(url_for("reserve"))

        try:
            seat_row = int(seat_row)
            seat_col = int(seat_col)
        except ValueError:
            flash("Row and column must be numbers.", "error")
            return redirect(url_for("reserve"))

        if not (1 <= seat_row <= 12 and 1 <= seat_col <= 4):
            flash("Row must be 1–12 and column 1–4.", "error")
            return redirect(url_for("reserve"))

        existing = Reservation.query.filter_by(
            seatRow=seat_row,
            seatColumn=seat_col
        ).first()
        if existing:
            flash("That seat is already reserved. Pick another one.", "error")
            return redirect(url_for("reserve"))

        full_name = f"{first_name} {last_name}"
        code = f"BUS-{seat_row}-{seat_col}-{uuid.uuid4().hex[:6].upper()}"

        new_res = Reservation(
            passengerName=full_name,
            seatRow=seat_row,
            seatColumn=seat_col,
            eTicketNumber=code
        )
        db.session.add(new_res)
        db.session.commit()

        price = seat_price(seat_row, seat_col)
        return render_template(
            "reserve_success.html",
            reservation=new_res,
            price=price
        )

    seating_chart = build_seating_chart()
    return render_template("reserve.html", seating_chart=seating_chart)

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        admin = Admin.query.filter_by(
            username=username,
            password=password
        ).first()

        if admin:
            session["admin_username"] = admin.username
            flash("Logged in.", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid username or password.", "error")
            return redirect(url_for("admin_login"))

    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_username", None)
    flash("Logged out.", "success")
    return redirect(url_for("main_menu"))

@app.route("/admin")
def admin_dashboard():
    if not is_admin_logged_in():
        flash("Please log in as admin.", "error")
        return redirect(url_for("admin_login"))

    seating_chart = build_seating_chart()
    total_sales = calculate_total_sales()
    reservations = Reservation.query.order_by(
        Reservation.created.desc()
    ).all()

    return render_template(
        "admin_dashboard.html",
        seating_chart=seating_chart,
        total_sales=total_sales,
        reservations=reservations
    )

@app.route("/admin/delete/<int:reservation_id>", methods=["POST"])
def delete_reservation(reservation_id):
    if not is_admin_logged_in():
        flash("Please log in as admin.", "error")
        return redirect(url_for("admin_login"))

    res = Reservation.query.get_or_404(reservation_id)
    db.session.delete(res)
    db.session.commit()
    flash("Reservation deleted.", "success")
    return redirect(url_for("admin_dashboard"))

if __name__ == "__main__":
    app.run(debug=True)


