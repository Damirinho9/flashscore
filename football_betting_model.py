"""
Модель прогнозирования футбольных матчей на основе xG
Парсинг данных с understat + расчет вероятностей + value betting
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from scipy.stats import poisson
import numpy as np
from datetime import datetime, timedelta
import pandas as pd


class FootballBettingModel:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
    def get_team_stats_understat(self, team_name, league, season='2024'):
        """Получить статистику команды с understat"""
        try:
            # Преобразуем название команды для URL
            team_url = team_name.replace(' ', '_')
            url = f'https://understat.com/team/{team_url}/{season}'
            
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Ищем JSON данные в скриптах
            scripts = soup.find_all('script')
            team_data = None
            
            for script in scripts:
                if 'var teamsData' in script.text:
                    # Извлекаем JSON
                    json_text = re.search(r'var teamsData\s*=\s*JSON\.parse\(\'(.+?)\'\)', script.text)
                    if json_text:
                        team_data = json.loads(json_text.group(1).encode().decode('unicode_escape'))
                        break
            
            return team_data
        except Exception as e:
            print(f"Ошибка получения данных: {e}")
            return None
    
    def calculate_team_strength(self, matches_data):
        """Рассчитать силу команды на основе последних матчей"""
        if not matches_data:
            return None
        
        recent_matches = matches_data[-10:]  # Последние 10 матчей
        
        xg_for = []
        xg_against = []
        goals_for = []
        goals_against = []
        
        for match in recent_matches:
            xg_for.append(float(match.get('xG', 0)))
            xg_against.append(float(match.get('xGA', 0)))
            goals_for.append(int(match.get('scored', 0)))
            goals_against.append(int(match.get('missed', 0)))
        
        return {
            'avg_xg_for': np.mean(xg_for),
            'avg_xg_against': np.mean(xg_against),
            'avg_goals_for': np.mean(goals_for),
            'avg_goals_against': np.mean(goals_against),
            'xg_std': np.std(xg_for),
            'form': sum(goals_for[-5:]) - sum(goals_against[-5:])  # Форма по последним 5
        }
    
    def predict_match_poisson(self, home_xg, away_xg, max_goals=7):
        """
        Прогноз матча методом Пуассона
        Возвращает вероятности всех счетов и исходов
        """
        # Матрица вероятностей счетов
        prob_matrix = np.zeros((max_goals + 1, max_goals + 1))
        
        for i in range(max_goals + 1):
            for j in range(max_goals + 1):
                prob_matrix[i][j] = poisson.pmf(i, home_xg) * poisson.pmf(j, away_xg)
        
        # Вероятности исходов
        home_win = np.sum(np.tril(prob_matrix, -1))  # Ниже диагонали
        draw = np.sum(np.diag(prob_matrix))           # Диагональ
        away_win = np.sum(np.triu(prob_matrix, 1))    # Выше диагонали
        
        # Тоталы
        over_2_5 = sum([prob_matrix[i][j] for i in range(max_goals + 1) 
                        for j in range(max_goals + 1) if i + j > 2.5])
        under_2_5 = 1 - over_2_5
        
        over_1_5 = sum([prob_matrix[i][j] for i in range(max_goals + 1) 
                        for j in range(max_goals + 1) if i + j > 1.5])
        
        btts = sum([prob_matrix[i][j] for i in range(1, max_goals + 1) 
                    for j in range(1, max_goals + 1)])
        
        return {
            'home_win': home_win,
            'draw': draw,
            'away_win': away_win,
            'over_2.5': over_2_5,
            'under_2.5': under_2_5,
            'over_1.5': over_1_5,
            'btts': btts,
            'expected_home_goals': home_xg,
            'expected_away_goals': away_xg,
            'probability_matrix': prob_matrix
        }
    
    def calculate_value(self, true_prob, bookmaker_odds):
        """
        Расчет value bet
        true_prob: твоя оценка вероятности
        bookmaker_odds: коэффициент букмекера
        """
        implied_prob = 1 / bookmaker_odds
        value = (true_prob * bookmaker_odds) - 1
        edge = true_prob - implied_prob
        
        return {
            'value': value,
            'edge': edge,
            'is_value': value > 0,
            'true_prob': true_prob,
            'implied_prob': implied_prob
        }
    
    def kelly_criterion(self, true_prob, bookmaker_odds, fraction=0.25):
        """
        Расчет оптимального размера ставки по Келли
        fraction: доля от полного Келли (0.25 = четверть Келли)
        """
        if bookmaker_odds <= 1:
            return 0
        
        kelly = (bookmaker_odds * true_prob - 1) / (bookmaker_odds - 1)
        
        # Консервативный подход - четверть Келли
        kelly_fraction = kelly * fraction
        
        # Не ставим, если отрицательное или слишком большое
        if kelly_fraction <= 0:
            return 0
        if kelly_fraction > 0.05:  # Максимум 5% банка
            return 0.05
        
        return kelly_fraction
    
    def analyze_match(self, home_team, away_team, home_xg, away_xg, 
                     bookmaker_odds=None, home_advantage=0.3):
        """
        Полный анализ матча
        home_advantage: преимущество домашней команды в xG (обычно 0.2-0.4)
        """
        # Корректируем xG с учетом домашнего преимущества
        adjusted_home_xg = home_xg + home_advantage
        adjusted_away_xg = away_xg
        
        # Прогноз
        prediction = self.predict_match_poisson(adjusted_home_xg, adjusted_away_xg)
        
        result = {
            'home_team': home_team,
            'away_team': away_team,
            'prediction': prediction,
            'recommendation': []
        }
        
        # Если есть коэффициенты букмекера - ищем value
        if bookmaker_odds:
            markets = {
                'home_win': ('П1', prediction['home_win']),
                'draw': ('X', prediction['draw']),
                'away_win': ('П2', prediction['away_win']),
                'over_2.5': ('ТБ 2.5', prediction['over_2.5']),
                'under_2.5': ('ТМ 2.5', prediction['under_2.5']),
                'btts': ('ОЗ', prediction['btts'])
            }
            
            for market, (name, true_prob) in markets.items():
                if market in bookmaker_odds:
                    odds = bookmaker_odds[market]
                    value_info = self.calculate_value(true_prob, odds)
                    kelly = self.kelly_criterion(true_prob, odds)
                    
                    if value_info['is_value'] and kelly > 0.01:  # Минимум 1% банка
                        result['recommendation'].append({
                            'market': name,
                            'odds': odds,
                            'true_prob': f"{true_prob:.1%}",
                            'implied_prob': f"{value_info['implied_prob']:.1%}",
                            'edge': f"{value_info['edge']:.1%}",
                            'value': f"{value_info['value']:.2%}",
                            'kelly_stake': f"{kelly:.1%}"
                        })
        
        return result


def example_usage():
    """Пример использования модели"""
    model = FootballBettingModel()
    
    # Пример: Манчестер Сити vs Арсенал
    # Предположим, собрали статистику:
    home_team = "Manchester City"
    away_team = "Arsenal"
    
    # xG команд на основе последних матчей (средние значения)
    home_avg_xg = 2.1  # Сити дома создают ~2.1 xG
    away_avg_xg = 1.4  # Арсенал в гостях ~1.4 xG
    
    # Коэффициенты букмекера (пример)
    bookmaker_odds = {
        'home_win': 1.75,
        'draw': 4.0,
        'away_win': 4.5,
        'over_2.5': 1.60,
        'under_2.5': 2.30,
        'btts': 1.85
    }
    
    # Анализ
    result = model.analyze_match(
        home_team, away_team,
        home_avg_xg, away_avg_xg,
        bookmaker_odds
    )
    
    print(f"\n{'='*60}")
    print(f"ПРОГНОЗ: {result['home_team']} vs {result['away_team']}")
    print(f"{'='*60}\n")
    
    pred = result['prediction']
    print(f"Ожидаемые голы:")
    print(f"  {home_team}: {pred['expected_home_goals']:.2f}")
    print(f"  {away_team}: {pred['expected_away_goals']:.2f}\n")
    
    print(f"Вероятности исходов:")
    print(f"  П1 (победа хозяев): {pred['home_win']:.1%}")
    print(f"  X  (ничья):          {pred['draw']:.1%}")
    print(f"  П2 (победа гостей):  {pred['away_win']:.1%}\n")
    
    print(f"Вероятности тоталов:")
    print(f"  ТБ 2.5: {pred['over_2.5']:.1%}")
    print(f"  ТМ 2.5: {pred['under_2.5']:.1%}")
    print(f"  Обе забьют: {pred['btts']:.1%}\n")
    
    if result['recommendation']:
        print(f"{'='*60}")
        print(f"VALUE СТАВКИ (рекомендации):")
        print(f"{'='*60}\n")
        
        for rec in result['recommendation']:
            print(f"Рынок: {rec['market']}")
            print(f"  Коэффициент: {rec['odds']}")
            print(f"  Твоя вероятность: {rec['true_prob']}")
            print(f"  Вероятность букмекера: {rec['implied_prob']}")
            print(f"  Edge (преимущество): {rec['edge']}")
            print(f"  Value: {rec['value']}")
            print(f"  Размер ставки (Kelly): {rec['kelly_stake']} от банка")
            print()
    else:
        print("Value ставок не найдено. Все коэффициенты справедливы.")
    
    print(f"{'='*60}\n")


if __name__ == "__main__":
    example_usage()
    
    # Дополнительный пример с другими данными
    print("\n" + "="*60)
    print("ВТОРОЙ ПРИМЕР: Более оборонительный матч")
    print("="*60 + "\n")
    
    model = FootballBettingModel()
    
    result2 = model.analyze_match(
        "Атлетико Мадрид", "Интер",
        home_xg=1.3,
        away_xg=1.1,
        bookmaker_odds={
            'home_win': 2.20,
            'draw': 3.20,
            'away_win': 3.40,
            'over_2.5': 2.10,
            'under_2.5': 1.75,
            'btts': 1.90
        },
        home_advantage=0.25
    )
    
    pred2 = result2['prediction']
    print(f"Вероятности: П1={pred2['home_win']:.1%}, X={pred2['draw']:.1%}, П2={pred2['away_win']:.1%}")
    print(f"ТБ 2.5: {pred2['over_2.5']:.1%}, ТМ 2.5: {pred2['under_2.5']:.1%}\n")
    
    if result2['recommendation']:
        print("Value ставки найдены:")
        for rec in result2['recommendation']:
            print(f"  {rec['market']}: коэф {rec['odds']}, edge {rec['edge']}, ставка {rec['kelly_stake']}")
    else:
        print("Value не найдено в этом матче.")
