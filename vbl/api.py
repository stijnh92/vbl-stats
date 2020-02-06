import json
import redis
import requests

class API:
    BASE_URL = 'https://vblcb.wisseq.eu/VBLCB_WebService/data/'
    GAME_ENDPOINT = 'DwfVgngByWedGuid'
    TEAMS_ENDPOINT = 'DwfDeelByWedGuid'

    authorization_header: str
    crud_method: str
    wq_version: str
    base_url: str
    redis: redis.Redis

    def __init__(self):
        self.wq_version = 'ddc1.0'
        self.authorization_header = 'na'
        self.crud_method = 'R'
        self.redis = redis.Redis(host='localhost', port=6379, db=0)

    def get_headers(self):
        return {
            'Content-Type': "application/json",
            'Authorization': self.authorization_header
        }

    def get_base_payload(self):
        return {
            "AuthHeader": self.authorization_header,
            "WQVer": self.wq_version,
            "CRUD": self.crud_method
        }
    def cache_key(self, endpoint, data):
        # Compose cache key based on the endpoint and the data
        return endpoint + '_' + json.dumps(data)

    def put(self, endpoint, data):
        # First check the cache before executing the call.
        cache_key = self.cache_key(endpoint, data)
        result = self.check_cache(cache_key)
        if result:
            return result

        data.update(self.get_base_payload())
        response = requests.put(
            self.BASE_URL + endpoint,
            json=data,
            headers=self.get_headers()
        )
        result = response.json()

        self.store_cache(cache_key, json.dumps(result))
        return result

    def check_cache(self, key):
        value = self.redis.get(key)
        return json.loads(value) if value else value

    def store_cache(self, key, value):
        self.redis.set(key, value)

    def get_game(self, game_id: str):
        return self.put(self.GAME_ENDPOINT, {
            "WedGUID": game_id,
        })

    def get_teams_from_game(self, game_id: str):
        return self.put(self.TEAMS_ENDPOINT, {
            "WedGUID": game_id,
        })
