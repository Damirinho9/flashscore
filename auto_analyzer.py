"""
ПОЛНОСТЬЮ АВТОМАТИЧЕСКИЙ АНАЛИЗ
Объединяет API-Football + Understat + модель прогнозирования

Использование:
python auto_analyzer.py --api-key YOUR_KEY --home "Manchester City" --away "Liverpool"
"""

import sys
import argparse
from typing import Dict, Optional
from datetime import datetime

from api_football_client import APIFootballClient, full_match_data_collection, LEAGUE_IDS
from data_parser import UnderstatParser
from football_betting_model import FootballBettingModel
from advanced_features import TeamContext, MatchImportance, AdvancedAdjustments
from team_elo import initialize_league_ratings, combine_xg_and_elo


class FullyAutomatedAnalyzer:
    """
    Полностью автоматический анализатор

    Собирает данные из:
    - API-Football: коэффициенты, форма, травмы, H2H, таблица
    - Understat: детальные xG данные
    - ELO: рейтинги команд

    Выдает:
    - Прогноз с учетом всех факторов
    - Value ставки
    - Оптимальный размер ставки
    """

    def __init__(self, api_key: str):
        self.api_client = APIFootballClient(api_key)
        self.understat_parser = UnderstatParser()
        self.model = FootballBettingModel()
        self.adjuster = AdvancedAdjustments()
        self.elo = initialize_league_ratings('EPL')

    def analyze_match(
        self,
        home_team: str,
        away_team: str,
        league: str = 'EPL',
        use_elo: bool = True,
        use_api_xg: bool = False
    ) -> Dict:
        """
        Полный автоматический анализ матча

        Args:
            home_team: Команда-хозяин
            away_team: Гостевая команда
            league: Лига
            use_elo: Комбинировать с ELO
            use_api_xg: Использовать средние голы из API вместо xG из Understat

        Returns:
            Полный результат анализа
        """
        print("\n" + "="*70)
        print(f"🤖 АВТОМАТИЧЕСКИЙ АНАЛИЗ: {home_team} vs {away_team}")
        print("="*70 + "\n")

        # ШАГ 1: Собираем данные через API-Football
        print("📊 ШАГ 1: Сбор данных через API-Football...")
        print("-" * 70)

        api_data = full_match_data_collection(
            api_key=self.api_client.api_key,
            home_team=home_team,
            away_team=away_team,
            league=league
        )

        if not api_data:
            print("❌ Не удалось собрать данные через API")
            return None

        # ШАГ 2: Получаем xG из Understat (более точные данные)
        print("\n📊 ШАГ 2: Получение xG данных из Understat...")
        print("-" * 70)

        if use_api_xg:
            # Используем средние голы из API-Football
            home_xg = api_data['home_team']['stats']['avg_goals_for']
            away_xg = api_data['away_team']['stats']['avg_goals_for']
            print(f"  ✅ Используем данные API-Football")
            print(f"  {home_team}: {home_xg:.2f} avg goals")
            print(f"  {away_team}: {away_xg:.2f} avg goals")
        else:
            # Получаем xG из Understat (точнее)
            try:
                home_xg_data = self.understat_parser.parse_team_stats(home_team, league, last_n_games=10)
                away_xg_data = self.understat_parser.parse_team_stats(away_team, league, last_n_games=10)

                if home_xg_data and away_xg_data:
                    home_xg = home_xg_data['home_xg']
                    away_xg = away_xg_data['away_xg']
                    print(f"  ✅ xG из Understat:")
                    print(f"  {home_team}: {home_xg:.2f} xG (дома)")
                    print(f"  {away_team}: {away_xg:.2f} xG (в гостях)")
                else:
                    print("  ⚠️  Данные Understat недоступны, используем API-Football")
                    home_xg = api_data['home_team']['stats']['avg_goals_for']
                    away_xg = api_data['away_team']['stats']['avg_goals_for']
            except Exception as e:
                print(f"  ⚠️  Ошибка Understat: {e}, используем API-Football")
                home_xg = api_data['home_team']['stats']['avg_goals_for']
                away_xg = api_data['away_team']['stats']['avg_goals_for']

        # ШАГ 3: Создаем контекст команд
        print("\n📊 ШАГ 3: Создание контекста команд...")
        print("-" * 70)

        home_context = self._create_team_context(
            api_data['home_team'],
            home_xg,
            is_home=True
        )

        away_context = self._create_team_context(
            api_data['away_team'],
            away_xg,
            is_home=False
        )

        # ШАГ 4: Корректируем xG
        print("\n📊 ШАГ 4: Корректировка xG на основе формы, травм, мотивации...")
        print("-" * 70)

        adjusted_home_xg = self.adjuster.adjust_xg(home_context)
        adjusted_away_xg = self.adjuster.adjust_xg(away_context)

        print(f"  {home_team}:")
        print(f"    Базовый xG: {home_xg:.2f}")
        print(f"    Скорректированный: {adjusted_home_xg:.2f} ({((adjusted_home_xg/home_xg - 1)*100):+.1f}%)")
        print(f"  {away_team}:")
        print(f"    Базовый xG: {away_xg:.2f}")
        print(f"    Скорректированный: {adjusted_away_xg:.2f} ({((adjusted_away_xg/away_xg - 1)*100):+.1f}%)")

        # ШАГ 5: Прогноз (Пуассон)
        print("\n📊 ШАГ 5: Расчет прогноза методом Пуассона...")
        print("-" * 70)

        result = self.model.analyze_match(
            home_team=home_team,
            away_team=away_team,
            home_xg=adjusted_home_xg,
            away_xg=adjusted_away_xg,
            bookmaker_odds=api_data['odds'] if api_data['odds'] else None,
            home_advantage=0.3
        )

        pred = result['prediction']
        print(f"  Вероятности: П1={pred['home_win']:.1%} | X={pred['draw']:.1%} | П2={pred['away_win']:.1%}")
        print(f"  ТБ 2.5: {pred['over_2.5']:.1%} | ТМ 2.5: {pred['under_2.5']:.1%}")
        print(f"  Обе забьют: {pred['btts']:.1%}")

        # ШАГ 6: Опционально - комбинация с ELO
        if use_elo:
            print("\n📊 ШАГ 6: Комбинирование с ELO-прогнозом...")
            print("-" * 70)

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

            # Обновляем результат
            result['prediction']['home_win'] = combined['home_win']
            result['prediction']['draw'] = combined['draw']
            result['prediction']['away_win'] = combined['away_win']

            # Пересчитываем рекомендации
            if api_data['odds']:
                result['recommendation'] = self._recalculate_recommendations(
                    combined,
                    api_data['odds']
                )

        # Финальный вывод
        self._print_final_results(result, api_data, home_context, away_context)

        # Добавляем исходные данные
        result['api_data'] = api_data
        result['home_context'] = home_context
        result['away_context'] = away_context

        return result

    def _create_team_context(self, team_data: Dict, base_xg: float, is_home: bool) -> TeamContext:
        """Создать контекст команды из данных API"""
        stats = team_data['stats']
        form = team_data['form'] if team_data['form'] else ['D', 'D', 'D', 'D', 'D']

        # Оценка влияния травм (упрощенно)
        injuries = team_data['injuries']
        missing_impact = min(len(injuries) * 0.15, 0.6)  # Каждая травма = 15%, макс 60%

        # Оценка мотивации (можно улучшить, получив место в таблице)
        match_importance = MatchImportance.NORMAL

        # Подсчет голов за последние 5
        goals_scored = 0
        goals_conceded = 0
        if stats:
            avg_gf = stats['avg_goals_for']
            avg_ga = stats['avg_goals_against']
            goals_scored = int(avg_gf * 5)
            goals_conceded = int(avg_ga * 5)

        context = TeamContext(
            team_name=team_data['name'],
            base_xg=base_xg,
            base_xga=stats['avg_goals_against'] if stats else 1.0,
            last_5_results=form[:5],
            goals_scored_last_5=goals_scored,
            goals_conceded_last_5=goals_conceded,
            league_position=10,  # Можно получить из standings API
            points=stats['wins'] * 3 + stats['draws'] if stats else 0,
            goal_difference=stats['goals_for'] - stats['goals_against'] if stats else 0,
            key_players_missing=len(injuries),
            missing_players_impact=missing_impact,
            match_importance=match_importance,
            rest_days=4  # По умолчанию
        )

        return context

    def _recalculate_recommendations(self, probs: Dict, odds: Dict) -> list:
        """Пересчет рекомендаций"""
        recommendations = []

        markets = {
            'home_win': ('П1', probs['home_win'], odds.get('home_win')),
            'draw': ('X', probs['draw'], odds.get('draw')),
            'away_win': ('П2', probs['away_win'], odds.get('away_win'))
        }

        for market, (name, true_prob, odds_value) in markets.items():
            if odds_value:
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

    def _print_final_results(self, result: Dict, api_data: Dict, home_ctx: TeamContext, away_ctx: TeamContext):
        """Финальный вывод результатов"""
        print("\n" + "="*70)
        print("🎯 ИТОГОВЫЙ ПРОГНОЗ")
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

        # Дополнительная информация
        print("\n" + "="*70)
        print("📋 ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ")
        print("="*70)

        print(f"\n{home_ctx.team_name}:")
        print(f"  Форма: {' '.join(home_ctx.last_5_results)}")
        print(f"  Травмы: {home_ctx.key_players_missing} игроков (влияние: {home_ctx.missing_players_impact:.0%})")

        print(f"\n{away_ctx.team_name}:")
        print(f"  Форма: {' '.join(away_ctx.last_5_results)}")
        print(f"  Травмы: {away_ctx.key_players_missing} игроков (влияние: {away_ctx.missing_players_impact:.0%})")

        # H2H
        if api_data.get('h2h'):
            h2h = api_data['h2h']
            print(f"\nЛичные встречи (последние {len(h2h['results'])}):")
            print(f"  {home_ctx.team_name}: {' '.join(h2h['results'])}")
            print(f"  Побед {home_ctx.team_name}: {h2h['team1_wins']}")
            print(f"  Побед {away_ctx.team_name}: {h2h['team2_wins']}")
            print(f"  Ничьих: {h2h['draws']}")

        print("\n" + "="*70 + "\n")


def main():
    """CLI интерфейс"""
    parser = argparse.ArgumentParser(description='Автоматический анализ футбольных матчей')

    parser.add_argument('--api-key', required=True, help='API ключ от API-Football')
    parser.add_argument('--home', required=True, help='Команда-хозяин')
    parser.add_argument('--away', required=True, help='Гостевая команда')
    parser.add_argument('--league', default='EPL', choices=list(LEAGUE_IDS.keys()), help='Лига')
    parser.add_argument('--no-elo', action='store_true', help='Не использовать ELO')
    parser.add_argument('--use-api-xg', action='store_true', help='Использовать средние голы из API вместо xG')

    args = parser.parse_args()

    # Создаем анализатор
    analyzer = FullyAutomatedAnalyzer(args.api_key)

    # Анализируем
    result = analyzer.analyze_match(
        home_team=args.home,
        away_team=args.away,
        league=args.league,
        use_elo=not args.no_elo,
        use_api_xg=args.use_api_xg
    )

    if result:
        # Сохраняем результат
        import json
        filename = f"analysis_{args.home.replace(' ', '_')}_vs_{args.away.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            # Конвертируем TeamContext в dict для JSON
            result_copy = result.copy()
            if 'home_context' in result_copy:
                result_copy['home_context'] = result_copy['home_context'].__dict__
            if 'away_context' in result_copy:
                result_copy['away_context'] = result_copy['away_context'].__dict__
                # Конвертируем enum
                if 'match_importance' in result_copy['home_context']:
                    result_copy['home_context']['match_importance'] = result_copy['home_context']['match_importance'].name
                if 'match_importance' in result_copy['away_context']:
                    result_copy['away_context']['match_importance'] = result_copy['away_context']['match_importance'].name

            json.dump(result_copy, f, indent=2, ensure_ascii=False, default=str)

        print(f"💾 Результаты сохранены в {filename}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main()
    else:
        print("\n" + "="*70)
        print("⚽ ПОЛНОСТЬЮ АВТОМАТИЧЕСКИЙ АНАЛИЗАТОР")
        print("="*70 + "\n")

        print("📝 ИСПОЛЬЗОВАНИЕ:\n")

        print("python auto_analyzer.py \\")
        print("  --api-key YOUR_API_KEY \\")
        print("  --home \"Manchester City\" \\")
        print("  --away \"Liverpool\" \\")
        print("  --league EPL\n")

        print("Опции:")
        print("  --league EPL|La_Liga|Bundesliga|Serie_A|Ligue_1")
        print("  --no-elo           Не использовать ELO-рейтинг")
        print("  --use-api-xg       Использовать средние голы из API вместо xG\n")

        print("="*70)
        print("\n🚀 ПРИМЕР:\n")

        print("Получи бесплатный API ключ: https://www.api-football.com/")
        print("Затем запусти:\n")

        print("python auto_analyzer.py \\")
        print("  --api-key abc123xyz \\")
        print("  --home \"Arsenal\" \\")
        print("  --away \"Chelsea\" \\")
        print("  --league EPL\n")

        print("Система автоматически:")
        print("  ✅ Найдет предстоящий матч")
        print("  ✅ Получит актуальные коэффициенты")
        print("  ✅ Соберет форму команд, травмы, H2H")
        print("  ✅ Получит xG данные")
        print("  ✅ Скорректирует прогноз на основе всех факторов")
        print("  ✅ Найдет value ставки")
        print("  ✅ Рассчитает оптимальный размер ставки\n")

        print("="*70 + "\n")
