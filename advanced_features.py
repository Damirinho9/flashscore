"""
Расширенные функции: учет травм, формы, мотивации, места в таблице
Корректировка xG на основе дополнительных факторов
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class MatchImportance(Enum):
    """Важность матча (влияет на мотивацию)"""
    LOW = 0.95          # Середина сезона, нет целей
    NORMAL = 1.0        # Обычный матч
    HIGH = 1.05         # Борьба за топ-4/выживание
    CRUCIAL = 1.1       # Финал, решающий матч


@dataclass
class TeamContext:
    """Контекст команды для корректировки прогноза"""
    team_name: str

    # Основные метрики
    base_xg: float                    # Базовый xG из истории
    base_xga: float                   # Базовый xGA (пропущенные)

    # Форма
    last_5_results: List[str]         # ['W', 'W', 'D', 'L', 'W']
    goals_scored_last_5: int
    goals_conceded_last_5: int

    # Турнирная таблица
    league_position: int              # Место в таблице
    points: int
    goal_difference: int

    # Травмы и дисквалификации
    key_players_missing: int          # Количество ключевых игроков
    missing_players_impact: float     # 0.0-1.0, оценка влияния потерь

    # Мотивация
    match_importance: MatchImportance

    # Дополнительные факторы
    rest_days: int                    # Дней отдыха перед матчем
    is_cup_match: bool = False
    manager_new: bool = False         # Новый тренер (бывает всплеск)


class AdvancedAdjustments:
    """Корректировка прогноза на основе дополнительных факторов"""

    def __init__(self):
        # Веса различных факторов
        self.weights = {
            'form': 0.15,           # Влияние формы на xG
            'injuries': 0.20,       # Влияние травм
            'motivation': 0.10,     # Влияние мотивации
            'fatigue': 0.05,        # Влияние усталости
            'manager_bounce': 0.08  # Эффект нового тренера
        }

    def adjust_xg(self, context: TeamContext) -> float:
        """
        Корректировка базового xG с учетом всех факторов

        Returns:
            Скорректированный xG
        """
        adjusted_xg = context.base_xg

        # 1. Корректировка по форме
        form_modifier = self._calculate_form_modifier(context.last_5_results)
        adjusted_xg *= (1 + form_modifier * self.weights['form'])

        # 2. Корректировка по травмам
        injury_modifier = -context.missing_players_impact  # Отрицательное влияние
        adjusted_xg *= (1 + injury_modifier * self.weights['injuries'])

        # 3. Корректировка по мотивации
        motivation_value = context.match_importance.value
        adjusted_xg *= motivation_value

        # 4. Корректировка по усталости
        if context.rest_days < 3:
            fatigue_penalty = (3 - context.rest_days) * 0.05
            adjusted_xg *= (1 - fatigue_penalty * self.weights['fatigue'])

        # 5. Эффект нового тренера (первые 5-10 матчей)
        if context.manager_new:
            adjusted_xg *= (1 + self.weights['manager_bounce'])

        return max(0.1, adjusted_xg)  # Минимум 0.1 xG

    def _calculate_form_modifier(self, results: List[str]) -> float:
        """
        Расчет модификатора формы

        Args:
            results: Список результатов ['W', 'W', 'D', 'L', 'W']

        Returns:
            Модификатор от -0.5 до +0.5
        """
        if not results:
            return 0.0

        # Конвертируем в очки: W=3, D=1, L=0
        points_map = {'W': 3, 'D': 1, 'L': 0}
        points = sum(points_map.get(r, 0) for r in results)

        # Максимум 15 очков (5 побед)
        max_points = len(results) * 3

        # Нормализуем в диапазон -0.5 до +0.5
        # 0 очков = -0.5, средние очки = 0, макс очки = +0.5
        avg_points = max_points / 2
        modifier = ((points - avg_points) / max_points) * 2 * 0.5

        return max(-0.5, min(0.5, modifier))

    def assess_table_motivation(self, position: int, league_size: int = 20) -> MatchImportance:
        """
        Оценка мотивации на основе места в таблице

        Args:
            position: Текущее место в таблице
            league_size: Размер лиги (обычно 20)

        Returns:
            Уровень важности матча
        """
        # Топ-4: борьба за ЛЧ
        if position <= 4:
            return MatchImportance.HIGH

        # 5-6: борьба за еврокубки
        elif position <= 6:
            return MatchImportance.HIGH

        # Зона вылета (последние 3 места)
        elif position >= league_size - 2:
            return MatchImportance.CRUCIAL

        # Над зоной вылета (17-18 место)
        elif position >= league_size - 5:
            return MatchImportance.HIGH

        # Середина таблицы
        else:
            return MatchImportance.LOW

    def calculate_h2h_adjustment(self, h2h_results: List[str], perspective: str = 'home') -> float:
        """
        Корректировка на основе личных встреч

        Args:
            h2h_results: Результаты последних встреч ['W', 'L', 'D', 'W', 'W']
            perspective: 'home' или 'away' - с чьей стороны смотрим

        Returns:
            Модификатор xG (0.8 - 1.2)
        """
        if not h2h_results:
            return 1.0

        wins = h2h_results.count('W')
        losses = h2h_results.count('L')
        total = len(h2h_results)

        # Если команда регулярно выигрывает у оппонента
        win_rate = wins / total

        if win_rate >= 0.7:
            return 1.15  # +15% к xG (психологическое преимущество)
        elif win_rate >= 0.5:
            return 1.05  # +5% к xG
        elif win_rate <= 0.3:
            return 0.9   # -10% к xG (психологический блок)
        else:
            return 1.0

    def estimate_injury_impact(self, missing_players: List[Dict]) -> float:
        """
        Оценка влияния травм

        Args:
            missing_players: Список травмированных игроков с их важностью
                [{'name': 'Haaland', 'position': 'FW', 'importance': 0.9}, ...]

        Returns:
            Суммарное влияние (0.0 - 1.0), где 1.0 = очень сильное влияние
        """
        if not missing_players:
            return 0.0

        total_impact = 0.0

        # Веса позиций (нападающие влияют на xG больше)
        position_weights = {
            'GK': 0.3,   # Вратари влияют на xGA
            'DF': 0.4,   # Защитники
            'MF': 0.6,   # Полузащитники
            'FW': 0.9    # Нападающие (критичны для xG)
        }

        for player in missing_players:
            importance = player.get('importance', 0.5)  # 0.0-1.0
            position = player.get('position', 'MF')
            weight = position_weights.get(position, 0.5)

            total_impact += importance * weight

        # Нормализуем (максимум 3 ключевых игрока)
        return min(1.0, total_impact / 3)


def create_example_context() -> tuple:
    """Пример использования с реальными данными"""

    # Пример: Манчестер Сити без Холанда
    city_context = TeamContext(
        team_name="Manchester City",
        base_xg=2.3,
        base_xga=0.8,
        last_5_results=['W', 'W', 'D', 'W', 'W'],
        goals_scored_last_5=14,
        goals_conceded_last_5=3,
        league_position=2,
        points=45,
        goal_difference=28,
        key_players_missing=1,
        missing_players_impact=0.4,  # Холанд - 40% влияния
        match_importance=MatchImportance.HIGH,
        rest_days=4,
        manager_new=False
    )

    # Пример: Арсенал в полном составе
    arsenal_context = TeamContext(
        team_name="Arsenal",
        base_xg=1.8,
        base_xga=1.1,
        last_5_results=['W', 'W', 'L', 'D', 'W'],
        goals_scored_last_5=10,
        goals_conceded_last_5=6,
        league_position=3,
        points=43,
        goal_difference=18,
        key_players_missing=0,
        missing_players_impact=0.0,
        match_importance=MatchImportance.HIGH,
        rest_days=3,
        manager_new=False
    )

    return city_context, arsenal_context


if __name__ == "__main__":
    print("\n" + "="*70)
    print("🔧 РАСШИРЕННЫЕ ФУНКЦИИ - Учет дополнительных факторов")
    print("="*70 + "\n")

    # Создаем примеры
    city_context, arsenal_context = create_example_context()

    # Инициализируем систему корректировок
    adjuster = AdvancedAdjustments()

    # Корректируем xG с учетом всех факторов
    city_adjusted = adjuster.adjust_xg(city_context)
    arsenal_adjusted = adjuster.adjust_xg(arsenal_context)

    print("ПРИМЕР: Manchester City vs Arsenal\n")
    print("-" * 70)

    print(f"\n{city_context.team_name}:")
    print(f"  Базовый xG (дома): {city_context.base_xg:.2f}")
    print(f"  Форма (последние 5): {' '.join(city_context.last_5_results)}")
    print(f"  Травмированные ключевые игроки: {city_context.key_players_missing}")
    print(f"  Влияние травм: {city_context.missing_players_impact:.0%}")
    print(f"  Дней отдыха: {city_context.rest_days}")
    print(f"  ➡️  СКОРРЕКТИРОВАННЫЙ xG: {city_adjusted:.2f}")
    print(f"  📊 Изменение: {((city_adjusted / city_context.base_xg - 1) * 100):+.1f}%")

    print(f"\n{arsenal_context.team_name}:")
    print(f"  Базовый xG (в гостях): {arsenal_context.base_xg:.2f}")
    print(f"  Форма (последние 5): {' '.join(arsenal_context.last_5_results)}")
    print(f"  Травмированные ключевые игроки: {arsenal_context.key_players_missing}")
    print(f"  Влияние травм: {arsenal_context.missing_players_impact:.0%}")
    print(f"  Дней отдыха: {arsenal_context.rest_days}")
    print(f"  ➡️  СКОРРЕКТИРОВАННЫЙ xG: {arsenal_adjusted:.2f}")
    print(f"  📊 Изменение: {((arsenal_adjusted / arsenal_context.base_xg - 1) * 100):+.1f}%")

    print("\n" + "-" * 70)
    print("\n💡 ИНТЕРПРЕТАЦИЯ:")
    print("-" * 70)
    print(f"""
- Сити без Холанда: базовый xG {city_context.base_xg:.2f} → {city_adjusted:.2f}
  → Травмы снизили атакующий потенциал

- Арсенал в полном составе: базовый xG {arsenal_context.base_xg:.2f} → {arsenal_adjusted:.2f}
  → Хорошая форма компенсирует меньший базовый xG

Эти скорректированные значения используй в основной модели вместо базовых xG!
    """)

    print("\n" + "="*70)
    print("ДОПОЛНИТЕЛЬНЫЕ ПРИМЕРЫ")
    print("="*70 + "\n")

    # Пример: оценка мотивации
    print("1. Оценка мотивации по месту в таблице:\n")

    positions = [1, 5, 10, 18]
    for pos in positions:
        motivation = adjuster.assess_table_motivation(pos, league_size=20)
        print(f"   Место {pos}: {motivation.name} (множитель {motivation.value})")

    # Пример: влияние травм
    print("\n2. Оценка влияния травм:\n")

    injuries_example = [
        {'name': 'Haaland', 'position': 'FW', 'importance': 0.9},
        {'name': 'De Bruyne', 'position': 'MF', 'importance': 0.8}
    ]
    impact = adjuster.estimate_injury_impact(injuries_example)
    print(f"   Травмированы: Haaland (FW), De Bruyne (MF)")
    print(f"   Суммарное влияние: {impact:.1%}")
    print(f"   → xG снизится примерно на {impact * 20:.0%}")

    # Пример: H2H
    print("\n3. Корректировка по личным встречам:\n")

    h2h_dominant = ['W', 'W', 'W', 'D', 'W']  # Команда регулярно выигрывает
    h2h_weak = ['L', 'L', 'D', 'L', 'L']      # Команда регулярно проигрывает

    adj_dominant = adjuster.calculate_h2h_adjustment(h2h_dominant)
    adj_weak = adjuster.calculate_h2h_adjustment(h2h_weak)

    print(f"   H2H (5 последних): {' '.join(h2h_dominant)}")
    print(f"   → Модификатор: {adj_dominant:.2f} (+{(adj_dominant-1)*100:.0f}%)")

    print(f"\n   H2H (5 последних): {' '.join(h2h_weak)}")
    print(f"   → Модификатор: {adj_weak:.2f} ({(adj_weak-1)*100:.0f}%)")

    print("\n" + "="*70)
    print("📝 КАК ИСПОЛЬЗОВАТЬ В МОДЕЛИ")
    print("="*70)
    print("""
from advanced_features import TeamContext, AdvancedAdjustments, MatchImportance

# 1. Создаешь контекст для каждой команды
home_context = TeamContext(
    team_name="Manchester City",
    base_xg=2.3,  # Из understat
    base_xga=0.8,
    last_5_results=['W', 'W', 'D', 'W', 'W'],  # Из flashscore
    # ... остальные параметры
)

# 2. Корректируешь xG
adjuster = AdvancedAdjustments()
home_xg_adjusted = adjuster.adjust_xg(home_context)
away_xg_adjusted = adjuster.adjust_xg(away_context)

# 3. Используешь скорректированные значения в основной модели
from football_betting_model import FootballBettingModel

model = FootballBettingModel()
result = model.analyze_match(
    "Manchester City", "Arsenal",
    home_xg=home_xg_adjusted,  # Вместо базового xG
    away_xg=away_xg_adjusted,
    bookmaker_odds=odds
)

✅ Это значительно улучшит точность прогнозов!
    """)
    print("="*70 + "\n")
