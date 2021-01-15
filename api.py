from flask import Flask, abort
from flask_restful import Resource, Api, reqparse, fields, marshal, inputs
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})
api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class CategoryModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    cat_type = db.Column(db.String(50), nullable=False)

    def __init__(self, name, amount, cat_type):
        self.name = name
        self.amount = amount 
        self.cat_type = cat_type

category_fields = {
    'id' : fields.Integer,
    'name': fields.String, 
    'amount': fields.Integer,
    'cat_type': fields.String
}

class ExpenseModel(db.Model):
    __tablename__ = 'expense'
    expense_id = db.Column(db.Integer, primary_key=True)
    month_id = db.Column(db.Integer, db.ForeignKey('month.month_id'))
    name = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    category = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)

    def __init__(self, month_id, name, timestamp, category, amount):
        self.month_id = month_id
        self.name = name
        self.timestamp = timestamp
        self.category = category
        self.amount = amount

class MonthModel(db.Model):
    __tablename__ = 'month'
    month_id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    expenses = db.relationship('ExpenseModel', backref='month', cascade='all, delete, delete-orphan', single_parent=True, order_by='ExpenseModel.timestamp')

    def __init__(self, timestamp, expenses):
        self.timestamp = timestamp
        self.expenses = list(map(lambda x: ExpenseModel(self.month_id, x['name'], datetime.strptime(x['timestamp'], '%Y-%m-%d'), x['category'], x['amount']), expenses))

expense_fields = {
    'expense_id' : fields.Integer,
    'month_id' : fields.Integer,
    'name' : fields.String,
    'timestamp' : fields.DateTime,
    'category' : fields.String,
    'amount' : fields.Float
}

month_fields = {
    'month_id' : fields.Integer,
    'timestamp' : fields.DateTime, 
    'expenses' : fields.List(fields.Nested(expense_fields))
}

class CategoryList(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('name', type=str, required=True, help='No category name provided', location='json')
        self.reqparse.add_argument('amount', type=int, required=True, help='No category amount provided', location='json')
        self.reqparse.add_argument('cat_type', type=str, required=True, help='No category type provided', location='json')
        super(CategoryList, self).__init__()

    def get(self):
        categories = CategoryModel.query.all()
        return {'categories': [marshal(category, category_fields) for category in categories]}

    def post(self):
        args = self.reqparse.parse_args()
        name = args['name']
        amount = args['amount']
        cat_type = args['cat_type']
        new_category = CategoryModel(name, amount, cat_type)
        db.session.add(new_category)
        db.session.commit()
        return {'category': marshal(new_category, category_fields)}, 201

class Category(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('name', type=str, location='json')
        self.reqparse.add_argument('amount', type=int, location='json')
        self.reqparse.add_argument('cat_type', type=str, location='json')
        super(Category, self).__init__()

    def get(self, cat_id):
        category = CategoryModel.query.filter_by(id=cat_id).first()
        if not category:
            abort(404)
        return {'category': marshal(category, category_fields)}

    def put(self, cat_id):
        category = CategoryModel.query.filter_by(id=cat_id).first()
        if not category:
            abort(404)
        args = self.reqparse.parse_args()
        if args['name']:
            category.name = args['name']
        if args['amount']:
            category.amount = args['amount']
        if args['cat_type']:
            category.cat_type = args['cat_type']
        db.session.commit()
        return {'category': marshal(category, category_fields)}
    
    def delete(self, cat_id):
        category = CategoryModel.query.filter_by(id=cat_id).first()
        if not category:
            abort(404)
        db.session.delete(category)
        db.session.commit()
        return {'result' : True}

class MonthList(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('timestamp', type=inputs.date, required=True, help='No timestamp provided', location='json')
        self.reqparse.add_argument('expenses', type=list, location='json')
        super(MonthList, self).__init__()

    def get(self):
        months = MonthModel.query.all()
        return {'months': [marshal(month, month_fields) for month in months]}

    def post(self):
        args = self.reqparse.parse_args()
        timestamp = args['timestamp']
        expenses = args['expenses']
        new_month = MonthModel(timestamp, expenses)
        db.session.add(new_month)
        db.session.commit()
        return {'month': marshal(new_month, month_fields)}, 201

class Month(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('timestamp', type=inputs.date, location='json')
        self.reqparse.add_argument('expenses', type=list, location='json')
        super(Month, self).__init__()

    def get(self, month_id):
        month = MonthModel.query.filter_by(month_id=month_id).first()
        if not month:
            abort(404)
        return {'month': marshal(month, month_fields)}

    def put(self, month_id):
        month = MonthModel.query.filter_by(month_id=month_id).first()
        if not month:
            abort(404)
        args = self.reqparse.parse_args()
        if args['timestamp']:
            month.timestamp = args['timestamp']
        if args['expenses']:
            for expense in args['expenses']:
                new_expense = ExpenseModel(month_id, expense['name'], datetime.strptime(expense['timestamp'], '%Y-%m-%d'), expense['category'], expense['amount'])
                db.session.add(new_expense)
        db.session.commit()
        return {'month': marshal(month, month_fields)}
    
    def delete(self, month_id):
        month = MonthModel.query.filter_by(month_id=month_id).first()
        if not month:
            abort(404)
        db.session.delete(month)
        db.session.commit()
        return {'result' : True}

class Expense(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('name', type=str, location='json')
        self.reqparse.add_argument('timestamp', type=inputs.date, location='json')
        self.reqparse.add_argument('category', type=str, location='json')
        self.reqparse.add_argument('amount', type=float, location='json')
        super(Expense, self).__init__()

    def put(self, month_id, expense_id):
        expense = ExpenseModel.query.filter_by(expense_id=expense_id).first()
        if not expense:
            abort(404)
        args = self.reqparse.parse_args()
        if args['name']:
            expense.name = args['name']
        if args['timestamp']:
            expense.timestamp = args['timestamp']
        if args['category']:
            expense.category = args['category']
        if args['amount']:
            expense.amount = args['amount']
        db.session.commit()
        return {'expense': marshal(expense, expense_fields)}
    
    def delete(self, month_id, expense_id):
        expense = ExpenseModel.query.filter_by(expense_id=expense_id).first()
        if not expense:
            abort(404)
        db.session.delete(expense)
        db.session.commit()
        return {'result' : True}

api.add_resource(CategoryList, '/api/categories')
api.add_resource(Category, '/api/categories/<int:cat_id>')
api.add_resource(MonthList, '/api/months')
api.add_resource(Month, '/api/months/<int:month_id>')
api.add_resource(Expense, '/api/months/<int:month_id>/expenses/<int:expense_id>')

if __name__ == "__main__":
    app.run(debug=True)