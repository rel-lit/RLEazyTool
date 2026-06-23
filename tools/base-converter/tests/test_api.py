import pytest
from fastapi.testclient import TestClient
from backend.main import app


client = TestClient(app)


def test_root_and_static():
    r = client.get('/')
    assert r.status_code == 200
    assert '计组计算题可视化工具' in r.text
    r2 = client.get('/js/app.js')
    assert r2.status_code == 200


def test_api_convert_base():
    r = client.post('/api/convert/base', json={
        'value': '13.625', 'from_base': 10, 'to_base': 2
    })
    assert r.status_code == 200
    data = r.json()
    assert data['result'] == '1101.101'
    assert any('除基取余' in step['title'] for step in data['steps'])


def test_api_convert_machine():
    r = client.post('/api/convert/machine', json={'value': '-13', 'width': 8})
    assert r.status_code == 200
    data = r.json()
    assert data['twos_complement'] == '11110011'


def test_api_compute_fixed():
    r = client.post('/api/compute/fixed', json={
        'x': '5', 'y': '3', 'width': 8, 'operation': 'add'
    })
    assert r.status_code == 200
    data = r.json()
    assert data['result_decimal'] == '8'


def test_api_compute_float():
    r = client.post('/api/compute/float', json={
        'x_mantissa': '+0.110101', 'x_exponent': '+0011',
        'y_mantissa': '-0.111010', 'y_exponent': '+0010',
        'operation': 'add'
    })
    assert r.status_code == 200
    data = r.json()
    assert data['normalized'] == '[000010 , 0.110000]'


def test_api_machine_auto_fraction():
    # Decimal value should auto-detect fraction mode
    r = client.post('/api/convert/machine', json={
        'value': '-0.625', 'width': 8, 'is_fraction': False, 'double_sign': False
    })
    assert r.status_code == 200
    data = r.json()
    assert data['twos_complement'] == '10110000'


def test_api_bad_request_returns_400():
    r = client.post('/api/convert/machine', json={
        'value': '999', 'width': 4, 'is_fraction': False, 'double_sign': False
    })
    assert r.status_code == 400
