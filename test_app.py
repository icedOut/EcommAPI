import pytest
from flask import url_for

def test_01_GET(client):
	assert client.get(url_for('products_get')).status_code == 200
        