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

get_products()

class BaseModel(p.Model):
    class Meta:
        database = db

class Product(BaseModel):
    id=p.AutoField(primary_key=True)
    inStock= p.BooleanField(default=True)
    description= p.TextField()
    price = p.DoubleField()
    image = p.TextField()

class ShippingInformation(BaseModel):
    id=p.Autofield(primary_key=True)
    country=p.TextField()
    address=p.TextField()
    postalCode=p.TextField()
    city=p.TextField()
    province=p.TextField()

class Transaction(BaseModel):
    id=p.Autofield(primary_key=True)
    success=p.BooleanField()
    amount_charged=p.DoubleField()

class CreditCard(BaseModel):
    id=p.Autofield(primary_key=True)
    name=p.TextField()
    number=p.TextField()
    exipration_year=p.IntegerField()
    cvv=p.IntegerField()
    expiration_month=p.IntegerField()

class Order(BaseModel):
    id=p.AutoField(primary_key=True)
    idProduit=p.ForeignKeyField(Product, backref= "produit", null = False)
    quantity=p.IntegerField(null=False)
    creditCard=p.ForeignKeyField(CreditCard,backref="creditcard")
    shippingInformation=p.ForeignKeyField(ShippingInformation,backref="info shiping")
    transaction=p.ForeignKeyField(Transaction,backref="transactions")
    shippingPrice=p.DoubleField()
    email=p.TextField()
    paid=p.BooleanField()

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

	for product in json_products:
		product = dict_to_model(Product, product)
		product.save()

@app.route('/', methods=['GET'])
def products():
    products = []
    for product in Products.select():
    	products.append(model_to_dict(product))

    return jsonify(products)

@app.route('/order', methods=['POST'])
def order_create():
    #todo

@app.route('/order/<int:order_id>', methods=['GET'])
def order_get(id):
    order = Order.get_or_none(id)
    if order_id is None;
        return abort(404)

@app.route('/order/<int:order_id>', methods=['PUT'])
def order_put(id):
    #todo    

@app.cli.command("init-db")
def init_db():
    #todo
