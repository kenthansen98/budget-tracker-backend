from flask import Flask, abort
from flask_restful import Resource, Api, reqparse, fields, marshal
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
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

api.add_resource(CategoryList, '/categories')
api.add_resource(Category, '/categories/<int:cat_id>')

if __name__ == "__main__":
    app.run(debug=True)