from flask import Flask, render_template
from flask import request

from vbl import api, utils

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/game/<game_id>')
def game(game_id):
    vbl_api = api.API()

    game_details = vbl_api.get_game_info(game_id)
    game_events = vbl_api.get_game(game_id)['GebNis']
    game_teams = vbl_api.get_teams_from_game(game_id)

    home_team, away_team = utils.get_teams_with_players(game_id, game_details, game_teams)
    player_stats = utils.get_player_stats(game_events)

    home_team.ft_attempts = utils.get_free_throws_allowed(away_team, player_stats)
    away_team.ft_attempts = utils.get_free_throws_allowed(home_team, player_stats)

    home_team_details = utils.summarize_results(home_team, player_stats)
    away_team_details = utils.summarize_results(away_team, player_stats)

    return render_template('game.html', home=home_team_details, away=away_team_details)
