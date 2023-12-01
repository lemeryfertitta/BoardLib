import requests


class MockResponse:
    def __init__(self, json_data={}, status_code=requests.codes.ok, text=None):
        self.json_data = json_data
        self.status_code = status_code
        self.text = text

    def json(self):
        return self.json_data

    def raise_for_status(self):
        if self.status_code != requests.codes.ok:
            raise requests.exceptions.HTTPError(
                f"HTTP {self.status_code}: {self.json_data}"
            )


class MockSession:
    def __init__(self, *responses):
        self.response_iterator = iter(responses)

    def get(self, *args, **kwargs):
        return next(self.response_iterator)

    def post(self, *args, **kwargs):
        return next(self.response_iterator)


def get_mock_request(**response_kwargs):
    return lambda *args, **kwargs: MockResponse(**response_kwargs)
