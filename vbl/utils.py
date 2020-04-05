from functools import wraps
import json

from redis import Redis

from vbl.models.event import GameEvent
from vbl.models.player import Player
from vbl.models.team import Team


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


def get_free_throws_allowed(team: Team, player_stats):
    free_throws_allowed = 0
    for player in team.players:
        if not player_stats.get(player.id):
            continue

        free_throws_allowed += player_stats[player.id].get('ft_allowed', 0)

    return free_throws_allowed


def summarize_results(team, player_stats):
    for player in team.players:
        player.stats = get_score_for_player(player, player_stats)
    totals = {
        'score': sum(player.stats['score'] for player in team.players),
        'total_minutes': sum(player.stats['total_minutes'] for player in team.players),
        'fouls': sum(player.stats['fouls'] for player in team.players),
        'ft': sum(player.stats.get('ft', 0) for player in team.players),
        '2p': sum(player.stats.get('2p', 0) for player in team.players),
        '3p': sum(player.stats.get('3p', 0) for player in team.players)
    }
    return totals


def get_score_for_player(player, player_stats):
    if player_stats.get(player.id):
        stats = player_stats[player.id]
        if stats['total_minutes'] != 0:
            ppm = round(stats['score'] / stats['total_minutes'], 2)
        else:
            ppm = 0

        if stats['games_played'] == 0:
            stats['games_played'] = 1

        stats.update({
            'ppm': ppm,
            'score_avg': round(stats['score'] / stats['games_played'], 2),
            'total_minutes_avg': round(stats['total_minutes'] / stats['games_played'], 2),
            'fouls_avg': round(stats['fouls'] / stats['games_played'], 2),
            'ft_avg': round(stats['ft'] / stats['games_played'], 2),
            '2p_avg': round(stats['2p'] / stats['games_played'], 2),
            '3p_avg': round(stats['3p'] / stats['games_played'], 2)
        })
        return stats

    return {
        'score': 0,
        'total_minutes': 0,
        'ppm': 0,
        'fouls': 0
    }


def get_player_stats(players, events):
    for _event in events:
        event = GameEvent(**_event)

        player_id = event.id
        player = players.get(player_id, {
            'last_in': 0,
            'last_out': 0,
            'total_minutes': 0,
            'score': 0,
            'fouls': 0,
            'ft_allowed': 0,
            'ft': 0,
            '2p': 0,
            '3p': 0,
            'games_played': 0
        })

        if event.is_substitution():
            player = substitute(player, event)
            players.update({
                player_id: player
            })

        elif event.is_foul():
            player['fouls'] = player.get('fouls', 0) + 1
            penalty = 0
            if event.content in ('P1', 'T1'):
                penalty = 1
            if event.content == 'P2':
                penalty = 2
            if event.content == 'P3':
                penalty = 3
            player['ft_allowed'] = player.get('ft_allowed', 0) + penalty

        elif event.is_score():
            points = int(event.content.split(' ')[0])
            player['score'] += points
            if points == 1:
                player['ft'] += 1
            elif points == -1:
                player['ft'] -= 1

            elif points == 2:
                player['2p'] += 1
            elif points == -2:
                player['2p'] -= 1

            elif points == 3:
                player['3p'] += 1
            elif points == -3:
                player['3p'] -= 1

        players.update({
            player_id: player
        })

    # When all events are finished, check if some players are not marked as 'out'
    # This happens when the last_in is greater than the last_out
    for player_id, stats in players.items():
        if stats['last_in'] > stats['last_out'] and stats['last_out'] != 40:
            minutes = 40 - stats['last_in']
            stats['last_out'] = 40
            stats['total_minutes'] += minutes

    return players


def substitute(player, substitution: GameEvent):
    minute = (substitution.period - 1) * 10 + substitution.minute

    if substitution.content == 'in':
        if substitution.minute == 1: # When a player comes in in the first minute of a quarter, set minutes to 0
            minute = (substitution.period - 1) * 10

        # Player comes in
        player['last_in'] = minute
    else:
        # Player comes out, get the minutes he played.
        last_in = player['last_in']
        player['last_out'] = minute
        player['total_minutes'] += minute - last_in

    return player


def get_teams_with_players(game, game_details, team_details):
    def get_players(team, players):
        for _player in players:
            if not _player['RugNr'].isdigit():
                continue

            player = Player(team, **_player)
            team.add_player(player)

    home = Team(game_details['teamThuisNaam'], game_details['teamThuisGUID'])
    away = Team(game_details['teamUitNaam'], game_details['teamUitGUID'])

    get_players(home, team_details['TtDeel'])
    get_players(away, team_details['TuDeel'])

    return home, away
