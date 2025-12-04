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

