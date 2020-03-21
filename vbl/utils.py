from functools import wraps
import json

from redis import Redis
from texttable import Texttable

from vbl.models import Team, Player, GameEvent


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
    table.set_cols_align(["l", "r", "r", "r", "r", "r", "r", "r", "r"])

    table.add_rows([
        ["Player", "Pts.", "Min.", 'Pts./Min.', 'Fouls', 'FT', '2PT', '3PT', 'GP'],
        *rows
    ])
    print(table.draw())


def get_free_throws_allowed(team: Team, player_stats):
    sum = 0
    for player in team.players:
        if not player_stats.get(player.id):
            continue

        sum += player_stats[player.id].get('ft_allowed', 0)

    return sum


def summarize_results(team, player_stats):
    rows = []
    for player in team.players:
        stats = get_score_for_player(player, player_stats)
        rows.append([
            player,
            stats['score'],
            stats['total_minutes'],
            stats['ppm'],
            stats['fouls'],
            stats.get('ft', 0),
            stats.get('2p', 0),
            stats.get('3p', 0),
            stats.get('games_played', 0),
        ])

    ft_made = sum(x[5] for x in rows)
    # Add totals row
    rows.append([
        "Total",
        sum(x[1] for x in rows),
        sum(x[2] for x in rows),
        "",
        sum(x[4] for x in rows),
        ft_made,
        sum(x[6] for x in rows),
        sum(x[7] for x in rows),
        ""
    ])
    return rows


def print_results(team, rows):
    ft_made = rows[-1][5]

    print(team.name)
    print_table(rows)
    print('Free Throws: {0}/{1} = {2}%'.format(ft_made, team.ft_attempts, int((ft_made / team.ft_attempts) * 100)))
    print('')


def get_score_for_player(player, player_stats):
    if player_stats.get(player.id):
        stats = player_stats[player.id]
        if stats['total_minutes'] != 0:
            ppm = round(stats['score'] / stats['total_minutes'], 2)
        else:
            ppm = 0
        stats.update({
            'ppm': ppm
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
            '3p': 0
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

            player = Player(**_player)
            team.add_player(player)

    print(game_details)
    home = Team(game_details['teamThuisNaam'], game_details['teamThuisGUID'])
    away = Team(game_details['teamUitNaam'], game_details['teamUitGUID'])

    get_players(home, team_details['TtDeel'])
    get_players(away, team_details['TuDeel'])

    return home, away
