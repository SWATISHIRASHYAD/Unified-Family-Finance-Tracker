from flask import jsonify,request
from .models import db,Budget,Alert
from flask_cors import CORS

def init_routes(app):
    CORS(app)
    @app.route('/Budget',methods=['GET'])
    def getall_budget():
        budgets=db.session.query(Budget).all()
        result=[]
        for budget in budgets:
            result.append([budget.category_id,budget.limit,budget.start_date,budget.end_date,budget.user_id])
        return jsonify({"message":result}),200

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