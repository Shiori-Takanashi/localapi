import pytest
from flask import Flask
from your_module_name import app  # ← 実際のモジュール名に書き換える

@pytest.fixture
def client():
    app.testing = True
    return app.test_client()

def test_get_db_species_success(client):
    res = client.get("/db/1")  # 1番のポケモンがDBにある前提
    assert res.status_code == 200
    data = res.get_json()
    assert isinstance(data, dict)
    assert "name" in data or "ja" in data  # スキーマに応じて調整

def test_get_db_species_not_found(client):
    res = client.get("/db/99999")  # 存在しないID
    assert res.status_code == 404
    data = res.get_json()
    assert "error" in data

def test_get_json_file_success(client):
    res = client.get("/json/1")  # 1.json が存在することが前提
    assert res.status_code == 200
    data = res.get_json()
    assert isinstance(data, dict)

def test_get_json_file_not_found(client):
    res = client.get("/json/9999")  # 存在しないJSON
    assert res.status_code == 404
    data = res.get_json()
    assert "error" in data

@pytest.mark.skip(reason="ランダムなsleepが入っているため省略")
def test_get_json_file_with_delay(client):
    res = client.get("/json/delay/1")
    assert res.status_code == 200
