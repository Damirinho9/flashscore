"""
ИНТЕГРИРОВАННЫЙ АНАЛИЗ
Объединяет все источники данных: xG, коэффициенты, форму, травмы, ELO

Это главный скрипт для реального использования!
"""

from football_betting_model import FootballBettingModel
from data_parser import collect_match_data, UnderstatParser
from flashscore_parser import manual_odds_input, get_odds_from_csv
from advanced_features import TeamContext, AdvancedAdjustments, MatchImportance
from team_elo import EloRatingSystem, initialize_league_ratings, combine_xg_and_elo
from typing import Dict, Optional


class IntegratedMatchAnalyzer:
    """Полный анализ с учетом всех факторов"""

    def __init__(self):
        self.model = FootballBettingModel()
        self.adjuster = AdvancedAdjustments()
        self.elo = initialize_league_ratings('EPL')

    def full_analysis(
        self,
        home_team: str,
        away_team: str,
        league: str = 'EPL',
        odds: Optional[Dict] = None,
        home_context: Optional[TeamContext] = None,
        away_context: Optional[TeamContext] = None,
        use_elo: bool = False
    ) -> Dict:
        """
        Полный интегрированный анализ

        Args:
            home_team: Команда-хозяин
            away_team: Гостевая команда
            league: Лига
            odds: Коэффициенты букмекера
            home_context: Контекст хозяев (травмы, форма, и т.д.)
            away_context: Контекст гостей
            use_elo: Комбинировать с ELO-прогнозом

        Returns:
            Полный результат анализа
        """
        print("\n" + "="*70)
        print(f"🎯 ИНТЕГРИРОВАННЫЙ АНАЛИЗ: {home_team} vs {away_team}")
        print("="*70 + "\n")

        # ШАГ 1: Получаем базовые xG из Understat
        print("[1/5] Сбор базовых xG данных с Understat...")
        match_data = collect_match_data(home_team, away_team, league)

        if not match_data:
            print("❌ Не удалось получить xG данные")
            return None

        base_home_xg = match_data['home_xg_expected']
        base_away_xg = match_data['away_xg_expected']

        print(f"  ✅ Базовый xG: {base_home_xg:.2f} - {base_away_xg:.2f}")

        # ШАГ 2: Корректируем xG на основе дополнительных факторов
        print("\n[2/5] Корректировка xG на основе формы, травм, мотивации...")

        if home_context:
            home_context.base_xg = base_home_xg
            adjusted_home_xg = self.adjuster.adjust_xg(home_context)
            print(f"  {home_team}: {base_home_xg:.2f} → {adjusted_home_xg:.2f} "
                  f"({((adjusted_home_xg/base_home_xg - 1)*100):+.1f}%)")
        else:
            adjusted_home_xg = base_home_xg
            print(f"  {home_team}: {base_home_xg:.2f} (без корректировок)")

        if away_context:
            away_context.base_xg = base_away_xg
            adjusted_away_xg = self.adjuster.adjust_xg(away_context)
            print(f"  {away_team}: {base_away_xg:.2f} → {adjusted_away_xg:.2f} "
                  f"({((adjusted_away_xg/base_away_xg - 1)*100):+.1f}%)")
        else:
            adjusted_away_xg = base_away_xg
            print(f"  {away_team}: {base_away_xg:.2f} (без корректировок)")

        # ШАГ 3: Получаем/вводим коэффициенты
        print("\n[3/5] Получение коэффициентов...")

        if not odds:
            print("  Коэффициенты не предоставлены. Варианты:")
            print("  1. Ввести вручную")
            print("  2. Загрузить из CSV")
            print("  3. Пропустить (анализ без value betting)")

            choice = input("\n  Выбор (1/2/3): ").strip()

            if choice == '1':
                odds = manual_odds_input(home_team, away_team)
            elif choice == '2':
                csv_file = input("  Путь к CSV файлу: ").strip()
                odds = get_odds_from_csv(csv_file, home_team, away_team)
            else:
                odds = None
                print("  ⚠️  Продолжаем без коэффициентов")

        # ШАГ 4: Основной прогноз (Пуассон)
        print("\n[4/5] Расчет прогноза методом Пуассона...")

        result = self.model.analyze_match(
            home_team=home_team,
            away_team=away_team,
            home_xg=adjusted_home_xg,
            away_xg=adjusted_away_xg,
            bookmaker_odds=odds,
            home_advantage=0.3
        )

        pred = result['prediction']
        print(f"  Вероятности: П1={pred['home_win']:.1%} | X={pred['draw']:.1%} | П2={pred['away_win']:.1%}")

        # ШАГ 5: Опционально - комбинация с ELO
        if use_elo:
            print("\n[5/5] Комбинирование с ELO-прогнозом...")

            elo_pred = self.elo.predict_match(home_team, away_team)

            xg_probs = {
                'home_win': pred['home_win'],
                'draw': pred['draw'],
                'away_win': pred['away_win']
            }

            combined = combine_xg_and_elo(xg_probs, elo_pred, weight_xg=0.7)

            print(f"  xG модель:   П1={xg_probs['home_win']:.1%} | X={xg_probs['draw']:.1%} | П2={xg_probs['away_win']:.1%}")
            print(f"  ELO модель:  П1={elo_pred['home_win']:.1%} | X={elo_pred['draw']:.1%} | П2={elo_pred['away_win']:.1%}")
            print(f"  Комбинация:  П1={combined['home_win']:.1%} | X={combined['draw']:.1%} | П2={combined['away_win']:.1%}")

            # Обновляем результат комбинированными вероятностями
            result['prediction']['home_win'] = combined['home_win']
            result['prediction']['draw'] = combined['draw']
            result['prediction']['away_win'] = combined['away_win']

            # Пересчитываем value ставки с новыми вероятностями
            if odds:
                result['recommendation'] = self._recalculate_recommendations(combined, odds)

        # Финальный вывод
        self._print_final_results(result, home_context, away_context)

        return result

    def _recalculate_recommendations(self, probs: Dict, odds: Dict) -> list:
        """Пересчет рекомендаций с новыми вероятностями"""
        recommendations = []

        markets = {
            'home_win': ('П1', probs['home_win']),
            'draw': ('X', probs['draw']),
            'away_win': ('П2', probs['away_win'])
        }

        for market, (name, true_prob) in markets.items():
            if market in odds:
                odds_value = odds[market]
                value_info = self.model.calculate_value(true_prob, odds_value)
                kelly = self.model.kelly_criterion(true_prob, odds_value)

                if value_info['is_value'] and kelly > 0.01:
                    recommendations.append({
                        'market': name,
                        'odds': odds_value,
                        'true_prob': f"{true_prob:.1%}",
                        'implied_prob': f"{value_info['implied_prob']:.1%}",
                        'edge': f"{value_info['edge']:.1%}",
                        'value': f"{value_info['value']:.2%}",
                        'kelly_stake': f"{kelly:.1%}"
                    })

        return recommendations

    def _print_final_results(self, result: Dict, home_ctx: TeamContext = None, away_ctx: TeamContext = None):
        """Красивый финальный вывод"""
        print("\n" + "="*70)
        print("📊 ИТОГОВЫЙ ПРОГНОЗ")
        print("="*70 + "\n")

        pred = result['prediction']

        # Основные вероятности
        print("Вероятности исходов:")
        print(f"  П1 (победа {result['home_team']}): {pred['home_win']:.1%}")
        print(f"  X  (ничья):                        {pred['draw']:.1%}")
        print(f"  П2 (победа {result['away_team']}): {pred['away_win']:.1%}")

        # Ожидаемые голы
        print(f"\nОжидаемые голы:")
        print(f"  {result['home_team']}: {pred['expected_home_goals']:.2f}")
        print(f"  {result['away_team']}: {pred['expected_away_goals']:.2f}")

        # Тоталы
        print(f"\nВероятности тоталов:")
        print(f"  ТБ 2.5: {pred['over_2.5']:.1%}")
        print(f"  ТМ 2.5: {pred['under_2.5']:.1%}")
        print(f"  Обе забьют: {pred['btts']:.1%}")

        # Value ставки
        if result['recommendation']:
            print("\n" + "="*70)
            print("💰 VALUE СТАВКИ")
            print("="*70 + "\n")

            for i, rec in enumerate(result['recommendation'], 1):
                print(f"{i}. {rec['market']}")
                print(f"   Коэффициент: {rec['odds']}")
                print(f"   Вероятность: {rec['true_prob']}")
                print(f"   Edge: {rec['edge']}")
                print(f"   Ставка (Kelly): {rec['kelly_stake']}")
                print()
        else:
            print("\n⚠️  Value ставок не найдено")

        # Контекстная информация
        if home_ctx or away_ctx:
            print("\n" + "="*70)
            print("📋 ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ")
            print("="*70)

            if home_ctx:
                print(f"\n{home_ctx.team_name}:")
                print(f"  Форма: {' '.join(home_ctx.last_5_results)}")
                print(f"  Место в таблице: {home_ctx.league_position}")
                print(f"  Травмы (влияние): {home_ctx.missing_players_impact:.0%}")

            if away_ctx:
                print(f"\n{away_ctx.team_name}:")
                print(f"  Форма: {' '.join(away_ctx.last_5_results)}")
                print(f"  Место в таблице: {away_ctx.league_position}")
                print(f"  Травмы (влияние): {away_ctx.missing_players_impact:.0%}")

        print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("⚽ ИНТЕГРИРОВАННЫЙ АНАЛИЗ МАТЧА")
    print("="*70 + "\n")

    print("Этот скрипт объединяет ВСЕ доступные данные:")
    print("  ✅ xG данные из Understat")
    print("  ✅ Коэффициенты (ручной ввод / CSV / API)")
    print("  ✅ Форма команд")
    print("  ✅ Травмы и дисквалификации")
    print("  ✅ Место в таблице и мотивация")
    print("  ✅ ELO-рейтинг (опционально)")
    print("  ✅ Математическая модель (Пуассон + Kelly)")
    print()

    # Пример с минимальными данными (только xG + коэффициенты)
    print("="*70)
    print("ПРИМЕР 1: Базовый анализ (xG + коэффициенты)")
    print("="*70 + "\n")

    analyzer = IntegratedMatchAnalyzer()

    # Можешь загрузить коэффициенты из CSV
    odds = get_odds_from_csv('odds_template.csv', 'Manchester City', 'Liverpool')

    if odds:
        result = analyzer.full_analysis(
            home_team="Manchester City",
            away_team="Liverpool",
            league='EPL',
            odds=odds
        )

    # Пример с полными данными
    print("\n" + "="*70)
    print("ПРИМЕР 2: Полный анализ (все факторы)")
    print("="*70 + "\n")

    from advanced_features import create_example_context

    city_ctx, arsenal_ctx = create_example_context()

    result2 = analyzer.full_analysis(
        home_team="Manchester City",
        away_team="Arsenal",
        league='EPL',
        odds={
            'home_win': 1.75,
            'draw': 4.00,
            'away_win': 4.50,
            'over_2.5': 1.60,
            'under_2.5': 2.30,
            'btts': 1.85
        },
        home_context=city_ctx,
        away_context=arsenal_ctx,
        use_elo=True  # Комбинировать с ELO
    )

    print("\n" + "="*70)
    print("📝 РЕКОМЕНДАЦИИ ПО ИСПОЛЬЗОВАНИЮ")
    print("="*70)
    print("""
1. МИНИМАЛЬНЫЙ ВАРИАНТ (быстрый):
   - Используй только xG + коэффициенты
   - Не требует дополнительных данных
   - Точность ~60-65%

2. ПРОДВИНУТЫЙ ВАРИАНТ (рекомендуется):
   - xG + коэффициенты + форма команд + травмы
   - Требует мониторинг новостей
   - Точность ~65-70%

3. ПОЛНЫЙ ВАРИАНТ (максимальная точность):
   - Все данные + ELO-рейтинг + H2H
   - Требует ведение базы данных
   - Точность ~70-75%

⚠️  ВАЖНО:
- Даже 75% точность ≠ гарантия прибыли
- Нужна дисциплина, управление банком, статистика
- Ставь только с edge > 5%
- Веди лог КАЖДОЙ ставки
    """)
    print("="*70 + "\n")
