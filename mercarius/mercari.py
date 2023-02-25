from enum import Enum

import json

import requests

rootURL = "https://www.mercari.com/"
# rootProductURL = "https://jp.mercari.com/item/"
searchURL = "{}v1/api".format(rootURL)


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
    def __init__(self, resp, limit, variables, status) -> None:
        self._variables = variables
        self._limit = limit
        self._resps = [resp]
        self._curPageItems = resp["data"]["search"]["itemsList"]
        self.nextKey = resp["data"]["search"]["nextKey"]
        self.query = self._variables["criteria"]["query"]
        self.status = status

    def __iter__(self):
        for rawItem in self._curPageItems:
            yield rawItem

        count = len(self._curPageItems)
        while not self.nextKey == '0' and count < self._limit:
            resp, _ = _search(self.query, status=self.status,
                              startKey=self.nextKey)
            self._curPageItems = resp["data"]["search"]["itemsList"]

            count += len(self._curPageItems)
            newKey = resp["data"]["search"]["nextKey"]
            self.nextKey = newKey

            for rawItem in self._curPageItems:
                yield rawItem



def _search(query, status: SearchItemStatus = SearchItemStatus.ON_SALE, startKey=None):
    operationName = "searchFacetQuery"
    extensions = {
        "persistedQuery": {
            "version": 1,
            "sha256Hash": "5b7b667eaf8a796406058428fa5df18e7cecd5229702ee0753a091d980884d38"
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
            "variables": json.dumps(variables)
        },
        headers={
            # some generic header is needed to prevent them instablocking us
            # the reason for mercarius is so they can track and block us if
            # we abuse it and they decide to. it's a courtesy to do
            # also, here's a funny thing - if you put "python"
            # anywhere here, it just decides to block it
            # with a varnish 403 error. isn't that fun?
            "User-Agent": "mercarius wrapper"
        }
    )

    return resp.json(), variables

def DupCheckers(resp):
    data = resp
    unique_ids = set()
    filtered_data = []
    id_counts = {}

    # Iterate over the original data
    for item in data:
        # Check if the "id" key is already in the set of unique IDs
        if item["id"] not in unique_ids:
            # If it's not, add the ID to the set and add the item to the filtered data
            unique_ids.add(item["id"])
            filtered_data.append(item)
        
        if item["id"] not in id_counts:
        # If it's not, add the ID to the dictionary with a count of 1
            id_counts[item["id"]] = 1
        else:
            # If it's already in the dictionary, increment the count for the ID
            id_counts[item["id"]] += 1

    total_duplicates = sum(count - 1 for count in id_counts.values())
    # Dump the filtered data as a JSON string
    print(f"Number of Dups:{total_duplicates}")
    filtered_json_str = json.dumps(filtered_data)
    return filtered_data


def search(query, status: SearchItemStatus = SearchItemStatus.ON_SALE, limit=1000):
    resp, variables = _search(query, status)
    resp, variables = DupCheckers(resp, variables)
    return ResultSet(resp, limit, variables, status)
