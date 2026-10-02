import pytest
import requests

from crawler.http import get_text


class FakeSession:
    def __init__(self, response):
        self.response = response

    def get(self, url, timeout):
        return self.response


def make_response(status, body, headers):
    response = requests.Response()
    response.status_code = status
    response._content = body.encode()
    response.headers.update(headers)
    response.url = "https://example.com/list"
    response.reason = "Forbidden"
    return response


def test_http_error_says_who_blocked_and_why():
    body = "<html><head><title>ERROR: The request could not be satisfied</title></head></html>"
    response = make_response(403, body, {"Server": "CloudFront", "X-Cache": "Error from cloudfront"})
    with pytest.raises(requests.HTTPError) as error:
        get_text(FakeSession(response), response.url)
    message = str(error.value)
    assert "403" in message
    assert "Error from cloudfront" in message
    assert "The request could not be satisfied" in message
