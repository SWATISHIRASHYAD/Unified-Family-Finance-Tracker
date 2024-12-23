from flask import Flask, jsonify, request, render_template, session, url_for, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from flask_cors import CORS
from datetime import datetime
import secrets
import enum
import os

# Flask App Initialization
app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# SQLAlchemy Setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost:3306/unified_family'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = secrets.token_hex(16)
db = SQLAlchemy(app)

# Models
class Budget(db.Model):
    __tablename__ = "budgets"
    budget_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    limit = db.Column(db.DECIMAL)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)

class AlertType(enum.Enum):
    WARNING = 'Warning'
    CRITICAL = 'Critical'

class Alert(db.Model):
    __tablename__ = "alert"
    alert_id = db.Column(db.Integer, primary_key=True)
    budget_id = db.Column(db.Integer, nullable=False)
    alert_type = db.Column(db.Enum(AlertType), nullable=False)
    alert_message = db.Column(db.String(255), nullable=False)
    alert_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_resolved = db.Column(db.Boolean, default=False, nullable=False)

class Expense(db.Model):
    __tablename__ = 'expenses'
    ExpenseID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    UserID = db.Column(db.Integer, nullable=False)
    categoryid = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    expensedate = db.Column(db.Date, nullable=False)
    expensedesc = db.Column(db.String(500))
    receiptpath = db.Column(db.String(500))
    expensetime = db.Column(db.Time, nullable=False)

    def __repr__(self):
        return f'<Expense {self.ExpenseID}>'

# Routes
@app.route('/')
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        sql = text("SELECT * FROM user WHERE username = :username")
        user = db.session.execute(sql, {"username": username}).fetchone()

        if user and user._mapping['user_password'] == password:
            session['user_id'] = user._mapping['User_id']
            session['family_head_id'] = user._mapping['family_head_id']
            return redirect(url_for('navigationbar'))
        else:
            flash('Invalid credentials')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/navigationbar')
def navigationbar():
    return render_template('navigationbar.html', title="Dashboard")

@app.route('/expensehome')
def expensehome():
    return render_template('expensehome.html')

@app.route('/add_expense', methods=['GET', 'POST'])
def add_expense():
    if request.method == 'POST':
        UserID = request.form['UserID']
        categoryid = request.form['categoryid']
        amount = request.form['amount']
        expensedate = datetime.strptime(request.form['expensedate'], '%Y-%m-%d').date()
        expensedesc = request.form.get('expensedesc', '')
        receiptpath = request.form.get('receiptpath', '')
        expensetime = datetime.strptime(request.form['expensetime'], '%H:%M').time()

        new_expense = Expense(
            UserID=UserID,
            categoryid=categoryid,
            amount=amount,
            expensedate=expensedate,
            expensedesc=expensedesc,
            receiptpath=receiptpath,
            expensetime=expensetime
        )

        db.session.add(new_expense)
        db.session.commit()
        return redirect(url_for('show_expenses'))

    return render_template('add_expenses.html')

@app.route('/show_expenses')
def show_expenses():
    expenses = Expense.query.all()
    return render_template('show_expenses.html', expenses=expenses)

@app.route('/budgethome')
def budgethome():
    return render_template('index.html')

@app.route('/addBudget')
def bud():
    return render_template('Budget.html')

@app.route('/viewAlerts')
def ale():
    return render_template('Alerts.html')

@app.route('/Budget', methods=['GET'])
def getall_budget():
    budgets = db.session.query(Budget).all()
    result = [
        {
            "category_id": budget.category_id,
            "limit": float(budget.limit),
            "start_date": budget.start_date,
            "end_date": budget.end_date,
            "user_id": budget.user_id
        }
        for budget in budgets
    ]
    return jsonify(result), 200

@app.route('/Budget', methods=['POST'])
def add_budget():
    data = request.get_json()
    budget = Budget(
        category_id=data['category_id'],
        user_id=data['user_id'],
        limit=data['limit'],
        start_date=data['start_date'],
        end_date=data['end_date']
    )
    db.session.add(budget)
    db.session.commit()
    return jsonify({"message": "Budget created successfully"}), 201

@app.route('/Budget', methods=['DELETE'])
def delete_budget():
    data = request.get_json()
    budget = db.session.query(Budget).filter_by(budget_id=data['budget_id']).first()
    if budget:
        db.session.delete(budget)
        db.session.commit()
        return jsonify({"message": f"Budget with id {data['budget_id']} is deleted"})
    return jsonify({"message": "No budget found with such ID"}), 404

@app.route('/Alerts', methods=['GET'])
def get_alerts():
    alerts = db.session.query(Alert).all()
    result = [
        {
            "alert_id": alert.alert_id,
            "alert_date": alert.alert_date,
            "alert_message": alert.alert_message,
            "alert_type": alert.alert_type.value,
            "budget_id": alert.budget_id,
            "is_resolved": alert.is_resolved
        }
        for alert in alerts
    ]
    return jsonify(result), 200

if __name__ == '__main__':
    app.run(debug=True)