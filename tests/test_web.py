import re

from fastapi.testclient import TestClient

import careertracker
from careertracker.web.app import app

client = TestClient(app)


def test_home_page_renders():
    response = client.get("/")
    assert response.status_code == 200
    assert "Career Mode Tracker" in response.text
    assert f"v{careertracker.__version__}" in response.text


def test_home_page_loads_local_htmx_and_css():
    html = client.get("/").text
    assert "/static/htmx.min.js" in html
    assert "/static/app.css" in html
    assert 'hx-get="/status"' in html


def test_htmx_and_css_are_served_locally():
    htmx = client.get("/static/htmx.min.js")
    assert htmx.status_code == 200
    assert "htmx" in htmx.text[:200]
    assert client.get("/static/app.css").status_code == 200


def test_status_fragment_is_html_fragment_not_full_page():
    response = client.get("/status")
    assert response.status_code == 200
    assert "Aplikacja działa" in response.text
    assert re.search(r"\d\d:\d\d:\d\d", response.text)
    assert "<html" not in response.text


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": careertracker.__version__}


def test_unknown_page_returns_404():
    assert client.get("/nie-ma-takiej-strony").status_code == 404
