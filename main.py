from vbl import api, utils


if __name__ == '__main__':
    vbl_api = api.API()

    game_id = 'BVBL19209120LIHSE31AEG'
    game_details = vbl_api.get_game_info(game_id)
    game_events = vbl_api.get_game(game_id)['GebNis']
    game_teams = vbl_api.get_teams_from_game(game_id)

    home_team, away_team = utils.get_teams_with_players(game_id, game_details, game_teams)
    player_stats = utils.get_player_stats(game_events)

    home_team.ft_attempts = utils.get_free_throws_allowed(away_team, player_stats)
    away_team.ft_attempts = utils.get_free_throws_allowed(home_team, player_stats)

    home_team_details = utils.summarize_results(home_team, player_stats)
    away_team_details = utils.summarize_results(away_team, player_stats)

    utils.print_results(home_team, home_team_details)
    utils.print_results(away_team, away_team_details)
