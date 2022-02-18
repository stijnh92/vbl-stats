import datetime
from collections import defaultdict

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
    poules = vbl_api.get_poule_list_for_region(region_id)

    # Sort the poules by the "sort" property.
    poules = sorted(poules, key=lambda i: i['sort'])

    # Group the poules by the "categorie" property.
    categories = defaultdict(list)
    for poule in poules:
        categories[poule['categorie']].append(poule)

    return render_template(
        'region.html',
        categories=categories
    )


@app.route('/poule/<poule_id>')
def poule(poule_id):
    vbl_api = api.API()
    teams = vbl_api.get_team_list_for_poule(poule_id)
    players = []

    for _team in teams:
        team, team_totals = get_team_details(_team['guid'], poule_id)
        players += [player for player in team.players]

    table_only = request.args.get('tableOnly', False)
    format = request.args.get('format', 'average')

    template = 'poule.html' if not table_only else 'team_table.html'
    show_average = format == 'average'

    return render_template(
        template,
        id=poule_id,
        teams=teams,
        players=players,
        show_average=show_average
    )


@app.route('/team/<team_id>/<poule_id>')
def team(team_id, poule_id):
    team, team_totals = get_team_details(team_id, poule_id)
    table_only = request.args.get('tableOnly', False)
    format = request.args.get('format', 'average')

    template = 'team.html' if not table_only else 'team_table.html'
    show_average = format == 'average'

    # TODO: Show games for team in this poule
    # TODO: Add detail view for a game

    return render_template(
        template,
        team=team,
        players=team.players,
        totals=team_totals,
        show_average=show_average
    )


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
    date = datetime.datetime.fromtimestamp(s / 1000.0)
    return date.astimezone(timezone('UTC')).strftime('%H:%M')


def get_team_details(team_id, poule_id):
    vbl_api = api.API()
    team_details = vbl_api.get_team(team_id)
    team = Team(team_details['naam'], team_details['guid'])

    all_games = vbl_api.get_games_for_team(team_id)

    print(team_id)

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

        # Check if we can mark this game as played for a player.
        for playerId, value in player_stats.items():
            # Check if the gamer has played at least one minute in this game.
            if value['game_minutes'] > 0:
                player_stats[playerId].update({
                    'games_played': player_stats[playerId]['games_played'] + 1
                })

        team.ft_attempts += utils.get_free_throws_allowed(other_team, player_stats)

        team_details = utils.summarize_results(team, player_stats)

    return team, team_details
