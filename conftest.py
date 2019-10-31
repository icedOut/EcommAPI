import inf5190
import pytest

@pytest.fixture
def app():
	app.debug = True
	return inf5190.app

	

