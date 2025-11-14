"""
Парсер для Flashscore.com
Получение актуальных данных: коэффициенты, форма, таблица, статистика
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import time
from typing import Dict, List, Optional
from datetime import datetime


class FlashscoreParser:
    """
    Парсер для flashscore.com

    ВАЖНО: Flashscore активно борется с парсерами, поэтому:
    1. Используй задержки между запросами (2-3 секунды минимум)
    2. Меняй User-Agent
    3. Возможно потребуется использовать прокси
    4. Рассмотри использование API (платный, но надежнее)
    """

    def __init__(self):
        self.base_url = "https://www.flashscore.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

    def get_match_odds(self, match_id: str) -> Optional[Dict]:
        """
        Получить коэффициенты на матч

        Args:
            match_id: ID матча из Flashscore (например, 'WjXr7wKC')

        Returns:
            Словарь с коэффициентами или None
        """
        try:
            url = f"{self.base_url}/match/{match_id}/#/match-summary"
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Ищем блок с коэффициентами
            # ВАЖНО: Структура Flashscore может измениться, нужна периодическая проверка
            odds_section = soup.find('div', class_='_odds_')

            if not odds_section:
                print("⚠️  Коэффициенты не найдены на странице")
                return None

            # Парсим коэффициенты основных букмекеров
            odds = self._parse_odds_block(odds_section)

            return odds

        except requests.Timeout:
            print(f"⏱️  Таймаут при получении коэффициентов для матча {match_id}")
            return None
        except requests.RequestException as e:
            print(f"❌ Ошибка сети: {e}")
            return None
        except Exception as e:
            print(f"❌ Ошибка парсинга коэффициентов: {e}")
            return None

    def _parse_odds_block(self, odds_section) -> Dict:
        """Парсинг блока с коэффициентами"""
        # Это заглушка - реальная структура зависит от актуальной верстки Flashscore
        # Нужно исследовать структуру страницы и адаптировать

        odds = {
            'home_win': None,
            'draw': None,
            'away_win': None,
            'over_2.5': None,
            'under_2.5': None,
            'btts': None,
            'bookmaker': 'Unknown',
            'timestamp': datetime.now().isoformat()
        }

        # TODO: Реальная реализация парсинга коэффициентов

        return odds

    def get_team_form(self, team_name: str, league: str = 'england/premier-league') -> Optional[Dict]:
        """
        Получить форму команды (последние матчи)

        Args:
            team_name: Название команды
            league: Путь к лиге (например, 'england/premier-league')

        Returns:
            Статистика формы команды
        """
        try:
            # Формируем URL команды
            team_url = team_name.lower().replace(' ', '-')
            url = f"{self.base_url}/team/{team_url}/{team_url_id}/"

            # ВАЖНО: Нужен реальный ID команды из Flashscore
            # Можно получить через поиск или из URL матча

            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Парсим последние результаты
            form_data = {
                'team_name': team_name,
                'last_5_results': [],  # ['W', 'W', 'D', 'L', 'W']
                'last_5_goals_scored': [],
                'last_5_goals_conceded': [],
                'wins_last_5': 0,
                'draws_last_5': 0,
                'losses_last_5': 0
            }

            # TODO: Реальная реализация парсинга формы

            return form_data

        except Exception as e:
            print(f"❌ Ошибка получения формы команды: {e}")
            return None

    def get_league_table(self, league: str = 'england/premier-league') -> Optional[List[Dict]]:
        """
        Получить турнирную таблицу

        Args:
            league: Путь к лиге

        Returns:
            Список команд с позициями, очками и т.д.
        """
        try:
            url = f"{self.base_url}/football/{league}/standings/"
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            table = []
            # TODO: Парсинг турнирной таблицы

            return table

        except Exception as e:
            print(f"❌ Ошибка получения таблицы: {e}")
            return None

    def get_h2h_stats(self, match_id: str) -> Optional[Dict]:
        """
        Получить статистику личных встреч (H2H)

        Args:
            match_id: ID матча

        Returns:
            Статистика H2H
        """
        try:
            url = f"{self.base_url}/match/{match_id}/#/h2h/overall"
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            h2h = {
                'total_matches': 0,
                'home_wins': 0,
                'draws': 0,
                'away_wins': 0,
                'last_5_results': []
            }

            # TODO: Парсинг H2H статистики

            return h2h

        except Exception as e:
            print(f"❌ Ошибка получения H2H: {e}")
            return None


class FlashscoreAPIClient:
    """
    Альтернатива парсингу - использование API

    Есть несколько вариантов:
    1. RapidAPI - Flashscore API (платный, но официальный)
    2. API-Football (бесплатный лимит 100 запросов/день)
    3. Football-Data.org (бесплатный, но ограниченный)
    """

    def __init__(self, api_key: str = None, provider: str = 'rapidapi'):
        self.api_key = api_key
        self.provider = provider

        if provider == 'rapidapi':
            self.base_url = "https://flashscore.p.rapidapi.com"
            self.headers = {
                'X-RapidAPI-Key': api_key,
                'X-RapidAPI-Host': 'flashscore.p.rapidapi.com'
            }
        elif provider == 'api-football':
            self.base_url = "https://v3.football.api-sports.io"
            self.headers = {
                'x-apisports-key': api_key
            }

    def get_odds(self, fixture_id: int) -> Optional[Dict]:
        """Получить коэффициенты через API"""
        if not self.api_key:
            print("❌ API ключ не установлен")
            return None

        try:
            if self.provider == 'api-football':
                url = f"{self.base_url}/odds"
                params = {'fixture': fixture_id}

                response = requests.get(url, headers=self.headers, params=params, timeout=15)
                response.raise_for_status()

                data = response.json()

                # Обрабатываем ответ API
                if data['response']:
                    return self._parse_api_odds(data['response'][0])

            return None

        except Exception as e:
            print(f"❌ Ошибка API: {e}")
            return None

    def _parse_api_odds(self, api_response: Dict) -> Dict:
        """Парсинг ответа API в единый формат"""
        odds = {
            'home_win': None,
            'draw': None,
            'away_win': None,
            'over_2.5': None,
            'under_2.5': None,
            'btts_yes': None,
            'btts_no': None
        }

        # Извлекаем коэффициенты из ответа API
        for bookmaker in api_response.get('bookmakers', []):
            for bet in bookmaker.get('bets', []):
                if bet['name'] == 'Match Winner':
                    for value in bet['values']:
                        if value['value'] == 'Home':
                            odds['home_win'] = float(value['odd'])
                        elif value['value'] == 'Draw':
                            odds['draw'] = float(value['odd'])
                        elif value['value'] == 'Away':
                            odds['away_win'] = float(value['odd'])

                elif bet['name'] == 'Goals Over/Under':
                    for value in bet['values']:
                        if 'Over 2.5' in value['value']:
                            odds['over_2.5'] = float(value['odd'])
                        elif 'Under 2.5' in value['value']:
                            odds['under_2.5'] = float(value['odd'])

                elif bet['name'] == 'Both Teams Score':
                    for value in bet['values']:
                        if value['value'] == 'Yes':
                            odds['btts_yes'] = float(value['odd'])
                        elif value['value'] == 'No':
                            odds['btts_no'] = float(value['odd'])

        return odds


def manual_odds_input(home_team: str, away_team: str) -> Dict:
    """
    Ручной ввод коэффициентов (если парсинг не работает)

    Самый надежный способ - просто открыть Flashscore/букмекера
    и вручную ввести коэффициенты
    """
    print(f"\n{'='*70}")
    print(f"ВВОД КОЭФФИЦИЕНТОВ: {home_team} vs {away_team}")
    print(f"{'='*70}\n")

    print("Открой сайт букмекера или Flashscore и введи актуальные коэффициенты:\n")

    try:
        home_win = float(input(f"П1 (победа {home_team}): "))
        draw = float(input(f"X (ничья): "))
        away_win = float(input(f"П2 (победа {away_team}): "))
        over_2_5 = float(input(f"ТБ 2.5: "))
        under_2_5 = float(input(f"ТМ 2.5: "))
        btts = float(input(f"Обе забьют (да): "))

        odds = {
            'home_win': home_win,
            'draw': draw,
            'away_win': away_win,
            'over_2.5': over_2_5,
            'under_2.5': under_2_5,
            'btts': btts,
            'source': 'manual_input',
            'timestamp': datetime.now().isoformat()
        }

        print(f"\n✅ Коэффициенты введены успешно")
        return odds

    except ValueError:
        print("\n❌ Ошибка ввода. Используй числовой формат (например, 1.85)")
        return None
    except KeyboardInterrupt:
        print("\n\n⚠️  Ввод отменен")
        return None


def get_odds_from_csv(csv_file: str, home_team: str, away_team: str) -> Optional[Dict]:
    """
    Загрузить коэффициенты из CSV файла

    Можешь заранее подготовить CSV с коэффициентами на предстоящие матчи:

    home_team,away_team,home_win,draw,away_win,over_2.5,under_2.5,btts
    Manchester City,Liverpool,1.85,4.00,4.20,1.60,2.30,1.75
    Arsenal,Chelsea,2.10,3.60,3.40,1.70,2.15,1.80
    """
    import pandas as pd

    try:
        df = pd.read_csv(csv_file)

        match = df[(df['home_team'] == home_team) & (df['away_team'] == away_team)]

        if match.empty:
            print(f"⚠️  Матч {home_team} vs {away_team} не найден в {csv_file}")
            return None

        odds = {
            'home_win': float(match['home_win'].iloc[0]),
            'draw': float(match['draw'].iloc[0]),
            'away_win': float(match['away_win'].iloc[0]),
            'over_2.5': float(match['over_2.5'].iloc[0]),
            'under_2.5': float(match['under_2.5'].iloc[0]),
            'btts': float(match['btts'].iloc[0]),
            'source': csv_file,
            'timestamp': datetime.now().isoformat()
        }

        print(f"✅ Коэффициенты загружены из {csv_file}")
        return odds

    except Exception as e:
        print(f"❌ Ошибка чтения CSV: {e}")
        return None


if __name__ == "__main__":
    print("\n" + "="*70)
    print("⚽ FLASHSCORE PARSER")
    print("="*70 + "\n")

    print("📝 ВАЖНАЯ ИНФОРМАЦИЯ:")
    print("-" * 70)
    print("""
Flashscore активно защищает свой сайт от парсинга. Варианты получения данных:

1. 🔧 Парсинг (сложно, может не работать):
   - Требует обхода защиты (CAPTCHA, rate limiting)
   - Структура сайта часто меняется
   - Может потребоваться Selenium + прокси

2. 💰 API (рекомендуется для продакшена):
   - API-Football.com: 100 запросов/день бесплатно
   - RapidAPI Flashscore: платный, но надежный
   - Football-Data.org: бесплатный, ограниченный

3. ✋ Ручной ввод (самый надежный для начала):
   - Открываешь Flashscore
   - Копируешь коэффициенты
   - Вводишь в систему

4. 📊 CSV файл (для batch-анализа):
   - Подготавливаешь файл с коэффициентами заранее
   - Система читает их автоматически

РЕКОМЕНДАЦИЯ для твоего случая:
- Начни с ручного ввода или CSV
- Если нужна автоматизация → используй API-Football (100 запросов/день хватит)
- Если нужен production → плати за RapidAPI
    """)

    print("="*70)
    print("\nПРИМЕР 1: Ручной ввод коэффициентов\n")

    odds = manual_odds_input("Manchester City", "Liverpool")
    if odds:
        print(f"\nПолученные коэффициенты:")
        print(json.dumps(odds, indent=2, ensure_ascii=False))

    print("\n" + "="*70)
    print("\nПРИМЕР 2: Загрузка из CSV\n")

    print("Создай файл odds.csv с колонками:")
    print("home_team,away_team,home_win,draw,away_win,over_2.5,under_2.5,btts")
    print("\nЗатем используй:")
    print("odds = get_odds_from_csv('odds.csv', 'Manchester City', 'Liverpool')")

    print("\n" + "="*70)
    print("\nПРИМЕР 3: API-Football (если есть API ключ)\n")

    print("""
# Регистрируйся на https://www.api-football.com/
# Получи бесплатный API ключ (100 запросов/день)

api_client = FlashscoreAPIClient(
    api_key='твой_ключ',
    provider='api-football'
)

odds = api_client.get_odds(fixture_id=12345)
    """)

    print("\n" + "="*70 + "\n")
