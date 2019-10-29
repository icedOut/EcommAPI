import json
import datetime
import time

import requests
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
    credit_card=JSONField(default={})
    shipping_information=JSONField(default={})
    transaction= JSONField(default={})
    shipping_price=p.DoubleField(default=0)
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
	if not request.is_json:
		return abort(400)
	try:
		json_payload = request.json['product']
		quantity = json_payload['quantity']
		product_id = json_payload['id']
	except KeyError:
		return error_message("product", "missing-fields", "La création d'une commande nécessite un produit"), 422

	if quantity <= 0:
		return error_message("product", "missing-fields", "La création d'une commande nécessite un produit"), 422

	product = Product.get_or_none(product_id)

	if product is None or not product.in_stock:
		return error_message("product", "out-of-inventory", "Le produit demandé n'est pas en inventaire"), 422

	new_order = Order()
	new_order.product = json_payload
	calculate_price(product, new_order, quantity)
	new_order.save(force_insert=True)
	return Response("Location: /order/" + str(new_order.id), 302)

@app.route('/order/<int:order_id>', methods=['PUT'])
def order_put(order_id):
	if not request.is_json:
	    return abort(400)
	
	json_payload = request.get_json()
	for key in json_payload.keys(): call_value = (key)
	
	if (call_value == 'credit_card'):
		
		try:
			credit_card = json_payload['credit_card']
			name = credit_card['name']
			number = credit_card['number']
			expiration_year = credit_card['expiration_year']
			cvv = credit_card['cvv']
			expiration_month = credit_card['expiration_month']
		except KeyError:
			return error_message("credit_card", "missing-fields", "Il manque un ou plusieurs champs qui sont obligatoire"), 422
	
			
		order = Order.get_or_none(order_id)
		order.credit_card = credit_card
		order.update()
		
		# INSÉRER L'APPEL DISTANT ICI AVEC L'OBJECT CREDIT_CARD 
		amount_charged_int = int(order.total_price)
		data= dict(credit_card=order.credit_card,amount_charged = int(order.total_price ))
		r= requests.post("https://caissy.dev/shops/pay",json=data ,timeout = 1)  # timeout = .5 N'est 
		r = r.json()
		return r
		
		
	if (call_value == 'order'):
		try: 
			json_payload = request.json['order'] 
			email = json_payload['email']
			shipping_information = json_payload['shipping_information']
			country = shipping_information['country']
			address = shipping_information['address']
			postal_code = shipping_information['postal_code']
			city = shipping_information['city']
			province = shipping_information['province']	
		except KeyError:
			return error_message("shipping_information", "missing-fields", "Il manque un ou plusieurs champs qui sont obligatoire"), 422

		order = Order.get_or_none(order_id)
		order.email = email
		order.shipping_information = shipping_information
		order.update()
		return Response("great" , 200)
	
	
	

@app.route('/order/<int:order_id>', methods=['GET'])
def order_get(order_id):
	order = Order.get_or_none(order_id)
	if order is None:
		return abort(404)
	return jsonify(model_to_dict(order))

def error_message(field, code, name):
	return jsonify({ "errors" : { field : {"code" : code, "name" : name}}})

def calculate_price(product, order, quantity):
	order.total_price = product.price * quantity 

	total_weight = product.weight * quantity 
	if total_weight < 500:
		order.shipping_price = 5
	elif total_weight < 2000:
		order.shipping_price = 10
	else:
		order.shipping_price = 25

@app.cli.command("init-db")
def init_db():
    db.create_tables([Product, Order])
    get_products()