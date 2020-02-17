from vbl.api import API as VBLApi
from vbl.models import Team, Player

from texttable import Texttable

def get_teams_with_players(game_id):
    def get_players(team, players):
        for _player in players:
            if not _player['RugNr'].isdigit():
                continue

            player = Player(_player['RelGUID'], _player['Naam'], _player['RugNr'])
            team.add_player(player)


    home_team = Team('home')
    away_team = Team('away')

    result = vbl_api.get_teams_from_game(game_id)
    get_players(home_team, result['TtDeel'])
    get_players(away_team, result['TuDeel'])

    return home_team, away_team


def substitute(player, substitution):
    minute = (substitution['Periode'] -1) * 10 + substitution['Minuut']

    if substitution['Text'] == 'in' and minute != 1:
        # Player comes in
        player['last_in'] = minute
    else:
        # Player comes out, get the minutes he played.
        last_in = player['last_in']
        player['last_out'] = minute
        player['total_minutes'] += minute - last_in

    return player

def get_player_stats(game_id):
    result = vbl_api.get_game(game_id)

    events = result['GebNis']
    players = {}
    for event in events:
        player_id = event['RelGUID']
        player = players.get(player_id, {
            'last_in': -1,
            'last_out': 0,
            'total_minutes': 0,
            'score': 0,
            'fouls': 0
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

        points = int(event['Text'][0])
        player['score'] += points

        players.update({
            player_id: player
        })


    # When all events are finished, check if some players are not marked as 'out'
    # This happens when the last_in is greater than the last_out
    for player_id, stats in players.items():
        if (stats['last_in'] > stats['last_out'] and stats['last_out'] != 40):
            minutes = 40 - stats['last_in']
            stats['last_out'] = 40
            stats['total_minutes'] += minutes

    return players


def print_results(players, home_team, away_team):
    teams = [home_team, away_team]
    for team in teams:
        rows = []
        for player in team.players:
            stats = get_score_for_player(player)
            rows.append([
                player.number,
                player.name,
                stats['score'],
                stats['total_minutes'],
                stats['ppm'],
                stats['fouls']
            ])

        table = Texttable()
        table.set_cols_align(["r", "l", "r", "r", "r", "r"])

        # calculate totals

        total_points = sum(x[2] for x in rows)
        total_minutes = sum(x[3] for x in rows)
        total_fouls = sum(x[5] for x in rows)
        rows.append([
            "",
            "Totaal",
            total_points,
            total_minutes,
            "",
            total_fouls
        ])

        table.add_rows([
            ["Nr", "Name", "Pts.", "Min.", 'Pts./Min.', 'Fouls'],
            *rows
        ])
        print(table.draw() + "\n")


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
    vbl_api = VBLApi()
    game_id = 'BVBL19209120LIHSE31AME'
    home_team, away_team = get_teams_with_players(game_id)
    player_stats = get_player_stats(game_id)

    print_results(player_stats, home_team, away_team)
