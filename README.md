# Mercari US API Wrapper

## Quick wrapper around US API

Mercari US uses a graphql endpoint which seems locked down in the frontend in production environment. Instead of using POST requests like most graphql, they're using [Automatic Persisted Queries](https://www.apollographql.com/docs/apollo-server/performance/apq/) for efficiency. What does that mean? Well, it means we can't custom craft properties to return which would let us make a query that makes it easier for their servers and requests less properties than we would use. But since I'm not gonna invest much time into reversing their graphql endpoint, I'll use their persisted queries in this project for now.

Essentially, a long hash will correspond to a preset schema to search for. In our case, we use `5b7b667eaf8a796406058428fa5df18e7cecd5229702ee0753a091d980884d38` for a `searchFacetQuery` since it's the first one that came up during my website usage. Looking into their source code, there's about ~20 other queries we can use but that will take some time to work out if they're needed and this seems to be good enough.

One weird inconsistency I saw during my progress was that the count returned back varies wildly and is really annoying...

## Features
Currently supported, you can pass in a query, and item status (on sale, sold out, or all) as well as a 'soft limit.' I call it soft because if you specify 100, you may receive up to 120, but you should never receive the limit + 30 ever. It's just easier to write this way and should be good enough for people. If you want to only look up 1 page, just pass a limit of 30 or lower and you'll get 30 results page if there's more than 30 listings available online.

By default, if you iterate over the list, it'll continuously query and fetch all of them.

To access properties of the items, they're all JSON objects and not coded to a class so you'll need to acces them all by in a similar fashion to `item["price"]`.

For a sample script to see how to quickly run it and test if it's working:

```python
from mercarius import search, SearchItemStatus

import json

merch = list(search('plush touhou', status=SearchItemStatus.ON_SALE))

print("total merch count: ", len(merch))

print('All IDs in query:')
print('\n'.join([x["id"] for x in merch]))


print('All keys in a single item:')
print(json.dumps(merch[0], indent=2))

```

It'll print out a blob of JSON so you can see all the available properties on the item object.

**Note, you're not guaranteed to have all unique items and may see duplicates.** I recommend to run the final list through a duplicate checker using the id property just to be safe. During my testing it was pretty random.



# Development

Clone this repo, install the dependencies in `requirement.txt` and off you go.

## Deploying / Publishing

- `python setup.py sdist`

- `twine upload dist/mercari-<version>.tar.gz`