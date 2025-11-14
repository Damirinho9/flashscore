"""
Batch-анализ нескольких матчей одновременно
Позволяет анализировать все матчи тура/недели за один запуск
"""

import json
from datetime import datetime
from typing import List, Dict, Optional
from football_betting_model import FootballBettingModel
from data_parser import collect_match_data
import pandas as pd


class BatchAnalyzer:
    def __init__(self):
        self.model = FootballBettingModel()
        self.results = []

    def analyze_matches(self, matches: List[Dict], save_results=True) -> pd.DataFrame:
        """
        Анализ списка матчей

        Args:
            matches: Список словарей с данными матчей
                [{
                    'home_team': 'Team A',
                    'away_team': 'Team B',
                    'league': 'EPL',
                    'odds': {...}
                }, ...]
            save_results: Сохранить результаты в JSON

        Returns:
            DataFrame с результатами всех матчей
        """
        print("\n" + "="*70)
        print(f"📊 BATCH АНАЛИЗ: {len(matches)} матчей")
        print("="*70 + "\n")

        for i, match in enumerate(matches, 1):
            print(f"\n[{i}/{len(matches)}] {match['home_team']} vs {match['away_team']}")
            print("-" * 70)

            try:
                # Собираем данные
                match_data = collect_match_data(
                    match['home_team'],
                    match['away_team'],
                    match.get('league', 'EPL')
                )

                if not match_data:
                    print(f"❌ Не удалось получить данные")
                    continue

                # Анализируем
                result = self.model.analyze_match(
                    home_team=match['home_team'],
                    away_team=match['away_team'],
                    home_xg=match_data['home_xg_expected'],
                    away_xg=match_data['away_xg_expected'],
                    bookmaker_odds=match.get('odds'),
                    home_advantage=match.get('home_advantage', 0.3)
                )

                # Сохраняем результат
                match_result = self._format_result(match, result, match_data)
                self.results.append(match_result)

                # Краткий вывод
                pred = result['prediction']
                print(f"  xG: {pred['expected_home_goals']:.2f} - {pred['expected_away_goals']:.2f}")
                print(f"  Вероятности: П1={pred['home_win']:.1%} | X={pred['draw']:.1%} | П2={pred['away_win']:.1%}")

                if result['recommendation']:
                    print(f"  💰 Найдено {len(result['recommendation'])} value ставок!")
                    for rec in result['recommendation']:
                        print(f"     • {rec['market']}: коэф {rec['odds']}, edge {rec['edge']}, ставка {rec['kelly_stake']}")
                else:
                    print(f"  ⚠️  Value не найдено")

            except Exception as e:
                print(f"❌ Ошибка анализа: {e}")
                continue

        # Создаем DataFrame с результатами
        df = self._create_summary_dataframe()

        # Сохраняем результаты
        if save_results:
            self._save_results()

        print("\n" + "="*70)
        print("✅ АНАЛИЗ ЗАВЕРШЕН")
        print("="*70 + "\n")

        return df

    def _format_result(self, match: Dict, result: Dict, match_data: Dict) -> Dict:
        """Форматирование результата для сохранения"""
        pred = result['prediction']

        return {
            'timestamp': datetime.now().isoformat(),
            'home_team': match['home_team'],
            'away_team': match['away_team'],
            'league': match.get('league', 'EPL'),
            'home_xg': match_data['home_xg_expected'],
            'away_xg': match_data['away_xg_expected'],
            'adjusted_home_xg': pred['expected_home_goals'],
            'adjusted_away_xg': pred['expected_away_goals'],
            'prob_home_win': pred['home_win'],
            'prob_draw': pred['draw'],
            'prob_away_win': pred['away_win'],
            'prob_over_2_5': pred['over_2.5'],
            'prob_btts': pred['btts'],
            'value_bets': result['recommendation'],
            'bookmaker_odds': match.get('odds', {})
        }

    def _create_summary_dataframe(self) -> pd.DataFrame:
        """Создать сводную таблицу результатов"""
        if not self.results:
            return pd.DataFrame()

        rows = []
        for r in self.results:
            row = {
                'Матч': f"{r['home_team']} - {r['away_team']}",
                'Лига': r['league'],
                'xG': f"{r['home_xg']:.2f} - {r['away_xg']:.2f}",
                'П1': f"{r['prob_home_win']:.1%}",
                'X': f"{r['prob_draw']:.1%}",
                'П2': f"{r['prob_away_win']:.1%}",
                'ТБ2.5': f"{r['prob_over_2_5']:.1%}",
                'Value ставок': len(r['value_bets'])
            }
            rows.append(row)

        return pd.DataFrame(rows)

    def _save_results(self):
        """Сохранить результаты в JSON"""
        filename = f"batch_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)

        print(f"\n💾 Результаты сохранены: {filename}")

    def get_best_bets(self, min_edge: float = 0.05) -> List[Dict]:
        """
        Получить лучшие ставки из всех проанализированных матчей

        Args:
            min_edge: Минимальное преимущество (по умолчанию 5%)

        Returns:
            Список лучших ставок, отсортированных по edge
        """
        all_bets = []

        for result in self.results:
            for bet in result['value_bets']:
                # Парсим edge из строки "5.0%" в число
                edge_value = float(bet['edge'].rstrip('%')) / 100

                if edge_value >= min_edge:
                    all_bets.append({
                        'match': f"{result['home_team']} - {result['away_team']}",
                        'league': result['league'],
                        'market': bet['market'],
                        'odds': bet['odds'],
                        'edge': edge_value,
                        'kelly_stake': bet['kelly_stake'],
                        'true_prob': bet['true_prob']
                    })

        # Сортируем по edge (убыванию)
        all_bets.sort(key=lambda x: x['edge'], reverse=True)

        return all_bets

    def print_best_bets(self, min_edge: float = 0.05, top_n: int = 10):
        """Красивый вывод лучших ставок"""
        best_bets = self.get_best_bets(min_edge)

        if not best_bets:
            print(f"\n⚠️  Нет ставок с edge >= {min_edge:.1%}")
            return

        print("\n" + "="*70)
        print(f"🏆 ТОП-{min(top_n, len(best_bets))} ЛУЧШИХ VALUE СТАВОК")
        print("="*70 + "\n")

        for i, bet in enumerate(best_bets[:top_n], 1):
            print(f"{i}. {bet['match']} ({bet['league']})")
            print(f"   Рынок: {bet['market']}")
            print(f"   Коэффициент: {bet['odds']}")
            print(f"   Твоя вероятность: {bet['true_prob']}")
            print(f"   💎 Edge: {bet['edge']:.2%}")
            print(f"   💵 Размер ставки: {bet['kelly_stake']}")
            print()


def example_batch_analysis():
    """Пример использования batch-анализа"""

    # Список матчей для анализа
    matches = [
        {
            'home_team': 'Manchester City',
            'away_team': 'Liverpool',
            'league': 'EPL',
            'odds': {
                'home_win': 1.85,
                'draw': 4.00,
                'away_win': 4.20,
                'over_2.5': 1.60,
                'under_2.5': 2.30,
                'btts': 1.75
            }
        },
        {
            'home_team': 'Arsenal',
            'away_team': 'Chelsea',
            'league': 'EPL',
            'odds': {
                'home_win': 2.10,
                'draw': 3.60,
                'away_win': 3.40,
                'over_2.5': 1.70,
                'under_2.5': 2.15,
                'btts': 1.80
            }
        },
        {
            'home_team': 'Tottenham',
            'away_team': 'Manchester United',
            'league': 'EPL',
            'odds': {
                'home_win': 2.20,
                'draw': 3.50,
                'away_win': 3.30,
                'over_2.5': 1.75,
                'under_2.5': 2.10,
                'btts': 1.70
            }
        }
    ]

    # Создаем анализатор
    analyzer = BatchAnalyzer()

    # Анализируем все матчи
    df = analyzer.analyze_matches(matches)

    # Выводим сводку
    print("\n" + "="*70)
    print("📋 СВОДНАЯ ТАБЛИЦА")
    print("="*70 + "\n")
    print(df.to_string(index=False))

    # Выводим лучшие ставки
    analyzer.print_best_bets(min_edge=0.03, top_n=5)


def analyze_premier_league_round():
    """
    Пример: Анализ целого тура АПЛ
    Замени команды на актуальные из предстоящего тура
    """
    matches = [
        {
            'home_team': 'Aston Villa',
            'away_team': 'Brighton',
            'league': 'EPL',
            'odds': {'home_win': 2.35, 'draw': 3.50, 'away_win': 3.00, 'over_2.5': 1.80, 'btts': 1.75}
        },
        {
            'home_team': 'Bournemouth',
            'away_team': 'Nottingham Forest',
            'league': 'EPL',
            'odds': {'home_win': 2.20, 'draw': 3.40, 'away_win': 3.30, 'over_2.5': 1.85, 'btts': 1.80}
        },
        # Добавь остальные матчи тура...
    ]

    analyzer = BatchAnalyzer()
    df = analyzer.analyze_matches(matches)

    print(df.to_string(index=False))
    analyzer.print_best_bets(min_edge=0.04, top_n=10)


if __name__ == "__main__":
    print("\n🚀 BATCH ANALYZER - Анализ нескольких матчей одновременно\n")

    # Запускаем пример
    example_batch_analysis()

    print("\n" + "="*70)
    print("📝 КАК ИСПОЛЬЗОВАТЬ")
    print("="*70)
    print("""
1. Создай список матчей с коэффициентами:
   matches = [{'home_team': 'A', 'away_team': 'B', 'league': 'EPL', 'odds': {...}}, ...]

2. Запусти анализ:
   analyzer = BatchAnalyzer()
   df = analyzer.analyze_matches(matches)

3. Получи лучшие ставки:
   analyzer.print_best_bets(min_edge=0.05)

4. Результаты автоматически сохраняются в JSON файл
   для последующего анализа и ведения статистики

💡 СОВЕТ: Используй batch-анализ для:
   - Анализа целого тура лиги
   - Поиска лучших матчей недели
   - Сравнения букмекеров (разные odds для одних матчей)
   - Автоматизации ежедневного скрининга матчей
    """)
    print("="*70 + "\n")
