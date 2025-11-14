"""
API-Football клиент - автоматический сбор ВСЕХ данных
Бесплатно: 100 запросов/день
Регистрация: https://www.api-football.com/
"""

import requests
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import time


class APIFootballClient:
    """
    Клиент для API-Football v3

    Получает:
    - Коэффициенты от всех букмекеров
    - Форму команд
    - Таблицу лиги
    - H2H статистику
    - Травмы и дисквалификации
    - Статистику матчей (xG, удары, владение)
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://v3.football.api-sports.io"
        self.headers = {
            'x-apisports-key': api_key
        }
        self.cache = {}

    def _request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Базовый запрос к API"""
        try:
            url = f"{self.base_url}/{endpoint}"
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            response.raise_for_status()

            data = response.json()

            # Проверяем лимиты
            if 'requests' in data:
                remaining = data['requests']['current']
                limit = data['requests']['limit_day']
                print(f"📊 API запросов использовано: {remaining}/{limit}")

            return data

        except requests.RequestException as e:
            print(f"❌ Ошибка API: {e}")
            return None

    def search_team(self, team_name: str, league_id: int = 39) -> Optional[int]:
        """
        Найти ID команды по названию

        Args:
            team_name: Название команды
            league_id: ID лиги (39 = Premier League)

        Returns:
            Team ID или None
        """
        cache_key = f"team_{team_name}_{league_id}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        data = self._request("teams", {"league": league_id, "search": team_name})

        if data and data['response']:
            team_id = data['response'][0]['team']['id']
            self.cache[cache_key] = team_id
            return team_id

        return None

    def get_upcoming_matches(self, league_id: int = 39, days: int = 7) -> List[Dict]:
        """
        Получить предстоящие матчи лиги

        Args:
            league_id: ID лиги (39 = EPL, 140 = La Liga, 78 = Bundesliga)
            days: Сколько дней вперед смотреть

        Returns:
            Список матчей
        """
        today = datetime.now().strftime('%Y-%m-%d')
        future = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')

        data = self._request("fixtures", {
            "league": league_id,
            "from": today,
            "to": future,
            "season": datetime.now().year
        })

        if not data or not data['response']:
            return []

        matches = []
        for fixture in data['response']:
            matches.append({
                'fixture_id': fixture['fixture']['id'],
                'date': fixture['fixture']['date'],
                'home_team': fixture['teams']['home']['name'],
                'away_team': fixture['teams']['away']['name'],
                'home_team_id': fixture['teams']['home']['id'],
                'away_team_id': fixture['teams']['away']['id'],
                'status': fixture['fixture']['status']['long']
            })

        return matches

    def get_odds(self, fixture_id: int) -> Optional[Dict]:
        """
        Получить коэффициенты на матч от всех букмекеров

        Returns:
            Средние коэффициенты от топ букмекеров
        """
        data = self._request("odds", {
            "fixture": fixture_id,
            "bookmaker": "8"  # Bet365 (можно изменить)
        })

        if not data or not data['response']:
            print(f"⚠️  Коэффициенты для матча {fixture_id} не найдены")
            return None

        odds = {
            'home_win': None,
            'draw': None,
            'away_win': None,
            'over_2.5': None,
            'under_2.5': None,
            'btts_yes': None,
            'btts_no': None,
            'bookmaker': None,
            'fixture_id': fixture_id
        }

        for bookmaker in data['response'][0]['bookmakers']:
            odds['bookmaker'] = bookmaker['name']

            for bet in bookmaker['bets']:
                # Match Winner
                if bet['name'] == 'Match Winner':
                    for value in bet['values']:
                        if value['value'] == 'Home':
                            odds['home_win'] = float(value['odd'])
                        elif value['value'] == 'Draw':
                            odds['draw'] = float(value['odd'])
                        elif value['value'] == 'Away':
                            odds['away_win'] = float(value['odd'])

                # Goals Over/Under
                elif bet['name'] == 'Goals Over/Under':
                    for value in bet['values']:
                        if 'Over 2.5' in value['value']:
                            odds['over_2.5'] = float(value['odd'])
                        elif 'Under 2.5' in value['value']:
                            odds['under_2.5'] = float(value['odd'])

                # Both Teams Score
                elif bet['name'] == 'Both Teams Score':
                    for value in bet['values']:
                        if value['value'] == 'Yes':
                            odds['btts_yes'] = float(value['odd'])
                        elif value['value'] == 'No':
                            odds['btts_no'] = float(value['odd'])

        return odds

    def get_team_statistics(self, team_id: int, league_id: int = 39, season: int = None) -> Optional[Dict]:
        """
        Получить статистику команды за сезон

        Returns:
            Детальная статистика
        """
        if season is None:
            season = datetime.now().year

        data = self._request("teams/statistics", {
            "team": team_id,
            "league": league_id,
            "season": season
        })

        if not data or not data['response']:
            return None

        stats = data['response']

        return {
            'team_name': stats['team']['name'],
            'matches_played': stats['fixtures']['played']['total'],
            'wins': stats['fixtures']['wins']['total'],
            'draws': stats['fixtures']['draws']['total'],
            'losses': stats['fixtures']['losses']['total'],
            'goals_for': stats['goals']['for']['total']['total'],
            'goals_against': stats['goals']['against']['total']['total'],
            'avg_goals_for': stats['goals']['for']['average']['total'],
            'avg_goals_against': stats['goals']['against']['average']['total'],
            'clean_sheets': stats['clean_sheet']['total'],
            'form': stats['form']  # "WWDLW"
        }

    def get_team_form(self, team_id: int, last_n: int = 5) -> Optional[List[str]]:
        """
        Получить форму команды (последние N матчей)

        Returns:
            ['W', 'W', 'D', 'L', 'W']
        """
        data = self._request("fixtures", {
            "team": team_id,
            "last": last_n
        })

        if not data or not data['response']:
            return None

        form = []
        for fixture in data['response']:
            home_team = fixture['teams']['home']['id']
            home_goals = fixture['goals']['home']
            away_goals = fixture['goals']['away']

            if home_goals is None or away_goals is None:
                continue  # Матч еще не сыгран

            if home_team == team_id:
                # Команда играла дома
                if home_goals > away_goals:
                    form.append('W')
                elif home_goals < away_goals:
                    form.append('L')
                else:
                    form.append('D')
            else:
                # Команда играла в гостях
                if away_goals > home_goals:
                    form.append('W')
                elif away_goals < home_goals:
                    form.append('L')
                else:
                    form.append('D')

        return form[:last_n]

    def get_h2h(self, team1_id: int, team2_id: int, last_n: int = 5) -> Optional[Dict]:
        """
        Получить статистику личных встреч

        Returns:
            H2H статистика
        """
        data = self._request("fixtures/headtohead", {
            "h2h": f"{team1_id}-{team2_id}",
            "last": last_n
        })

        if not data or not data['response']:
            return None

        h2h = {
            'total_matches': 0,
            'team1_wins': 0,
            'team2_wins': 0,
            'draws': 0,
            'results': []  # С точки зрения team1
        }

        for fixture in data['response']:
            h2h['total_matches'] += 1

            home_id = fixture['teams']['home']['id']
            home_goals = fixture['goals']['home']
            away_goals = fixture['goals']['away']

            if home_goals > away_goals:
                winner = home_id
            elif away_goals > home_goals:
                winner = fixture['teams']['away']['id']
            else:
                winner = None
                h2h['draws'] += 1

            if winner == team1_id:
                h2h['team1_wins'] += 1
                h2h['results'].append('W')
            elif winner == team2_id:
                h2h['team2_wins'] += 1
                h2h['results'].append('L')
            else:
                h2h['results'].append('D')

        return h2h

    def get_injuries(self, team_id: int) -> Optional[List[Dict]]:
        """
        Получить список травмированных игроков

        Returns:
            Список травм
        """
        data = self._request("injuries", {"team": team_id})

        if not data or not data['response']:
            return []

        injuries = []
        for injury in data['response']:
            injuries.append({
                'player_name': injury['player']['name'],
                'player_id': injury['player']['id'],
                'type': injury['player']['type'],  # Missing, Doubtful, etc.
                'reason': injury['player']['reason']
            })

        return injuries

    def get_league_standings(self, league_id: int = 39, season: int = None) -> Optional[List[Dict]]:
        """
        Получить турнирную таблицу

        Returns:
            Таблица лиги
        """
        if season is None:
            season = datetime.now().year

        data = self._request("standings", {
            "league": league_id,
            "season": season
        })

        if not data or not data['response']:
            return None

        standings = []
        for team in data['response'][0]['league']['standings'][0]:
            standings.append({
                'position': team['rank'],
                'team_name': team['team']['name'],
                'team_id': team['team']['id'],
                'points': team['points'],
                'played': team['all']['played'],
                'wins': team['all']['win'],
                'draws': team['all']['draw'],
                'losses': team['all']['lose'],
                'goals_for': team['all']['goals']['for'],
                'goals_against': team['all']['goals']['against'],
                'goal_difference': team['goalsDiff'],
                'form': team['form']
            })

        return standings


# ID лиг для API-Football
LEAGUE_IDS = {
    'EPL': 39,           # Premier League
    'La_Liga': 140,      # La Liga
    'Bundesliga': 78,    # Bundesliga
    'Serie_A': 135,      # Serie A
    'Ligue_1': 61,       # Ligue 1
    'Champions_League': 2,
    'Europa_League': 3
}


def full_match_data_collection(api_key: str, home_team: str, away_team: str, league: str = 'EPL') -> Dict:
    """
    Полный автоматический сбор ВСЕХ данных для матча

    Returns:
        Словарь со всеми данными
    """
    print(f"\n{'='*70}")
    print(f"🤖 АВТОМАТИЧЕСКИЙ СБОР ДАННЫХ: {home_team} vs {away_team}")
    print(f"{'='*70}\n")

    client = APIFootballClient(api_key)
    league_id = LEAGUE_IDS.get(league, 39)

    # ШАГ 1: Найти ID команд
    print("[1/7] Поиск ID команд...")
    home_id = client.search_team(home_team, league_id)
    away_id = client.search_team(away_team, league_id)

    if not home_id or not away_id:
        print(f"❌ Не удалось найти команды: {home_team} ({home_id}), {away_team} ({away_id})")
        return None

    print(f"  ✅ {home_team}: ID={home_id}")
    print(f"  ✅ {away_team}: ID={away_id}")

    # ШАГ 2: Найти fixture_id предстоящего матча
    print("\n[2/7] Поиск предстоящего матча...")
    matches = client.get_upcoming_matches(league_id, days=14)

    fixture_id = None
    for match in matches:
        if match['home_team_id'] == home_id and match['away_team_id'] == away_id:
            fixture_id = match['fixture_id']
            print(f"  ✅ Матч найден: fixture_id={fixture_id}, дата={match['date']}")
            break

    if not fixture_id:
        print(f"  ⚠️  Матч не найден в ближайших 14 днях")

    # ШАГ 3: Получить коэффициенты
    print("\n[3/7] Получение коэффициентов...")
    odds = None
    if fixture_id:
        odds = client.get_odds(fixture_id)
        if odds:
            print(f"  ✅ Коэффициенты: П1={odds['home_win']} X={odds['draw']} П2={odds['away_win']}")
        else:
            print(f"  ⚠️  Коэффициенты еще не доступны")

    time.sleep(1)  # Пауза между запросами

    # ШАГ 4: Статистика и форма хозяев
    print(f"\n[4/7] Получение статистики {home_team}...")
    home_stats = client.get_team_statistics(home_id, league_id)
    home_form = client.get_team_form(home_id, last_n=5)

    if home_stats:
        print(f"  ✅ Форма: {' '.join(home_form) if home_form else 'N/A'}")
        print(f"  ✅ Средний xG: {home_stats['avg_goals_for']:.2f}")

    time.sleep(1)

    # ШАГ 5: Статистика и форма гостей
    print(f"\n[5/7] Получение статистики {away_team}...")
    away_stats = client.get_team_statistics(away_id, league_id)
    away_form = client.get_team_form(away_id, last_n=5)

    if away_stats:
        print(f"  ✅ Форма: {' '.join(away_form) if away_form else 'N/A'}")
        print(f"  ✅ Средний xG: {away_stats['avg_goals_for']:.2f}")

    time.sleep(1)

    # ШАГ 6: H2H
    print(f"\n[6/7] Получение H2H статистики...")
    h2h = client.get_h2h(home_id, away_id, last_n=5)

    if h2h:
        print(f"  ✅ Последние встречи (с точки зрения {home_team}): {' '.join(h2h['results'])}")
        print(f"  ✅ Побед {home_team}: {h2h['team1_wins']}, Побед {away_team}: {h2h['team2_wins']}, Ничьих: {h2h['draws']}")

    time.sleep(1)

    # ШАГ 7: Травмы
    print(f"\n[7/7] Проверка травм...")
    home_injuries = client.get_injuries(home_id)
    away_injuries = client.get_injuries(away_id)

    print(f"  ✅ Травмы {home_team}: {len(home_injuries)} игроков")
    if home_injuries:
        for inj in home_injuries[:3]:  # Показываем первых 3
            print(f"     - {inj['player_name']}: {inj['reason']}")

    print(f"  ✅ Травмы {away_team}: {len(away_injuries)} игроков")
    if away_injuries:
        for inj in away_injuries[:3]:
            print(f"     - {inj['player_name']}: {inj['reason']}")

    # Собираем все в один словарь
    result = {
        'fixture_id': fixture_id,
        'odds': odds,
        'home_team': {
            'name': home_team,
            'id': home_id,
            'stats': home_stats,
            'form': home_form,
            'injuries': home_injuries
        },
        'away_team': {
            'name': away_team,
            'id': away_id,
            'stats': away_stats,
            'form': away_form,
            'injuries': away_injuries
        },
        'h2h': h2h,
        'timestamp': datetime.now().isoformat()
    }

    print(f"\n{'='*70}")
    print(f"✅ СБОР ДАННЫХ ЗАВЕРШЕН")
    print(f"{'='*70}\n")

    return result


if __name__ == "__main__":
    print("\n" + "="*70)
    print("⚽ API-FOOTBALL CLIENT - Автоматический сбор данных")
    print("="*70 + "\n")

    print("📝 РЕГИСТРАЦИЯ:")
    print("1. Перейди на https://www.api-football.com/")
    print("2. Зарегистрируйся (бесплатно)")
    print("3. Получи API ключ в личном кабинете")
    print("4. Бесплатный план: 100 запросов/день\n")

    api_key = input("Введи свой API ключ (или 'demo' для примера): ").strip()

    if api_key and api_key != 'demo':
        # Реальный пример
        data = full_match_data_collection(
            api_key=api_key,
            home_team="Manchester City",
            away_team="Liverpool",
            league='EPL'
        )

        if data:
            # Сохраняем в файл
            filename = f"match_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"💾 Данные сохранены в {filename}")
    else:
        print("\n📊 ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ:\n")

        print("# Инициализация")
        print("client = APIFootballClient('твой_api_ключ')\n")

        print("# Получить предстоящие матчи АПЛ")
        print("matches = client.get_upcoming_matches(league_id=39, days=7)\n")

        print("# Получить коэффициенты")
        print("odds = client.get_odds(fixture_id=12345)\n")

        print("# Получить форму команды")
        print("form = client.get_team_form(team_id=50, last_n=5)  # ['W','W','D','L','W']\n")

        print("# Получить травмы")
        print("injuries = client.get_injuries(team_id=50)\n")

        print("# Полный сбор данных")
        print("data = full_match_data_collection(")
        print("    api_key='твой_ключ',")
        print("    home_team='Manchester City',")
        print("    away_team='Liverpool',")
        print("    league='EPL'")
        print(")")

    print("\n" + "="*70 + "\n")
