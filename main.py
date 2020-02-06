from vbl.api import API as VBLApi

def get_teams(game_id):
    result = vbl_api.get_teams_from_game(game_id)
    return result['TtDeel'], result['TuDeel']


def get_game_events(game_id):
    result = vbl_api.get_game(game_id)

    events = result['GebNis']
    players = {}
    for event in events:
        if event['GebType'] == 10:
            player_id = event['RelGUID']
            player = players.get(player_id)
            points = int(event['Text'][0])
            if not player:
                players.update({
                    player_id: {
                        'score': 0,
                        'team': event['TofU']
                    }
                })

            players[player_id].update({
                'score': players[player_id]['score'] + points
            })

    return players


def get_player(player_id, team):
    for member in team:
        if member['RelGUID'] == player_id:
            return member


def print_results(players, home_team, away_team):
    home_players = {}
    away_players = {}
    for player_id, stats in players.items():
        team = home_team if stats['team'] == 'T' else away_team
        player = get_player(player_id, team)

        if stats['team'] == 'T':
            home_players.update({"{0} [{1}]".format(player['Naam'], player['RugNr']) : stats['score']})
        else:
            away_players.update({"{0} [{1}]".format(player['Naam'], player['RugNr']) : stats['score']})

    print('HOME TEAM')
    print('=========')
    for player, score in sorted(home_players.items(), key=lambda x: x[1], reverse=True):
        print("{0:25} {1:2}".format(player, score))

    print('')
    print('AWAY TEAM')
    print('=========')
    for player, score in sorted(away_players.items(), key=lambda x: x[1], reverse=True):
        print("{0:25} {1:2}".format(player, score))


if __name__ == '__main__':
    vbl_api = VBLApi()
    game_id = 'BVBL19209120LIHSE31AGB'
    home_team, away_team = get_teams(game_id)
    players = get_game_events(game_id)

    # print(home_team)
    # print(away_team)
    # print(players)

    print_results(players, home_team, away_team)


# Event types:
# - 10: score
# - 20: time out
# - 30: fout
# - 40: nieuwe periode
# - 50: wissel
# - 60: einde match
