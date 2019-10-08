import json
import datetime

import click
from flask import Flask, jsonify, request, abort, redirect, url_for
import peewee as p
from playhouse.shortcuts import model_to_dict, dict_to_model
from urllib.error import HTTPError
from urllib.request import Request, urlopen

app = Flask(__name__)

db = p.SqliteDatabase("db.sqlite")

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

class ShippingInformation(BaseModel):
    id=p.AutoField(primary_key=True)
    country=p.TextField()
    address=p.TextField()
    postalCode=p.TextField()
    city=p.TextField()
    province=p.TextField()

class Transaction(BaseModel):
    id=p.AutoField(primary_key=True)
    success=p.BooleanField()
    amount_charged=p.DoubleField()

class CreditCard(BaseModel):
    id=p.AutoField(primary_key=True)
    name=p.TextField()
    number=p.TextField()
    exipration_year=p.IntegerField()
    cvv=p.IntegerField()
    expiration_month=p.IntegerField()

class Order(BaseModel):
    order_id=p.AutoField(primary_key=True)
    id=p.ForeignKeyField(Product, backref="product", null=False)
    quantity=p.IntegerField(null=False)
    creditCard=p.ForeignKeyField(CreditCard, backref="creditcard", null=True)
    shippingInformation=p.ForeignKeyField(ShippingInformation, backref="info shiping", null=True)
    transaction=p.ForeignKeyField(Transaction, backref="transactions", null=True)
    shippingPrice=p.DoubleField(null=True)
    email=p.TextField(null=True)
    paid=p.BooleanField(null=True)

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
	if not request.is_json:
		return abort(400)

	json_payload = request.json['product']
	new_order = dict_to_model(Order, json_payload)
	new_order.save(force_insert=True)
	return redirect(url_for("order_get", order_id=new_order.order_id))

@app.route('/order/<int:order_id>', methods=['GET'])
def order_get(order_id):
	order = Order.get_or_none(order_id)
	if order_id is None:
		return abort(404)
	return jsonify(model_to_dict(order))

@app.cli.command("init-db")
def init_db():
    db.create_tables([Product, Transaction, ShippingInformation, Order, CreditCard])
    get_products()
