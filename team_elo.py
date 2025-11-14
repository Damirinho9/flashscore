"""
ELO-рейтинг для команд
Дополнительная метрика для улучшения прогнозов на основе xG
"""

import json
from typing import Dict, Optional
from datetime import datetime
import math


class EloRatingSystem:
    """
    Система ELO-рейтинга для футбольных команд
    Можно использовать как дополнительный фактор к xG
    """

    def __init__(self, k_factor: float = 32, home_advantage: float = 100):
        """
        Args:
            k_factor: Коэффициент K (скорость изменения рейтинга)
                      32 - стандартное значение
                      20 - для топ-команд (более стабильно)
                      40 - для молодых команд (быстрая адаптация)
            home_advantage: Преимущество дома в единицах ELO
        """
        self.k_factor = k_factor
        self.home_advantage = home_advantage
        self.ratings = {}
        self.default_rating = 1500  # Начальный рейтинг

    def get_rating(self, team: str) -> float:
        """Получить текущий рейтинг команды"""
        return self.ratings.get(team, self.default_rating)

    def set_rating(self, team: str, rating: float):
        """Установить рейтинг команды"""
        self.ratings[team] = rating

    def expected_score(self, rating_a: float, rating_b: float) -> float:
        """
        Рассчитать ожидаемый результат для команды A

        Returns:
            Вероятность победы от 0 до 1
        """
        return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

    def update_ratings(self, home_team: str, away_team: str,
                      home_goals: int, away_goals: int) -> Dict[str, float]:
        """
        Обновить рейтинги после матча

        Args:
            home_team: Команда-хозяин
            away_team: Гостевая команда
            home_goals: Голы хозяев
            away_goals: Голы гостей

        Returns:
            Словарь с новыми рейтингами {'home': new_rating, 'away': new_rating}
        """
        # Получаем текущие рейтинги
        home_rating = self.get_rating(home_team)
        away_rating = self.get_rating(away_team)

        # Учитываем домашнее преимущество
        adjusted_home = home_rating + self.home_advantage
        adjusted_away = away_rating

        # Ожидаемые результаты
        expected_home = self.expected_score(adjusted_home, adjusted_away)
        expected_away = 1 - expected_home

        # Фактический результат (1 = победа, 0.5 = ничья, 0 = поражение)
        if home_goals > away_goals:
            actual_home, actual_away = 1.0, 0.0
        elif home_goals < away_goals:
            actual_home, actual_away = 0.0, 1.0
        else:
            actual_home, actual_away = 0.5, 0.5

        # Учитываем разницу голов (больше разница = больше изменение рейтинга)
        goal_diff = abs(home_goals - away_goals)
        multiplier = self._goal_difference_multiplier(goal_diff)

        # Обновляем рейтинги
        new_home_rating = home_rating + self.k_factor * multiplier * (actual_home - expected_home)
        new_away_rating = away_rating + self.k_factor * multiplier * (actual_away - expected_away)

        # Сохраняем новые рейтинги
        self.set_rating(home_team, new_home_rating)
        self.set_rating(away_team, new_away_rating)

        return {
            'home': new_home_rating,
            'away': new_away_rating,
            'home_change': new_home_rating - home_rating,
            'away_change': new_away_rating - away_rating
        }

    def _goal_difference_multiplier(self, goal_diff: int) -> float:
        """
        Множитель на основе разницы голов
        Чем больше разгром, тем значительнее изменение рейтинга
        """
        if goal_diff <= 1:
            return 1.0
        elif goal_diff == 2:
            return 1.5
        else:
            return (goal_diff + 11) / 8

    def predict_match(self, home_team: str, away_team: str) -> Dict[str, float]:
        """
        Прогноз матча на основе ELO

        Returns:
            Словарь с вероятностями: {'home_win', 'draw', 'away_win'}
        """
        home_rating = self.get_rating(home_team)
        away_rating = self.get_rating(away_team)

        # Учитываем домашнее преимущество
        adjusted_home = home_rating + self.home_advantage
        adjusted_away = away_rating

        # Базовая вероятность победы хозяев
        home_win_prob = self.expected_score(adjusted_home, adjusted_away)

        # Оценка вероятности ничьей (эмпирическая формула)
        rating_diff = abs(adjusted_home - adjusted_away)
        draw_prob = 0.25 * math.exp(-rating_diff / 500)

        # Нормализуем вероятности
        total = home_win_prob + draw_prob + (1 - home_win_prob)
        home_win_prob = home_win_prob / total
        draw_prob = draw_prob / total
        away_win_prob = 1 - home_win_prob - draw_prob

        return {
            'home_win': home_win_prob,
            'draw': draw_prob,
            'away_win': away_win_prob,
            'home_rating': home_rating,
            'away_rating': away_rating
        }

    def get_top_teams(self, n: int = 20) -> list:
        """Получить топ-N команд по рейтингу"""
        sorted_teams = sorted(self.ratings.items(), key=lambda x: x[1], reverse=True)
        return sorted_teams[:n]

    def save_ratings(self, filename: str = 'elo_ratings.json'):
        """Сохранить рейтинги в файл"""
        data = {
            'ratings': self.ratings,
            'k_factor': self.k_factor,
            'home_advantage': self.home_advantage,
            'timestamp': datetime.now().isoformat()
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_ratings(self, filename: str = 'elo_ratings.json'):
        """Загрузить рейтинги из файла"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.ratings = data['ratings']
            self.k_factor = data.get('k_factor', self.k_factor)
            self.home_advantage = data.get('home_advantage', self.home_advantage)
            return True
        except FileNotFoundError:
            return False


def combine_xg_and_elo(xg_prob: Dict, elo_prob: Dict, weight_xg: float = 0.7) -> Dict:
    """
    Комбинировать прогнозы на основе xG и ELO

    Args:
        xg_prob: Вероятности из модели на основе xG
        elo_prob: Вероятности из ELO
        weight_xg: Вес xG модели (0-1), остальное - вес ELO
                   0.7 = 70% xG, 30% ELO (рекомендуется)

    Returns:
        Комбинированные вероятности
    """
    weight_elo = 1 - weight_xg

    combined = {
        'home_win': xg_prob['home_win'] * weight_xg + elo_prob['home_win'] * weight_elo,
        'draw': xg_prob['draw'] * weight_xg + elo_prob['draw'] * weight_elo,
        'away_win': xg_prob['away_win'] * weight_xg + elo_prob['away_win'] * weight_elo
    }

    # Нормализуем (на случай погрешностей округления)
    total = sum(combined.values())
    combined = {k: v / total for k, v in combined.items()}

    return combined


def initialize_league_ratings(league: str = 'EPL') -> EloRatingSystem:
    """
    Инициализировать примерные ELO-рейтинги для лиги

    Это стартовые значения, которые будут уточняться по мере обновления
    """
    elo = EloRatingSystem()

    # Примерные начальные рейтинги АПЛ (сезон 2024)
    epl_ratings = {
        'Manchester City': 1850,
        'Liverpool': 1780,
        'Arsenal': 1770,
        'Aston Villa': 1680,
        'Tottenham': 1670,
        'Manchester United': 1650,
        'Chelsea': 1640,
        'Newcastle United': 1630,
        'Brighton': 1600,
        'West Ham': 1580,
        'Fulham': 1560,
        'Brentford': 1550,
        'Crystal Palace': 1530,
        'Bournemouth': 1520,
        'Nottingham Forest': 1510,
        'Everton': 1490,
        'Wolves': 1480,
        'Ipswich': 1460,
        'Southampton': 1450,
        'Leicester': 1440
    }

    if league == 'EPL':
        for team, rating in epl_ratings.items():
            elo.set_rating(team, rating)

    # Можно добавить рейтинги для других лиг

    return elo


def example_usage():
    """Пример использования ELO-рейтинга"""

    print("\n" + "="*70)
    print("⚽ СИСТЕМА ELO-РЕЙТИНГА")
    print("="*70 + "\n")

    # Инициализируем систему с рейтингами АПЛ
    elo = initialize_league_ratings('EPL')

    # Пример 1: Прогноз матча
    print("ПРИМЕР 1: Прогноз на основе ELO\n")

    home_team = "Manchester City"
    away_team = "Liverpool"

    prediction = elo.predict_match(home_team, away_team)

    print(f"{home_team} vs {away_team}")
    print(f"\nРейтинги:")
    print(f"  {home_team}: {prediction['home_rating']:.0f}")
    print(f"  {away_team}: {prediction['away_rating']:.0f}")
    print(f"\nВероятности (ELO):")
    print(f"  П1: {prediction['home_win']:.1%}")
    print(f"  X:  {prediction['draw']:.1%}")
    print(f"  П2: {prediction['away_win']:.1%}")

    # Пример 2: Обновление после матча
    print("\n" + "-"*70)
    print("ПРИМЕР 2: Обновление рейтингов после матча\n")

    # Предположим, Сити выиграл 3:1
    result = elo.update_ratings(home_team, away_team, 3, 1)

    print(f"Результат: {home_team} 3:1 {away_team}")
    print(f"\nИзменение рейтингов:")
    print(f"  {home_team}: {result['home']:.0f} ({result['home_change']:+.0f})")
    print(f"  {away_team}: {result['away']:.0f} ({result['away_change']:+.0f})")

    # Пример 3: Комбинация с xG
    print("\n" + "-"*70)
    print("ПРИМЕР 3: Комбинированный прогноз (xG + ELO)\n")

    # Прогноз на основе xG (из основной модели)
    xg_prediction = {
        'home_win': 0.542,
        'draw': 0.231,
        'away_win': 0.227
    }

    # Прогноз на основе ELO
    elo_prediction = elo.predict_match("Arsenal", "Chelsea")

    # Комбинируем (70% xG + 30% ELO)
    combined = combine_xg_and_elo(xg_prediction, elo_prediction, weight_xg=0.7)

    print("Arsenal vs Chelsea")
    print(f"\nПрогноз xG:     П1={xg_prediction['home_win']:.1%} | X={xg_prediction['draw']:.1%} | П2={xg_prediction['away_win']:.1%}")
    print(f"Прогноз ELO:    П1={elo_prediction['home_win']:.1%} | X={elo_prediction['draw']:.1%} | П2={elo_prediction['away_win']:.1%}")
    print(f"Комбинированный: П1={combined['home_win']:.1%} | X={combined['draw']:.1%} | П2={combined['away_win']:.1%}")

    # Пример 4: Топ команд
    print("\n" + "-"*70)
    print("ПРИМЕР 4: Топ-10 команд по ELO\n")

    top_teams = elo.get_top_teams(10)
    for i, (team, rating) in enumerate(top_teams, 1):
        print(f"{i:2d}. {team:20s} {rating:.0f}")

    # Сохраняем рейтинги
    elo.save_ratings()
    print("\n💾 Рейтинги сохранены в elo_ratings.json")

    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    example_usage()

    print("="*70)
    print("📝 КАК ИСПОЛЬЗОВАТЬ")
    print("="*70)
    print("""
1. Базовое использование:
   elo = EloRatingSystem()
   prediction = elo.predict_match("Team A", "Team B")

2. Обновление после матча:
   elo.update_ratings("Team A", "Team B", goals_a=2, goals_b=1)

3. Комбинация с xG (рекомендуется):
   combined = combine_xg_and_elo(xg_prob, elo_prob, weight_xg=0.7)

4. Сохранение/загрузка рейтингов:
   elo.save_ratings('my_ratings.json')
   elo.load_ratings('my_ratings.json')

💡 СОВЕТЫ:
   - ELO лучше работает на длинной дистанции (100+ матчей)
   - Комбинируй с xG для лучших результатов (70% xG + 30% ELO)
   - Регулярно обновляй рейтинги после каждого тура
   - K-factor: 32 стандарт, 20 для стабильных лиг, 40 для молодых
   - Home advantage: 100 для топ-лиг, 50-80 для слабых лиг
    """)
    print("="*70 + "\n")
