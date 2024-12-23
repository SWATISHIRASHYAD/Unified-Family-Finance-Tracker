from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
import enum
from datetime import datetime
import os

app = Flask(__name__, static_folder='static', template_folder='templates')

# Directly set configuration values
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost:3306/unified_family'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')

# Initialize SQLAlchemy directly with the app
db = SQLAlchemy(app)

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

@app.route('/')
def index():
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
    result = []
    for budget in budgets:
        result.append([budget.category_id, budget.limit, budget.start_date, budget.end_date, budget.user_id])
    return jsonify({"message": result}), 200

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
    try:
        budget = db.session.query(Budget).filter_by(budget_id=data['budget_id']).first()
        db.session.delete(budget)
        db.session.commit()
        return jsonify({"message": f"Budget with id:-{data['budget_id']} is deleted"})
    except:
        return jsonify({"message": "No id with such budget"}), 404

@app.route('/Alerts', methods=["GET"])
def get_alerts():
    alerts = db.session.query(Alert).all()
    alert = []
    for i in alerts:
        alert.append([i.alert_id, i.alert_date, i.alert_message, i.alert_type.value, i.budget_id, i.is_resolved])
    return jsonify({"alerts": alert}), 200

if __name__ == "__main__":
    app.run(debug=True)
