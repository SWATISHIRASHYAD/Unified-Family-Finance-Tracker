from flask import Flask, request, render_template, session, url_for, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import secrets
import enum
from datetime import datetime
from flask import jsonify,request
from models import db,Budget,Alert
import matplotlib.pyplot as plt
import os
import pandas as pd

app = Flask(__name__)

# SQLAlchemy Setup
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost:3306/module3'
#change the password and databasename as per your system

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = secrets.token_hex(16)


db = SQLAlchemy(app)


class Budget(db.Model):
    __tablename__="budgets"
    budget_id=db.Column(db.Integer,primary_key=True,autoincrement=True)
    category_id=db.Column(db.Integer,nullable=False)
    user_id=db.Column(db.Integer,nullable=False)
    limit=db.Column(db.DECIMAL)
    start_date=db.Column(db.Date)
    end_date=db.Column(db.Date)

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

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        sql = text("SELECT * FROM user WHERE username = :username")
        user = db.session.execute(sql, {"username": username}).fetchone()

        if user and user._mapping['user_password'] == password:  # Check password
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
        # Get data from form
        UserID = request.form['UserID']
        categoryid = request.form['categoryid']
        amount = request.form['amount']
        expensedate = datetime.strptime(request.form['expensedate'], '%Y-%m-%d').date()
        expensedesc = request.form.get('expensedesc', '')
        receiptpath = request.form.get('receiptpath', '')
        expensetime = datetime.strptime(request.form['expensetime'], '%H:%M').time()

        # Create a new expense object
        new_expense = Expense(
            UserID=UserID,
            categoryid=categoryid,
            amount=amount,
            expensedate=expensedate,
            expensedesc=expensedesc,
            receiptpath=receiptpath,
            expensetime=expensetime
        )

        # Add the expense to the database
        db.session.add(new_expense)
        db.session.commit()

        return redirect(url_for('show_expenses'))

    return render_template('add_expenses.html')

@app.route('/show_expenses')
def show_expenses():
    expenses = Expense.query.all()  # Fetch all expenses
    return render_template('show_expenses.html', expenses=expenses)

@app.route('/saving_goals')
def saving_goals():
    user_id = session.get('user_id')
    family_head_id = session.get('family_head_id')

    sql = text("""
        SELECT * FROM savings_goals
        WHERE 
            (Goal_type = 'Personal' AND User_id = :user_id)
            OR
            (Goal_type = 'Family' AND family_head_id = :family_head_id)
    """)
    savings_goals = db.session.execute(sql, {"user_id": user_id, "family_head_id": family_head_id}).fetchall()

    return render_template("saving_goals.html", datas=savings_goals)


@app.route("/add_amount/<string:id>", methods=["GET", "POST"])
def add_amount(id):
    user_id = session.get("user_id")
    family_head_id = session.get("family_head_id")

    sql = text("""
        SELECT * FROM savings_goals 
        WHERE Goal_id = :goal_id AND (User_id = :user_id OR family_head_id = :family_head_id)
    """)
    goal = db.session.execute(sql, {"goal_id": id, "user_id": user_id, "family_head_id": family_head_id}).fetchone()

    if not goal:
        flash("Goal not found")
        return redirect(url_for("saving_goals"))

    if request.method == "POST":
        additional_amount = float(request.form["additional_amount"])

        # Update achieved_amount
        update_sql = text("""
            UPDATE savings_goals 
            SET achieved_amount = COALESCE(achieved_amount, 0) + :amount
            WHERE Goal_id = :goal_id AND (User_id = :user_id OR family_head_id = :family_head_id)
        """)
        db.session.execute(update_sql, {
            "amount": additional_amount,
            "goal_id": id,
            "user_id": user_id,
            "family_head_id": family_head_id
        })

        # Update goal status
        goal = db.session.execute(sql, {"goal_id": id, "user_id": user_id, "family_head_id": family_head_id}).fetchone()
        achieved_amount = goal._mapping["Achieved_amount"]
        target_amount = goal._mapping["Target_amount"]

        status = "completed" if achieved_amount >= target_amount else "on-going"
        status_sql = text("""
            UPDATE savings_goals 
            SET Goal_status = :status
            WHERE Goal_id = :goal_id AND (User_id = :user_id OR family_head_id = :family_head_id)
        """)
        db.session.execute(status_sql, {"status": status, "goal_id": id, "user_id": user_id, "family_head_id": family_head_id})
        db.session.commit()

        flash("Amount Added Successfully!")
        return redirect(url_for("saving_goals"))

    return render_template("add_amount.html", data=goal)


@app.route("/addgoal", methods=['GET', 'POST'])
def add_Goal():
    family_head_id = session.get('family_head_id')
    user_id = session.get('user_id')

    if request.method == "POST":
        target_amount = request.form['target_amount']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        goal_status = request.form['goal_status']
        goal_description = request.form['goal_description']
        achieved_amount = request.form['achieved_amount']
        goal_type = request.form['goal_type']

        sql = text("""
            INSERT INTO savings_goals 
            (User_id, family_head_id, Target_amount, start_date, end_date, Goal_status, Goal_description, Achieved_amount, Goal_type)
            VALUES (:user_id, :family_head_id, :target_amount, :start_date, :end_date, :goal_status, :goal_description, :achieved_amount, :goal_type)
        """)
        db.session.execute(sql, {
            "user_id": user_id,
            "family_head_id": family_head_id,
            "target_amount": target_amount,
            "start_date": start_date,
            "end_date": end_date,
            "goal_status": goal_status,
            "goal_description": goal_description,
            "achieved_amount": achieved_amount,
            "goal_type": goal_type
        })
        db.session.commit()

        flash("Goal Added Successfully")
        return redirect(url_for('saving_goals'))

    return render_template("addgoals.html")


@app.route("/edit_Goals/<string:id>", methods=['GET', 'POST'])
def edit_Goals(id):
    user_id = session.get('user_id')

    if request.method == 'POST':
        target_amount = request.form['target_amount']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        goal_status = request.form['goal_status']
        goal_description = request.form['goal_description']
        achieved_amount = request.form['achieved_amount']
        goal_type = request.form['goal_type']

        sql = text("""
            UPDATE savings_goals 
            SET Target_amount = :target_amount, start_date = :start_date, end_date = :end_date, 
                Goal_status = :goal_status, Goal_description = :goal_description, 
                Achieved_amount = :achieved_amount, Goal_type = :goal_type
            WHERE Goal_id = :goal_id AND User_id = :user_id
        """)
        db.session.execute(sql, {
            "target_amount": target_amount,
            "start_date": start_date,
            "end_date": end_date,
            "goal_status": goal_status,
            "goal_description": goal_description,
            "achieved_amount": achieved_amount,
            "goal_type": goal_type,
            "goal_id": id,
            "user_id": user_id
        })
        db.session.commit()

        flash("Goal Updated Successfully")
        return redirect(url_for("saving_goals"))

    sql = text("SELECT * FROM savings_goals WHERE Goal_id = :goal_id")
    goal = db.session.execute(sql, {"goal_id": id}).fetchone()

    return render_template("editgoals.html", datas=goal)


@app.route("/delete_Goals/<string:id>", methods=['GET', 'POST'])
def delete_Goals(id):
    user_id = session.get('user_id')

    sql = text("DELETE FROM savings_goals WHERE Goal_id = :goal_id AND User_id = :user_id")
    db.session.execute(sql, {"goal_id": id, "user_id": user_id})
    db.session.commit()

    flash('Goal Deleted Successfully')
    return redirect(url_for("saving_goals"))


@app.route('/budgethome')
def budgethome():
    return render_template('index.html')


@app.route('/addBudget')
def bud():
    return render_template('Budget.html')

@app.route('/viewAlerts')
def ale():
    with db.engine.connect() as conn:
        alerts=conn.execute(text("select * from alert"))
        alerts=[[a.alert_id,a.budget_id,a.alert_type,a.alert_message,a.alert_date,a.is_resolved] for a in alerts]
        return render_template('Alerts.html',alerts=alerts)

@app.route('/Budget',methods=['GET'])
def getall_budget():
    budgets=db.session.query(Budget).all()
    budgets=[[budget.budget_id,budget.category_id,budget.limit,budget.start_date,budget.end_date,budget.user_id] for budget in budgets]
    return render_template('viewBudget.html',budgets=budgets)

@app.route('/Budget',methods=['POST'])
def add_budget():
    data=request.get_json()
    budget=Budget(category_id=data['category_id'],user_id=data['user_id'],limit=data['limit'],start_date=data['start_date'],end_date=data['end_date'])
    db.session.add(budget)
    db.session.commit()
    return jsonify({"message":"Budget created successfully"}),201

@app.route('/Budget',methods=['DELETE'])
def delete_budget():
    data=request.get_json()
    try:
        budget=db.session.query(Budget).filter_by(budget_id=data['budget_id']).first()
        db.session.delete(budget)
        db.session.commit()
        return jsonify({"message":f"Budget with id:-{data['budget_id']} is deleted"})
    except:
        return jsonify({"message":"No id with such budget"}),404

@app.route('/Alerts',methods=["GET"])
def get_alerts():
    alerts=db.session.query(Alert)
    alert=[]
    for i in alerts:
        alert.append([i.alert_id,i.alert_date,i.alert_message,i.alert_type,i.budget_id,i.is_resolved])
    return jsonify({"alerts":alerts}),200


GRAPH_DIR = "static/images"
DOWNLOAD_DIR = "static/downloads"
os.makedirs(GRAPH_DIR, exist_ok=True)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Route for budget visualization
@app.route('/organize')
def budget_visualization():
    # Query budget data
    budgets = Budget.query.all()
    df = pd.DataFrame([{ 'category_id': b.category_id, 'limit': b.limit } for b in budgets])

    # Generate and save the graph
    graph_path = os.path.join(GRAPH_DIR, 'budget_graph.png')
    plt.figure(figsize=(10, 6))
    plt.plot(df['category_id'], df['limit'], marker='o', color='blue', label='Budget Limit')
    plt.title('Budget Graph')
    plt.xlabel('Category ID')
    plt.ylabel('Budget Limit')
    plt.legend()
    plt.grid()
    plt.savefig(graph_path)
    plt.close()

    # Generate and save the CSV
    csv_path = os.path.join(DOWNLOAD_DIR, 'budget_data.csv')
    df.to_csv(csv_path, index=False)

    return render_template('indexreport.html', graph_url=url_for('static', filename='images/budget_graph.png'), csv_url=url_for('static', filename='downloads/budget_data.csv'))

# Route for expenses visualization
@app.route('/expenses')
def expenses_visualization():
    # Query expense data
    expenses = Expense.query.all()
    df = pd.DataFrame([{ 'categoryid': e.categoryid, 'amount': e.amount } for e in expenses])

    # Generate and save the graph
    graph_path = os.path.join(GRAPH_DIR, 'expenses_graph.png')
    plt.figure(figsize=(10, 6))
    plt.plot(df['categoryid'], df['amount'], marker='o', color='blue', label='Expense Limit')
    plt.title('Expenses Graph')
    plt.xlabel('Category ID')
    plt.ylabel('Amount')
    plt.legend()
    plt.grid()
    plt.savefig(graph_path)
    plt.close()

    # Generate and save the CSV
    csv_path = os.path.join(DOWNLOAD_DIR, 'expense_data.csv')
    df.to_csv(csv_path, index=False)

    return render_template('indexreport.html', graph_url=url_for('static', filename='images/expenses_graph.png'), csv_url=url_for('static', filename='downloads/expense_data.csv'))


if __name__ == '__main__':
    app.run(debug=True)
