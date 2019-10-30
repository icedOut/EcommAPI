from inf5190 import init_db
import pytest

@pytest.fixture
def app():
    app = init_db()
    return app
	

def test_01_GET(client):
    assert client.get(url_for('/')).status_code == 200	