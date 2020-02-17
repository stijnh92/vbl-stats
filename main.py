import vbl.api
from vbl.models import Team, Player
from vbl.utils import print_table


def get_teams_with_players(game):
    def get_players(team, players):
        for _player in players:
            if not _player['RugNr'].isdigit():
                continue

            player = Player(_player['RelGUID'], _player['Naam'], _player['RugNr'])
            team.add_player(player)

    home = Team('home')
    away = Team('away')

    result = vbl_api.get_teams_from_game(game)
    get_players(home, result['TtDeel'])
    get_players(away, result['TuDeel'])

    return home, away


def substitute(player, substitution):
    minute = (substitution['Periode'] - 1) * 10 + substitution['Minuut']

    if substitution['Text'] == 'in' and minute != 1:
        # Player comes in
        player['last_in'] = minute
    else:
        # Player comes out, get the minutes he played.
        last_in = player['last_in']
        player['last_out'] = minute
        player['total_minutes'] += minute - last_in

    return player


def get_player_stats(game):
    result = vbl_api.get_game(game)

    events = result['GebNis']
    players = {}
    for event in events:
        player_id = event['RelGUID']
        player = players.get(player_id, {
            'last_in': -1,
            'last_out': 0,
            'total_minutes': 0,
            'score': 0,
            'fouls': 0,
            'ft': 0,
            '2p': 0,
            '3p': 0
        })

        if event['GebType'] == 50:
            player = substitute(player, event)
            players.update({
                player_id: player
            })

        if event['GebType'] == 30:
            player['fouls'] = player.get('fouls', 0) + 1

        if event['GebType'] != 10:
            continue

        points = int(event['Text'].split(' ')[0])
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


def print_results(team):
    rows = []
    for player in team.players:
        stats = get_score_for_player(player)
        rows.append([
            player.number,
            player.name,
            stats['score'],
            stats['total_minutes'],
            stats['ppm'],
            stats['fouls'],
            stats.get('ft', 0),
            stats.get('2p', 0),
            stats.get('3p', 0),
        ])

    # Add totals row
    rows.append([
        "",
        "Total",
        sum(x[2] for x in rows),
        sum(x[3] for x in rows),
        "",
        sum(x[5] for x in rows),
        sum(x[6] for x in rows),
        sum(x[7] for x in rows),
        sum(x[8] for x in rows),
    ])
    print_table(rows)


def get_score_for_player(player):
    if player_stats.get(player.id):
        stats = player_stats[player.id]
        if stats['total_minutes'] != 0:
            ppm = stats['score'] / stats['total_minutes']
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


if __name__ == '__main__':
    vbl_api = vbl.api.API()
    game_id = 'BVBL19209120LIHSE31AIG'
    home_team, away_team = get_teams_with_players(game_id)
    player_stats = get_player_stats(game_id)

    print_results(home_team)
    print_results(away_team)
