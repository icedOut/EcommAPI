import json
import datetime

import click
from flask import Flask, jsonify, request, abort, redirect, url_for
import peewee as p
from playhouse.shortcuts import model_to_dict, dict_to_model

app = Flask(__name__)

db = p.SqliteDatabase("db.sqlite")

class BaseModel(p.Model):
    class Meta:
        database = db


class Product(BaseModel):
    id=p.AutoField(primary_key=true)
    inStock= p.BooleanField(default=true)
    description= p.TextField()
    price = p.DoubleField()
    image = p.TextField()

class ShippingInformation(BaseModel):
    id=p.Autofield(primary_key=true)
    country=p.TextField()
    address=p.TextField()
    postalCode=p.TextField()
    city=p.TextField()
    province=p.TextField()

class Transaction(BaseModel):
    id=p.Autofield(primary_key=true)
    success=p.BooleanField()
    amount_charged=p.DoubleField()


class CreditCard(BaseModel):
    id=p.Autofield(primary_key=true)
    name=p.TextField()
    number=p.TextField()
    exipration_year=p.IntegerField()
    cvv=p.IntegerField()
    expiration_month=p.IntegerField()


class Order(BaseModel):
    id=p.AutoField(primary_key=true)
    idProduit=p.ForeignKeyField(Product, backref= "produit", null = false)
    quantity=p.IntegerField(null=false)
    creditCard=p.ForeignKeyField(CreditCard,backref="creditcard")
    shippingInformation=p.ForeignKeyField(ShippingInformation,backref="info shiping")
    transaction=p.ForeignKeyField(Transaction,backref="transactions")
    shippingPrice=p.DoubleField()
    email=p.TextField()
    paid=p.BooleanField()




    
    


@app.route('/', methods=['GET'])
def products():
    #todo

@app.route('/')

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