"""
Парсер для автоматического сбора xG данных
Работает с understat.com и альтернативными источниками
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import time
from datetime import datetime
import pandas as pd


class UnderstatParser:
    def __init__(self):
        self.base_url = "https://understat.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.leagues = {
            'EPL': 'epl',
            'La_Liga': 'la_liga', 
            'Bundesliga': 'bundesliga',
            'Serie_A': 'serie_a',
            'Ligue_1': 'ligue_1',
            'RFPL': 'rfpl'
        }
    
    def get_league_teams(self, league='EPL', season='2024'):
        """Получить список команд лиги"""
        try:
            league_url = self.leagues.get(league, 'epl')
            url = f"{self.base_url}/league/{league_url}/{season}"

            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Ищем данные команд в скриптах
            scripts = soup.find_all('script')
            for script in scripts:
                if 'var teamsData' in script.text:
                    json_match = re.search(r'var teamsData\s*=\s*JSON\.parse\(\'(.+?)\'\)', script.text)
                    if json_match:
                        teams_data = json.loads(json_match.group(1).encode().decode('unicode_escape'))
                        return teams_data

            return None
        except requests.Timeout:
            print(f"⏱️  Таймаут при получении данных лиги {league}")
            return None
        except requests.RequestException as e:
            print(f"❌ Ошибка сети при получении команд: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ Ошибка парсинга JSON: {e}")
            return None
        except Exception as e:
            print(f"❌ Неожиданная ошибка получения команд: {e}")
            return None
    
    def get_team_matches(self, team_id, season='2024'):
        """Получить матчи команды за сезон"""
        try:
            url = f"{self.base_url}/team/{team_id}/{season}"
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            scripts = soup.find_all('script')
            for script in scripts:
                if 'var matchesData' in script.text:
                    json_match = re.search(r'var matchesData\s*=\s*JSON\.parse\(\'(.+?)\'\)', script.text)
                    if json_match:
                        matches_data = json.loads(json_match.group(1).encode().decode('unicode_escape'))
                        return matches_data

            return None
        except requests.Timeout:
            print(f"⏱️  Таймаут при получении матчей команды {team_id}")
            return None
        except requests.RequestException as e:
            print(f"❌ Ошибка сети при получении матчей: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ Ошибка парсинга JSON матчей: {e}")
            return None
        except Exception as e:
            print(f"❌ Неожиданная ошибка получения матчей команды {team_id}: {e}")
            return None
    
    def parse_team_stats(self, team_name, league='EPL', last_n_games=10):
        """
        Парсинг статистики команды для модели
        Возвращает средние xG за последние N матчей
        """
        try:
            # Получаем команды лиги
            teams_data = self.get_league_teams(league)
            if not teams_data:
                return None
            
            # Ищем нужную команду
            team_id = None
            for team in teams_data:
                if team['title'].lower() == team_name.lower():
                    team_id = team['id']
                    break
            
            if not team_id:
                print(f"Команда {team_name} не найдена")
                return None
            
            # Получаем матчи
            matches = self.get_team_matches(team_id)
            if not matches:
                return None
            
            # Фильтруем последние N матчей
            recent_matches = sorted(matches, key=lambda x: x['datetime'], reverse=True)[:last_n_games]
            
            home_matches = [m for m in recent_matches if m['side'] == 'h']
            away_matches = [m for m in recent_matches if m['side'] == 'a']
            
            stats = {
                'team_name': team_name,
                'total_matches': len(recent_matches),
                'home_xg': sum([float(m['xG']) for m in home_matches]) / len(home_matches) if home_matches else 0,
                'away_xg': sum([float(m['xG']) for m in away_matches]) / len(away_matches) if away_matches else 0,
                'home_xga': sum([float(m['xGA']) for m in home_matches]) / len(home_matches) if home_matches else 0,
                'away_xga': sum([float(m['xGA']) for m in away_matches]) / len(away_matches) if away_matches else 0,
                'overall_xg': sum([float(m['xG']) for m in recent_matches]) / len(recent_matches),
                'overall_xga': sum([float(m['xGA']) for m in recent_matches]) / len(recent_matches),
            }
            
            return stats
        
        except Exception as e:
            print(f"Ошибка парсинга статистики {team_name}: {e}")
            return None


class FootyStatsParser:
    """
    Альтернативный парсер для footystats.org
    Можно использовать если understat недоступен
    """
    def __init__(self):
        self.base_url = "https://footystats.org"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def get_team_stats(self, team_name, league='premier-league'):
        """
        Получить статистику команды с footystats
        """
        try:
            # Форматируем название для URL
            team_url = team_name.lower().replace(' ', '-')
            url = f"{self.base_url}/{league}/{team_url}"
            
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Здесь нужно адаптировать под реальную структуру сайта
            # Это примерная схема
            stats = {}
            
            # Ищем таблицы со статистикой
            stat_tables = soup.find_all('table', class_='stat-table')
            
            return stats
        except Exception as e:
            print(f"Ошибка footystats: {e}")
            return None


class DataCache:
    """Кэширование данных чтобы не долбить сайты"""
    def __init__(self, cache_file='team_cache.json'):
        self.cache_file = cache_file
        self.cache = self.load_cache()
    
    def load_cache(self):
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    
    def save_cache(self):
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)
    
    def get(self, key):
        if key in self.cache:
            # Проверяем свежесть (24 часа)
            cached_time = datetime.fromisoformat(self.cache[key]['timestamp'])
            if (datetime.now() - cached_time).total_seconds() < 86400:
                return self.cache[key]['data']
        return None
    
    def set(self, key, data):
        self.cache[key] = {
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        self.save_cache()


def collect_match_data(home_team, away_team, league='EPL'):
    """
    Собрать данные для конкретного матча
    """
    parser = UnderstatParser()
    cache = DataCache()
    
    print(f"Сбор данных для матча: {home_team} vs {away_team}")
    
    # Проверяем кэш
    home_key = f"{league}_{home_team}_10"
    away_key = f"{league}_{away_team}_10"
    
    home_stats = cache.get(home_key)
    if not home_stats:
        print(f"Парсинг {home_team}...")
        home_stats = parser.parse_team_stats(home_team, league, last_n_games=10)
        if home_stats:
            cache.set(home_key, home_stats)
        time.sleep(2)  # Пауза между запросами
    else:
        print(f"{home_team} - данные из кэша")
    
    away_stats = cache.get(away_key)
    if not away_stats:
        print(f"Парсинг {away_team}...")
        away_stats = parser.parse_team_stats(away_team, league, last_n_games=10)
        if away_stats:
            cache.set(away_key, away_stats)
        time.sleep(2)
    else:
        print(f"{away_team} - данные из кэша")
    
    if not home_stats or not away_stats:
        print("Не удалось получить данные")
        return None
    
    return {
        'home': home_stats,
        'away': away_stats,
        'home_xg_expected': home_stats['home_xg'],  # xG дома
        'away_xg_expected': away_stats['away_xg'],  # xG в гостях
    }


def create_dataframe_from_stats(stats):
    """Создать DataFrame для анализа"""
    if not stats:
        return None
    
    df = pd.DataFrame({
        'Команда': [stats['home']['team_name'], stats['away']['team_name']],
        'Место': ['Дома', 'В гостях'],
        'xG': [stats['home']['home_xg'], stats['away']['away_xg']],
        'xGA': [stats['home']['home_xga'], stats['away']['away_xga']],
        'Общий xG': [stats['home']['overall_xg'], stats['away']['overall_xg']],
        'Матчей': [stats['home']['total_matches'], stats['away']['total_matches']]
    })
    
    return df


if __name__ == "__main__":
    # Пример использования
    print("="*60)
    print("СБОР ДАННЫХ ДЛЯ ПРОГНОЗА")
    print("="*60 + "\n")
    
    # Реальный пример (нужно заменить на актуальные команды)
    match_data = collect_match_data(
        home_team="Manchester City",
        away_team="Liverpool", 
        league='EPL'
    )
    
    if match_data:
        print("\n" + "="*60)
        print("СОБРАННЫЕ ДАННЫЕ")
        print("="*60 + "\n")
        
        df = create_dataframe_from_stats(match_data)
        print(df.to_string(index=False))
        
        print(f"\n\nДанные для модели:")
        print(f"home_xg = {match_data['home_xg_expected']:.2f}")
        print(f"away_xg = {match_data['away_xg_expected']:.2f}")
        print(f"\nЭти значения используй в football_betting_model.py")
    else:
        print("\nНе удалось собрать данные. Используй ручной ввод.")
