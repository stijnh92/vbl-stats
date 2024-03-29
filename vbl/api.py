from .utils import cached

import requests


class API:
    BASE_URL = 'https://vblcb.wisseq.eu/VBLCB_WebService/data/'
    GAME_INFO_ENDPOINT = 'MatchByWedGuid'
    GAME_ENDPOINT = 'DwfVgngByWedGuid'
    GAMES_FOR_TEAM_ENDPOINT = 'TeamMatchesByGuid'
    POULE_LIST_ENDPOINT = 'ListByRegio'
    TEAM_ENDPOINT = 'TeamDetailByGuid'
    TEAM_LIST_ENDPOINT = 'pouleByGuid'
    TEAMS_FROM_GAME_ENDPOINT = 'DwfDeelByWedGuid'

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

    @cached
    def get(self, endpoint, parameters):
        response = requests.get(
            self.BASE_URL + endpoint,
            parameters
        )
        print(self.BASE_URL + endpoint)
        return response.json()

    def get_team(self, team_id: str):
        return self.get(self.TEAM_ENDPOINT, {
            "teamGuid": team_id,
        })[0]

    def get_team_list_for_poule(self, poule_id: str):
        return self.get(self.TEAM_LIST_ENDPOINT, {
            "pouleguid": poule_id,
        })[0]['teams']

    def get_poule_list_for_region(self, region_id: str):
        return self.get(self.POULE_LIST_ENDPOINT, {
            "IssRegioguid": region_id,
        })

    def get_game(self, game_id: str):
        return self.put(self.GAME_ENDPOINT, {
            "WedGUID": game_id,
        })

    def get_game_info(self, game_id: str):
        return self.get(self.GAME_INFO_ENDPOINT, {
            "issguid": game_id,
        })[0]['doc']

    def get_teams_from_game(self, game_id: str):
        return self.put(self.TEAMS_FROM_GAME_ENDPOINT, {
            "WedGUID": game_id,
        })

    def get_games_for_team(self, team_id: str):
        return self.get(self.GAMES_FOR_TEAM_ENDPOINT, {
            "teamGuid": team_id,
        })
