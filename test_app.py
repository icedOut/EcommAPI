import pytest
from flask import url_for
import json


def test_01_GET(client):
	assert client.get(url_for('products_get')).status_code == 200
	
def test_02_POST(client):
	assert client.post(url_for('order_post'), json={"product":{"id":1235,"quantity":2}}).status_code == 302       