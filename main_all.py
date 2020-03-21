from vbl import api, utils
from vbl.models import Team

if __name__ == '__main__':
    vbl_api = api.API()

    team_id = 'BVBL1379HSE  1'
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

    print(team_details)
    utils.print_results(team, team_details)
