import datetime

from pytz import timezone
from flask import Flask, render_template
from flask import request

from vbl import api, utils
from vbl.models.team import Team

app = Flask(__name__)


@app.route('/')
def index():
    # TODO: Scrape these values from the VBL site.
    # https://www.basketbal.vlaanderen/competitie/resultaten-en-kalender
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
    poules = vbl_api.get_poule_list(region_id)
    return render_template(
        'region.html',
        poules=poules
    )


@app.route('/poule/<poule_id>')
def poule(poule_id):
    vbl_api = api.API()
    teams = vbl_api.get_team_list(poule_id)
    players = []

    for _team in teams:
        team, team_totals = get_team_details(_team['guid'], poule_id)
        players += [player for player in team.players]

    table_only = request.args.get('tableOnly', False)
    format = request.args.get('format', 'average')
    template = 'poule.html' if not table_only else 'team_table.html'

    return render_template(
        template,
        teams=teams,
        id=poule_id,
        players=players,
        show_average=format == 'average'
    )


@app.route('/team/<team_id>/<poule_id>')
def team(team_id, poule_id):
    team, team_totals = get_team_details(team_id, poule_id)
    table_only = request.args.get('tableOnly', False)
    format = request.args.get('format', 'average')

    template = 'team.html' if not table_only else 'team_table.html'
    return render_template(
        template,
        players=team.players,
        totals=team_totals,
        show_average=format == 'average'
    )


def get_team_details(team_id, poule_id):
    vbl_api = api.API()
    team_details = vbl_api.get_team(team_id)
    team = Team(team_details['naam'], team_details['guid'])

    all_games = vbl_api.get_games_for_team(team_id)

    played_games = []
    for game in all_games:
        if game['pouleGUID'] == poule_id and game['uitslag'] != '':
            played_games.append(game)

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

        # add all players to the requested team
        for player in requested_team.players:
            if player.id not in [player.id for player in team.players]:
                team.add_player(player)

        player_stats = utils.get_player_stats(player_stats, game_events)

        # Get the amount of games played per player
        for playerId, value in player_stats.items():
            # If the player id is found in the team details of this game, add one extra
            played = False
            if playerId in [player['RelGUID'] for player in game_teams['TtDeel']]:
                played = True
            if playerId in [player['RelGUID'] for player in game_teams['TuDeel']]:
                played = True

            if played:
                player_stats[playerId].update({
                    'games_played': player_stats[playerId]['games_played'] + 1
                })

        team.ft_attempts = utils.get_free_throws_allowed(other_team, player_stats)

        team_details = utils.summarize_results(team, player_stats)
        team.ft_attempts += team.ft_attempts

    return team, team_details


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

    utils.summarize_results(home_team, player_stats)
    utils.summarize_results(away_team, player_stats)

    return render_template(
        'game.html',
        home_team=home_team,
        away_team=away_team,
        game_details=game_details
    )


@app.template_filter('timestamp_to_hours')
def timestamp_to_hours(s):
    date = datetime.datetime.fromtimestamp(s/1000.0)
    return date.astimezone(timezone('UTC')).strftime('%H:%M')
