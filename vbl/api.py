from .utils import cached

import requests


class API:
    BASE_URL = 'https://vblcb.wisseq.eu/VBLCB_WebService/data/'
    GAME_ENDPOINT = 'DwfVgngByWedGuid'
    TEAMS_ENDPOINT = 'DwfDeelByWedGuid'

    authorization_header: str
    crud_method: str
    wq_version: str
    base_url: str

    def __init__(self):
        self.wq_version = 'ddc1.0'
        self.authorization_header = 'na'
        self.crud_method = 'R'

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

    @cached
    def put(self, endpoint, data):
        data.update(self.get_base_payload())
        response = requests.put(
            self.BASE_URL + endpoint,
            json=data,
            headers=self.get_headers()
        )
        return response.json()

    def get_game(self, game_id: str):
        return self.put(self.GAME_ENDPOINT, {
            "WedGUID": game_id,
        })

    def get_teams_from_game(self, game_id: str):
        return self.put(self.TEAMS_ENDPOINT, {
            "WedGUID": game_id,
        })
