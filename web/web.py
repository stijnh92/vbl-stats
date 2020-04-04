import datetime
import time
from pytz import timezone

from flask import Flask, render_template
from flask import request

from vbl import api, utils
from vbl.models import Team

app = Flask(__name__)


@app.route('/')
def index():
    # TODO: Scrape these values
    regions = {
        'BVBL9110': 'Antwerpen',
        'BVBL9120': 'Limburg',
        'BVBL9130': 'Oost-Vlaanderen',
        'BVBL9140': 'Vlaams-Brabant',
        'BVBL9150': 'West-Vlaanderen',
        'BVBL9100': 'Landelijk',
        'BVBL9170': 'Nationaal',
        'BVBL9170': 'Jeugd',
        'BVBL9160': 'R-Bab'
    }
    return render_template(
        'index.html',
        regions=regions
    )


@app.route('/region/<region_id>')
def region(region_id):
    vbl_api = api.API()
    poules = vbl_api.get_poules(region_id)
    return render_template(
        'region.html',
        poules=poules
    )


@app.route('/poule/<poule_id>')
def poule(poule_id):
    vbl_api = api.API()
    teams = vbl_api.get_teams(poule_id)
    return render_template(
        'poule.html',
        teams=teams
    )


@app.route('/team/<team_id>')
def team(team_id):
    vbl_api = api.API()
    team = vbl_api.get_team(team_id)

    all_games = vbl_api.get_games_for_team(team_id)

    played_games = []
    for game in all_games:
        if game['pouleGUID'] == 'BVBL19209120LIHSE31A' and game['uitslag'] != '':
            played_games.append(game)

    team = Team('BBC As', team_id)
    team_details = []
    player_stats = {}

    for game in played_games:
        game_id = game['guid']

        game_details = vbl_api.get_game_info(game_id)
        game_events = vbl_api.get_game(game_id)['GebNis']
        game_teams = vbl_api.get_teams_from_game(game_id)

        home_team, away_team = utils.get_teams_with_players(game_id, game_details, game_teams)

        # Check if the home team or the away team is our team to keep stats for
        if home_team.id == team.id:
            requested_team = home_team
            other_team = away_team
        else:
            requested_team = away_team
            other_team = home_team

        player_stats = utils.get_player_stats(player_stats, game_events)

        requested_team.ft_attempts = utils.get_free_throws_allowed(other_team, player_stats)

        team_details = utils.summarize_results(requested_team, player_stats)
        team.ft_attempts += requested_team.ft_attempts

    return render_template(
        'team.html',
        team=team,
        details=team_details
    )



@app.template_filter('timestamp_to_hours')
def timestamp_to_hours(s):
    date = datetime.datetime.fromtimestamp(s/1000.0)
    return date.astimezone(timezone('UTC')).strftime('%H:%M')


@app.route('/game/<game_id>')
def game(game_id):
    vbl_api = api.API()

    game_details = vbl_api.get_game_info(game_id)
    game_events = vbl_api.get_game(game_id)['GebNis']
    game_teams = vbl_api.get_teams_from_game(game_id)

    home_team, away_team = utils.get_teams_with_players(game_id, game_details, game_teams)
    player_stats = utils.get_player_stats({}, game_events)

    home_team.ft_attempts = utils.get_free_throws_allowed(away_team, player_stats)
    away_team.ft_attempts = utils.get_free_throws_allowed(home_team, player_stats)

    home_team_details = utils.summarize_results(home_team, player_stats)
    away_team_details = utils.summarize_results(away_team, player_stats)

    print(game_details)

    return render_template(
        'game.html',
        home_details=home_team_details,
        away_details=away_team_details,
        home_totals=home_team_details[-1],
        away_totals=away_team_details[-1],
        home_team=home_team,
        away_team=away_team,
        game_details=game_details
    )
