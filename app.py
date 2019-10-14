import json
import datetime

import click
from flask import Flask, jsonify, request, abort, redirect, url_for, Response
import peewee as p
from playhouse.shortcuts import model_to_dict, dict_to_model
from urllib.error import HTTPError
from urllib.request import Request, urlopen

app = Flask(__name__)

db = p.SqliteDatabase("db.sqlite")

class JSONField(p.TextField):
    """
    Class to "fake" a JSON field with a text field. Not efficient but works nicely
    """
    def db_value(self, value):
        """Convert the python value for storage in the database."""
        return value if value is None else json.dumps(value)

    def python_value(self, value):
        """Convert the database value to a pythonic value."""
        return value if value is None else json.loads(value)

class BaseModel(p.Model):
    class Meta:
        database = db

class Product(BaseModel):
    id=p.IntegerField(primary_key=True)
    in_stock = p.BooleanField(default=True)
    description= p.TextField()
    price = p.DoubleField()
    image = p.TextField()
    name = p.TextField()
    weight = p.IntegerField()

class Order(BaseModel):
    id=p.AutoField(primary_key=True)
    product = JSONField(p.TextField(null=True))
    creditCard=JSONField(default={})
    shippingInformation=JSONField(default={})
    transaction= JSONField(default={})
    shippingPrice=p.DoubleField(default=0)
    email=p.TextField(null=True)
    paid=p.BooleanField(default=False)
    total_price=p.DoubleField(default=0)

def perform_request(uri, method="GET", data=None):
    request = Request('https://caissy.dev/shops/{0}'.format(uri))
    request.method = method
    request.add_header("content-type", "application/json")

    if data:
        request.data = json.dumps(data).encode('utf-8')

    try:
        with urlopen(request) as response:
            data = response.read()
            headers = response.headers

            if headers['content-type'] == "application/json":
                 return json.loads(data)
            else:
                return None
    except HTTPError as e:
        code = e.code
        headers = e.headers
        data = e.read()

        error = ApiError()
        error.code = code
        if headers['content-type'] == "application/json":
            error.content = json.loads(data)

        raise error

def get_products():
	json_products = perform_request("products")
	for product in json_products['products']:
		my_product = dict_to_model(Product, product)
		my_product.save(force_insert=True)

@app.route('/', methods=['GET'])
def products_get():
    products = []

    for product in Product.select():
    	products.append(model_to_dict(product))

    return jsonify(products)

@app.route('/order', methods=['POST'])
def order_post():
	json_payload = []
	if not request.is_json:
		return abort(400)
	try:
		json_payload = request.json['productz']
	except KeyError:
		return jsonify({"code": "missing-fields", "name": "La création d'une commande nécessite un produit"}), 422

	product = Product.get_or_none(json_payload.id)
	
	new_order = Order()
	new_order.product = json_payload
	new_order.save(force_insert=True)
	return Response("Location: /order/" + str(new_order.id), 302)

@app.route('/order/<int:order_id>', methods=['GET'])
def order_get(order_id):
	order = Order.get_or_none(order_id)
	if order_id is None:
		return abort(404)
	return jsonify(model_to_dict(order))

@app.cli.command("init-db")
def init_db():
    db.create_tables([Product, Order])
    get_products()
