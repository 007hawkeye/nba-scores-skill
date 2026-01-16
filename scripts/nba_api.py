import requests
from datetime import datetime, timedelta
from dateutil import parser as date_parser

class NBAApi:
    BASE_URL = "https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json"
    
    def __init__(self):
        self.games = []
        self.last_updated = None
    
    def fetch_games(self):
        try:
            response = requests.get(self.BASE_URL, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            self.games = []
            scoreboard = data.get('scoreboard', {})
            games = scoreboard.get('games', [])
            
            for game in games:
                game_info = self._parse_game(game)
                if game_info:
                    self.games.append(game_info)
            
            self.last_updated = datetime.now()
            return True, self.games
            
        except requests.RequestException as e:
            return False, f"获取NBA数据失败: {str(e)}"
        except Exception as e:
            return False, f"解析NBA数据失败: {str(e)}"
    
    def _parse_game(self, game):
        try:
            home_team = game.get('homeTeam', {})
            away_team = game.get('awayTeam', {})
            game_status = game.get('gameStatus', 0)
            game_status_text = game.get('gameStatusText', '')
            game_time = game.get('gameTimeUTC', '')
            
            game_info = {
                'game_id': game.get('gameId', ''),
                'game_code': game.get('gameCode', ''),
                'game_status': game_status,
                'game_status_text': game_status_text,
                'game_time': game_time,
                'is_live': game_status == 2,
                'is_finished': game_status == 3,
                'home_team': {
                    'team_id': home_team.get('teamId', ''),
                    'team_name': home_team.get('teamName', ''),
                    'team_city': home_team.get('teamCity', ''),
                    'team_tricode': home_team.get('teamTricode', ''),
                    'score': home_team.get('score', 0),
                    'wins': home_team.get('wins', 0),
                    'losses': home_team.get('losses', 0)
                },
                'away_team': {
                    'team_id': away_team.get('teamId', ''),
                    'team_name': away_team.get('teamName', ''),
                    'team_city': away_team.get('teamCity', ''),
                    'team_tricode': away_team.get('teamTricode', ''),
                    'score': away_team.get('score', 0),
                    'wins': away_team.get('wins', 0),
                    'losses': away_team.get('losses', 0)
                }
            }
            
            return game_info
            
        except Exception as e:
            print(f"解析比赛数据失败: {e}")
            return None
    
    def get_games_by_status(self, status='all'):
        if status == 'live':
            return [game for game in self.games if game['is_live']]
        elif status == 'finished':
            return [game for game in self.games if game['is_finished']]
        else:
            return self.games
    
    def get_total_games(self):
        return len(self.games)
    
    def get_live_games_count(self):
        return len([game for game in self.games if game['is_live']])
    
    def get_finished_games_count(self):
        return len([game for game in self.games if game['is_finished']])
