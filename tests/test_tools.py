import pytest

from tools import calculate, get_time, get_weather, send_email


def test_calculate_basic():
    assert calculate("12 * 7 + 3") == "87"


def test_calculate_division():
    assert calculate("10 / 4") == "2.5"


def test_calculate_unary_negative():
    assert calculate("-5 + 2") == "-3"


def test_calculate_rejects_non_arithmetic():
    with pytest.raises(ValueError):
        calculate("__import__('os').system('echo hi')")


def test_calculate_division_by_zero():
    with pytest.raises(ValueError):
        calculate("1 / 0")


def test_get_time_default_utc():
    assert "UTC" in get_time()


def test_get_time_valid_timezone():
    assert "Asia/Kolkata" in get_time("Asia/Kolkata")


def test_get_time_invalid_timezone():
    with pytest.raises(ValueError):
        get_time("Not/AZone")


def test_send_email_valid():
    result = send_email("john@example.com", "Meeting", "See you then")
    assert "john@example.com" in result
    assert "Meeting" in result


def test_send_email_invalid_address():
    with pytest.raises(ValueError):
        send_email("not-an-email", "Subject")


def test_send_email_empty_subject():
    with pytest.raises(ValueError):
        send_email("john@example.com", "")


class _FakeResponse:
    def __init__(self, json_data):
        self._json_data = json_data

    def raise_for_status(self):
        pass

    def json(self):
        return self._json_data


def test_get_weather_success(monkeypatch):
    def fake_get(url, params=None, timeout=None):
        if "geocoding" in url:
            return _FakeResponse({"results": [{"name": "Paris", "latitude": 48.85, "longitude": 2.35}]})
        return _FakeResponse({"current_weather": {"temperature": 18.5, "weathercode": 1}})

    monkeypatch.setattr("tools.requests.get", fake_get)
    result = get_weather("Paris")
    assert "Paris" in result
    assert "18.5" in result
    assert "mainly clear" in result


def test_get_weather_city_not_found(monkeypatch):
    def fake_get(url, params=None, timeout=None):
        return _FakeResponse({"results": []})

    monkeypatch.setattr("tools.requests.get", fake_get)
    with pytest.raises(ValueError):
        get_weather("Nowhereville")
