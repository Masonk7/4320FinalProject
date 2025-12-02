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