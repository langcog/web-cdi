import requests
from django.conf import settings


def cdi_cat_api(query_string):
    resp = requests.get(settings.CAT_API_BASE_URL + query_string)
    if resp.status_code != 200:
        # This means something went wrong.
        print("GET /tasks/ {}".format(resp.status_code))

    return resp.json()
