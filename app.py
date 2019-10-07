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
    #todo


class Order(BaseModel):
    #todo


@app.route('/', methods=['GET'])
def products():
    #todo

@app.route('/order', methods=['POST'])
def order_create():
    #todo

@app.route('/order/<int:order_id>', methods=['GET'])
def order_get(id):
    #todo

@app.route('/order/<int:order_id>', methods=['PUT'])
def order_put(id):
    #todo    


@app.cli.command("init-db")
def init_db():
    #todo