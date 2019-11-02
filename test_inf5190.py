import pytest
import json
import inf5190
from flask import url_for , jsonify


@pytest.fixture
def app():
	app = inf5190.app
	return app

def test_01_PRODUCTS_GET(client):
    assert client.get(url_for('products_get')).status_code == 200

def test_02_ORDER_POST_SUCCESS(client):
	headers = {'Content-Type' : 'application/json'}
	data = dict(product=dict(id=1231,quantity=2))
	status_code = client.post(url_for('order_post'), data=json.dumps(data),headers=headers).status_code
	assert status_code == 302

def test_03_ORDER_POST_0_QUANTITY(client):
	headers = {'Content-Type' : 'application/json'}
	data = dict(product=dict(id=1231,quantity=0))
	status_code = client.post(url_for('order_post'), data=json.dumps(data),headers=headers).status_code
	assert status_code == 422

def test_04_ORDER_POST_NO_PRODUCT_ID(client):
	headers = {'Content-Type' : 'application/json'}
	data = dict(product=dict(id=121,quantity=0))
	status_code = client.post(url_for('order_post'), data=json.dumps(data),headers=headers).status_code
	assert status_code == 422

def test_05_ORDER_POST_NO_STOCK(client):
	headers = {'Content-Type' : 'application/json'}
	data = dict(product=dict(id=1232,quantity=1))
	status_code = client.post(url_for('order_post'), data=json.dumps(data),headers=headers).status_code
	assert status_code == 422

def test_06_ORDER_POST_MISSING_FIELD(client):
	headers = {'Content-Type' : 'application/json'}
	data = dict(product=dict(id=1231))
	status_code = client.post(url_for('order_post'), data=json.dumps(data),headers=headers).status_code
	assert status_code == 422
	
def test_07_ORDER_GET_SUCCESS(client):
	status_code = client.get(url_for('order_get',order_id=1)).status_code
	assert status_code == 200
	
def test_08_ORDER_PUT_NO_EMAIL(client):
	headers = {'Content-Type' : 'application/json'}
	data = dict(order=dict(shipping_information=dict(country='canada',province='QC')))
	status_code = client.put(url_for('order_put',order_id=1),data=json.dumps(data),headers=headers).status_code
	assert status_code == 422
	
def test_09_ORDER_PUT_SHIPPING_INFO_SUCCESS(client):
	headers = {'Content-Type' : 'application/json'}
	data = dict(order=dict(email="caissy.jean-philippe@uqam.ca",shipping_information=dict(country='canada', address='201, rue president kennedy' , postal_code = 'H2X 3Y7' , city = 'Montreal' , province='QC')))
	response = client.put(url_for('order_put',order_id=1),data=json.dumps(data),headers=headers).status_code
	assert response == 302
	
def test_10_ORDER_PUT_ORDER_NOT_FOUND(client):
	headers = {'Content-Type' : 'application/json'}
	data = dict(order=dict(email="caissy.jean-philippe@uqam.ca",shipping_information=dict(country='canada', address='201, rue president kennedy' , postal_code = 'H2X 3Y7' , city = 'Montreal' , province='QC')))
	response = client.put(url_for('order_put',order_id=999),data=json.dumps(data),headers=headers).status_code
	assert response == 404
	
	
	
