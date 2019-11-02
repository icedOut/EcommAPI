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
	inf5190.reset_orders()

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
	headers = {'Content-Type' : 'application/json'}
	json_post = dict(product=dict(id=1231,quantity=2))
	post = client.post(url_for('order_post'), data=json.dumps(json_post),headers=headers)
	status_code = client.get(url_for('order_get',order_id=1)).status_code
	assert status_code == 200
	inf5190.reset_orders()
	
def test_08_ORDER_GET_FAIL(client):
	status_code = client.get(url_for('order_get',order_id=99999)).status_code
	assert status_code == 404
	
def test_09_ORDER_PUT_NO_EMAIL(client):
	headers = {'Content-Type' : 'application/json'}
	json_post = dict(product=dict(id=1231,quantity=2))
	post = client.post(url_for('order_post'), data=json.dumps(json_post),headers=headers)
	data = dict(order=dict(shipping_information=dict(country='canada',province='QC')))
	response = client.put(url_for('order_put',order_id=1),data=json.dumps(data),headers=headers)
	status_code = response.status_code
	text_response=response.get_json()
	assert status_code == 422
	assert text_response == {
    "errors": {
        "shipping_information": {
            "code": "missing-fields",
            "name": "Il manque un ou plusieurs champs qui sont obligatoire"
        }
    }
}
	inf5190.reset_orders()
	
def test_10_ORDER_PUT_ORDER_NOT_FOUND(client):
	headers = {'Content-Type' : 'application/json'}
	data = dict(order=dict(email="caissy.jean-philippe@uqam.ca",shipping_information=dict(country='canada', address='201, rue president kennedy' , postal_code = 'H2X 3Y7' , city = 'Montreal' , province='QC')))
	response = client.put(url_for('order_put',order_id=99999),data=json.dumps(data),headers=headers).status_code
	assert response == 404
	
def test_11_ORDER_PUT_SHIPPING_INFO_SUCCESS(client):
	headers = {'Content-Type' : 'application/json'}
	json_post = dict(product=dict(id=1231,quantity=2))
	post = client.post(url_for('order_post'), data=json.dumps(json_post),headers=headers)
	data = dict(order=dict(email="caissy.jean-philippe@uqam.ca",shipping_information=dict(country='canada', address='201, rue president kennedy' , postal_code = 'H2X 3Y7' , city = 'Montreal' , province='QC')))
	response = client.put(url_for('order_put',order_id=1),data=json.dumps(data),headers=headers).status_code
	assert response == 302
	inf5190.reset_orders()

def test_12_ORDER_PUT_CREDIT_CARD_SUCCESS(client):
	headers = {'Content-Type' : 'application/json'}
	json_post = dict(product=dict(id=1231,quantity=2))
	post = client.post(url_for('order_post'), data=json.dumps(json_post),headers=headers)
	data = dict(order=dict(email="caissy.jean-philippe@uqam.ca",shipping_information=dict(country='canada', address='201, rue president kennedy' , postal_code = 'H2X 3Y7' , city = 'Montreal' , province='QC')))
	response = client.put(url_for('order_put',order_id=1),data=json.dumps(data),headers=headers).status_code
	data2 = dict(credit_card=dict(name="john doe",number="4242 4242 4242 4242",expiration_year=2024,cvv="123",expiration_month=9))
	response2 = client.put(url_for('order_put',order_id=1),data=json.dumps(data2),headers=headers).status_code
	assert response2 == 302
	inf5190.reset_orders()
		
	
def test_13_ORDER_PUT_CREDIT_CARD_ALREADY_PAID(client):
	headers = {'Content-Type' : 'application/json'}
	json_post = dict(product=dict(id=1231,quantity=2))
	post = client.post(url_for('order_post'), data=json.dumps(json_post),headers=headers)
	data = dict(order=dict(email="caissy.jean-philippe@uqam.ca",shipping_information=dict(country='canada', address='201, rue president kennedy' , postal_code = 'H2X 3Y7' , city = 'Montreal' , province='QC')))
	response = client.put(url_for('order_put',order_id=1),data=json.dumps(data),headers=headers).status_code
	data2 = dict(credit_card=dict(name="john doe",number="4242 4242 4242 4242",expiration_year=2024,cvv="123",expiration_month=9))
	response2 = client.put(url_for('order_put',order_id=1),data=json.dumps(data2),headers=headers)
	response3 = client.put(url_for('order_put',order_id=1),data=json.dumps(data2),headers=headers)
	assert response3.status_code == 422
	assert response3.get_json() == {
   "errors" : {
       "order": {
           "code": "already-paid",
           "name": "La commande a déjà été payée."
       }
   }
}
	inf5190.reset_orders()
	
def test_14_ORDER_PUT_CREDIT_CARD_DECLINED_CARD(client):
	headers = {'Content-Type' : 'application/json'}
	json_post = dict(product=dict(id=1231,quantity=2))
	post = client.post(url_for('order_post'), data=json.dumps(json_post),headers=headers)
	data = dict(order=dict(email="caissy.jean-philippe@uqam.ca",shipping_information=dict(country='canada', address='201, rue president kennedy' , postal_code = 'H2X 3Y7' , city = 'Montreal' , province='QC')))
	response = client.put(url_for('order_put',order_id=1),data=json.dumps(data),headers=headers).status_code
	data2 = dict(credit_card=dict(name="john doe",number="4000 0000 0000 0002",expiration_year=2024,cvv="123",expiration_month=9))
	response2 = client.put(url_for('order_put',order_id=1),data=json.dumps(data2),headers=headers)
	assert response2.status_code == 422
	assert response2.get_json() == {
    "errors": {
        "credit_card": {
            "code": "card-declined",
            "name": "La carte de crédit a été déclinée."
        }
    }
}
	inf5190.reset_orders()
	
def test_15_ORDER_PUT_CREDIT_CARD_INVALID_NUMBER(client):
	headers = {'Content-Type' : 'application/json'}
	json_post = dict(product=dict(id=1231,quantity=2))
	post = client.post(url_for('order_post'), data=json.dumps(json_post),headers=headers)
	data = dict(order=dict(email="caissy.jean-philippe@uqam.ca",shipping_information=dict(country='canada', address='201, rue president kennedy' , postal_code = 'H2X 3Y7' , city = 'Montreal' , province='QC')))
	response = client.put(url_for('order_put',order_id=1),data=json.dumps(data),headers=headers).status_code
	data2 = dict(credit_card=dict(name="john doe",number="4000 0000 0000 2222",expiration_year=2024,cvv="123",expiration_month=9))
	response2 = client.put(url_for('order_put',order_id=1),data=json.dumps(data2),headers=headers)
	assert response2.status_code == 422
	assert response2.get_json() == {
    "errors": {
        "credit_card": {
            "code": "incorrect-number",
            "name": "Le numéro de la carte de crédit est invalide"
        }
    }
}
	inf5190.reset_orders()
	
def test_16_ORDER_PUT_CREDIT_CARD_NO_INFO_ERROR(client):
	headers = {'Content-Type' : 'application/json'}
	json_post = dict(product=dict(id=1231,quantity=2))
	post = client.post(url_for('order_post'), data=json.dumps(json_post),headers=headers)
	data = dict(credit_card=dict(name="john doe",number="4242 4242 4242 4242",expiration_year=2024,cvv="123",expiration_month=9))
	response = client.put(url_for('order_put',order_id=1),data=json.dumps(data),headers=headers)
	assert response.status_code == 422
	assert response.get_json() == {
    "errors": {
        "order": {
            "code": "missing-fields",
            "name": "Les informations du clients sont nécessaire avant d'appliquer une carte de crédit"
        }
    }
}
	inf5190.reset_orders()
	
	
	