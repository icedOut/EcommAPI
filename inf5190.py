# coding=utf-8
import json
import datetime
import time
import click
from flask import Flask, jsonify, request, abort, redirect, url_for, Response
import peewee as p
from playhouse.shortcuts import model_to_dict, dict_to_model
import urllib
from urllib.request import Request, urlopen
import os
import psycopg2
from playhouse.db_url import connect
import redis
from rq import Queue, Worker, Connection


if 'HEROKU' in os.environ or 'DYNO' in os.environ or 'I_AM_HEROKU' in os.environ:
	db =  connect(os.environ.get('DATABASE_URL'))	
else:
	db = p.PostgresqlDatabase(os.environ['DB_NAME'], user=os.environ['DB_USER'], password=os.environ['DB_PASSWORD'], host=os.environ['DB_HOST'], port=os.environ['DB_PORT'])
db_redis = redis.from_url(os.environ['REDIS_URL'])
app = Flask(__name__)

queue= Queue(connection=db_redis)
	

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
	products = JSONField(p.TextField(null=True))
	credit_card=JSONField(default={})
	shipping_information=JSONField(default={})
	transaction= JSONField(default={})
	shipping_price=p.DoubleField(default=0)
	being_paid=p.BooleanField(default=False)
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
		data = e.read().decode()
		return json.loads(data)

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
		print('pas jason')
		return abort(400)
	if('product' in request.json):
		return order_one_product(request)
	elif('products' in request.json):
		return order_multiple_product(request)
	else:
		return error_message("product", "missing-fields", "La création d'une commande nécessite un produit"), 422

def order_multiple_product(request):
	try:
		json_payload = request.json['products']
		for i in json_payload:
			quantity = i['quantity']
			product_id = i['id']
			if quantity <= 0:
				return error_message("product", "out-of-inventory", "Le produit demandé n'est pas en inventaire"), 422

			product = Product.get_or_none(product_id)

			if product is None or not product.in_stock:
				return error_message("product", "out-of-inventory", "Le produit demandé n'est pas en inventaire"), 422
	except KeyError:
		return error_message("product", "missing-fields", "La création d'une commande nécessite un produit"), 422
	new_order = Order()
	new_order.products = json_payload
	calculate_price(new_order)
	new_order.save(force_insert=True)

	return redirect(url_for("order_get", order_id=new_order.id))


def order_one_product(request):
	try:
		json_payload = request.json['product']
		quantity = json_payload['quantity']
		product_id = json_payload['id']
	except KeyError:
		return error_message("product", "missing-fields", "La création d'une commande nécessite un produit"), 422

	if quantity <= 0:
		return error_message("product", "out-of-inventory", "Le produit demandé n'est pas en inventaire"), 422

	product = Product.get_or_none(product_id)

	if product is None or not product.in_stock:
		return error_message("product", "out-of-inventory", "Le produit demandé n'est pas en inventaire"), 422

	new_order = Order()
	new_order.products = json_payload
	calculate_price(new_order)
	new_order.save(force_insert=True)

	return redirect(url_for("order_get", order_id=new_order.id))

@app.route('/order/<int:order_id>', methods=['PUT'])
def order_put(order_id):
	if not request.is_json:
		return abort(400)
	order = Order.get_or_none(order_id)
	if(order == None):
		return error_message("order", "no-order-found", "Aucune commande avec ce ID a été trouvée"), 404	
	json_payload = request.json
	if 'order' in json_payload:
		if 'credit_card' in json_payload:				
			return error_message("shipping_information", "bad-request", "On ne peut pas fournir un email et shipping_information avec une carte de crédit"), 422
		return order_put_shipping_information(json_payload, order_id)
	elif 'credit_card' in json_payload:
		if(order.being_paid):
			return Response(409)
		order.being_paid=True
		order.save()
		job = queue.enqueue(order_put_credit_card, json_payload, order_id)
		return redirect(url_for('verify_job', job_id=job.id))
	else:
		return error_message("order", "missing-fields", "Aucune information de commande a été trouvée"), 422

@app.route('/order/<int:order_id>', methods=['GET'])
def order_get(order_id):
	order = Order.get_or_none(order_id)
	if order is None:
		return error_message("order", "no-order-found", "Aucune commande avec ce ID a été trouvée"), 404

	if(order.being_paid):
		return Response("",status=202)

	if(db_redis.exists(order_id) != 0):
		print("Cached order  \n")
		data = db_redis.get(order_id)
		return json.loads(data)
	print(" Order not in cache")
	return jsonify(dict(order=model_to_dict(order)))

def error_message(field, code, name):
	return jsonify({ "errors" : { field : {"code" : code, "name" : name}}})

def calculate_price(order):
	total_weight = 0

	if(isinstance(order.products, list)):
		for i in order.products:
			order.total_price += Product.get_or_none(i['id']).price * i['quantity'] 
			total_weight += Product.get_or_none(i['id']).weight * i['quantity']
	else:
		order.total_price += Product.get_or_none(order.products['id']).price * order.products['quantity']
		total_weight += Product.get_or_none(order.products['id']).weight * order.products['quantity']
	if total_weight < 500:
		order.shipping_price = 5
	elif total_weight < 2000:
		order.shipping_price = 10
	else:
		order.shipping_price = 25

def order_put_shipping_information(json_payload, order_id):
	try:
		json_payload = json_payload['order']
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
	order.save()
	return redirect(url_for("order_get", order_id=order.id))

def order_put_credit_card(json_payload, order_id):
	
	order = Order.get_or_none(order_id)

	if(order.paid == True):
		return error_message("order", "already-paid", "La commande a déjà été payée."), 422

	if(order.shipping_information == {}):
		return error_message("order", "missing-fields", "Les informations du clients sont nécessaire avant d'appliquer une carte de crédit"), 422

	try:
		credit_card = json_payload['credit_card']
		name = credit_card['name']
		number = credit_card['number']
		expiration_year = credit_card['expiration_year']
		cvv = credit_card['cvv']
		expiration_month = credit_card['expiration_month']
	except KeyError:
		return error_message("credit_card", "missing-fields", "Il manque un ou plusieurs champs qui sont obligatoire"), 422
		
	# INSÉRER L'APPEL DISTANT ICI AVEC L'OBJECT CREDIT_CARD 
	amount_charged = int(order.total_price) + int(order.shipping_price)
	data = dict(credit_card=credit_card,amount_charged = amount_charged)

	r = perform_request("pay" ,"POST", data)

	if('transaction' in r):
		order.credit_card = r['credit_card']
		order.transaction = r['transaction']
		order.paid = True
		order.being_paid = False
		order.save()
		order_load = json.dumps(model_to_dict(order))
		db_redis.set(order.id,order_load,ex=3600)
		return redirect(url_for("order_get", order_id=order.id))
	else:
		order.being_paid = False
		order.save()
		return jsonify(r), 422

@app.cli.command("init-db")
def init_db():
	db.create_tables([Product, Order])
	get_products()
 
def reset_orders():
	for order in Order().select():
		order.delete_instance()

@app.route("/job/<string:job_id>")
def verify_job(job_id):
	job = queue.fetch_job(job_id)
	if not job.is_finished:
		return Response("", status=202)
	return job.result

@app.cli.command("worker")
def rq_worker():
	worker = Worker([queue], connection=db_redis)
	worker.work()