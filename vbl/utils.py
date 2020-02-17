from functools import wraps

import json
from redis import Redis
from texttable import Texttable


def cache_key(endpoint, data):
    """
    Compose cache key based on the endpoint and the data
    """
    return endpoint + '_' + json.dumps(data)


def cached(func):
    """
    Cache the result of the function call.
    Assume the result of the function can be serialized as JSON.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Generate the cache key from the function's arguments.
        _, endpoint, data = list(args)
        key = cache_key(endpoint, data)

        redis = Redis(host='localhost', port=6379, db=0)
        result = redis.get(key)

        if result is None:
            # Run the function and cache the result.
            value = func(*args, **kwargs)
            redis.set(key, json.dumps(value))
        else:
            # Skip the function and use the cached value instead.
            value_json = result.decode('utf-8')
            value = json.loads(value_json)

        return value

    return wrapper


def print_table(rows):
    table = Texttable()
    table.set_cols_align(["r", "l", "r", "r", "r", "r", "r", "r", "r"])

    table.add_rows([
        ["Nr", "Name", "Pts.", "Min.", 'Pts./Min.', 'Fouls', 'FT', '2PT', '3PT'],
        *rows
    ])
    print(table.draw() + "\n")
