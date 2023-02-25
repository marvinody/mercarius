from mercarius import search, SearchItemStatus

import json

merch = list(search('plush touhou', status=SearchItemStatus.ON_SALE))

print("total merch count: ", len(merch))

print('All IDs in query:')
print('\n'.join([x["id"] for x in merch]))


print('All keys in a single item:')
print(json.dumps(merch[0], indent=2))
