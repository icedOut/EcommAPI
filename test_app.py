import pytest
from flask import url_for


class TestApp:

    def test_get(self, client):
        res = client.get(url_for('/'))
        assert res.status_code == 200
        