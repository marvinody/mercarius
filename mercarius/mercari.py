from enum import Enum
from hashlib import sha256
import json
import os
import re

import requests

rootURL = "https://www.mercari.com/"
# rootProductURL = "https://jp.mercari.com/item/"
searchURL = "{}v1/api".format(rootURL)
initializeURL = "{}v1/initialize".format(rootURL)

USER_AGENT = "mercarius wrapper v2"


def generateAccessToken():
    resp = requests.get(initializeURL, headers={
        "User-Agent": USER_AGENT
    })

    data = resp.json()

    # not checking these now, but at the time of writing this code
    # these tokens expire 7 days after they're created...should be fine
    token = data["accessToken"]

    return token


# probably a better way to handle this transformation but
# hardcoding the arrays didn't work on first iteration
class SearchItemStatus(Enum):
    ALL = 1
    ON_SALE = 2
    SOLD_OUT = 3

    # following array values were pulled from looking at their values in UI
    def toMercariKey(self):

        if self == self.ALL:
            return []
        elif self == self.ON_SALE:
            return [1]
        elif self == self.SOLD_OUT:
            return [2, 3]


class ResultSet:
    def __init__(self, resp, limit, variables, status, token) -> None:
        self._variables = variables
        self._limit = limit
        self._resps = [resp]
        self._curPageItems = resp["data"]["search"]["itemsList"]
        self.nextKey = resp["data"]["search"]["nextKey"]
        self.query = self._variables["criteria"]["query"]
        self.status = status
        self.token = token

    def __iter__(self):
        for rawItem in self._curPageItems:
            yield rawItem

        count = len(self._curPageItems)

        while count < self._limit and self._curPageItems:
            resp, _ = _search(self.query, status=self.status,
                              startKey=self.nextKey, accessToken=self.token)
            self._curPageItems = resp["data"]["search"]["itemsList"]

            count += len(self._curPageItems)
            newKey = resp["data"]["search"]["nextKey"]
            self.nextKey = newKey

            for rawItem in self._curPageItems:
                yield rawItem


def loadSearchFacetQuery():
    file_dir = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(file_dir, 'searchFacetQuery.graphql')
    with open(file=file_path) as f:
        return f.read()


def _search(query, status: SearchItemStatus = SearchItemStatus.ON_SALE, startKey=None, accessToken=None):
    if not accessToken:
        raise ValueError("Must provide an access token")
    operationName = "searchFacetQuery"

    graphQlQuery = re.sub(' {2,}', ' ', ("".join(
        loadSearchFacetQuery().splitlines())))

    hash = sha256(graphQlQuery.encode('utf-8')).hexdigest()

    extensions = {
        "persistedQuery": {
            "version": 1,
            # this is super prone to breaking randomly and I'm not sure how to fix this permanently
            # maybe a way to lookup dynamically on start and fetch the hash we want for the operation?
            # is that even a method or call somewhere? more research needed - definitely coded into JS if not
            "sha256Hash": hash
        }
    }
    variables = {
        "criteria": {
            "startKey": startKey,
            "offset": 0,
            "soldItemsOffset": 0,
            "promotedItemsOffset": 0,
            "sortBy": 0,
            "length": 30,
            "query": query,
            "itemConditions": [],
            "shippingPayerIds": [],
            "sizeGroupIds": [],
            "sizeIds": [],
            "itemStatuses": status.toMercariKey(),
            "customFacets": [],
            "facets": [1, 2, 3, 5, 7, 8, 9, 10, 11, 13],
            "authenticities": [],
            "deliveryType": "all",
            "state": None,
            "locale": None,
            "shopPageUri": None,
            "withCouponOnly": None
        },
        "categoryId": 0
    }

    resp = requests.get(
        searchURL,
        params={
            "operationName": operationName,
            "extensions": json.dumps(extensions),
            "variables": json.dumps(variables),
            "query": graphQlQuery
        },
        headers={
            # some generic header is needed to prevent them instablocking us
            # the reason for mercarius is so they can track and block us if
            # we abuse it and they decide to. it's a courtesy to do
            # also, here's a funny thing - if you put "python"
            # anywhere here, it just decides to block it
            # with a varnish 403 error. isn't that fun?
            "User-Agent": USER_AGENT,
            # the new auth fix
            "authorization": "Bearer {}".format(accessToken),
            "apollo-require-preflight": "true",
        }
    )

    resp.raise_for_status()

    data = resp.json()

    if ('errors' in data):
        errorMsgs = ','.join([e["message"] for e in data["errors"]])
        raise ValueError(f"Error on query, {errorMsgs}")

    return data, variables


def search(query, status: SearchItemStatus = SearchItemStatus.ON_SALE, limit=1000):
    token = generateAccessToken()

    resp, variables = _search(query, status, accessToken=token)

    return ResultSet(resp, limit, variables, status, token)
