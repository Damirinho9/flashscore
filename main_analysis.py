"""
ГЛАВНЫЙ СКРИПТ - Полный цикл анализа матча
Парсинг данных → Прогноз → Value betting
"""

from football_betting_model import FootballBettingModel
from data_parser import collect_match_data, UnderstatParser, DataCache
import sys


def analyze_upcoming_match(home_team, away_team, league='EPL', 
                          bookmaker_odds=None, home_advantage=0.3):
    """
    Полный анализ предстоящего матча
    
    Args:
        home_team: Название команды-хозяина
        away_team: Название гостевой команды
        league: Лига (EPL, La_Liga, Bundesliga, Serie_A, Ligue_1, RFPL)
        bookmaker_odds: Словарь с коэффициентами букмекера
        home_advantage: Преимущество дома в xG (0.2-0.4)
    """
    
    print("\n" + "="*70)
    print(f"АНАЛИЗ МАТЧА: {home_team} vs {away_team}")
    print("="*70 + "\n")
    
    # Шаг 1: Собираем данные
    print("[1/3] Сбор статистики команд...")
    match_data = collect_match_data(home_team, away_team, league)
    
    if not match_data:
        print("\n❌ Не удалось собрать данные. Проверь названия команд.")
        print("\nДоступные лиги:")
        print("  - EPL (Англия)")
        print("  - La_Liga (Испания)")
        print("  - Bundesliga (Германия)")
        print("  - Serie_A (Италия)")
        print("  - Ligue_1 (Франция)")
        print("  - RFPL (Россия)")
        return None
    
    # Шаг 2: Прогнозируем
    print("\n[2/3] Расчет прогноза на основе xG...")
    
    model = FootballBettingModel()
    result = model.analyze_match(
        home_team=home_team,
        away_team=away_team,
        home_xg=match_data['home_xg_expected'],
        away_xg=match_data['away_xg_expected'],
        bookmaker_odds=bookmaker_odds,
        home_advantage=home_advantage
    )
    
    # Шаг 3: Выводим результаты
    print("\n[3/3] Результаты анализа:")
    print_results(result, match_data)
    
    return result


def print_results(result, match_data):
    """Красивый вывод результатов"""
    pred = result['prediction']
    
    print("\n" + "="*70)
    print("📊 СТАТИСТИКА КОМАНД (последние 10 матчей)")
    print("="*70)
    
    home_stats = match_data['home']
    away_stats = match_data['away']
    
    print(f"\n🏠 {result['home_team']}:")
    print(f"   xG дома: {home_stats['home_xg']:.2f}")
    print(f"   xGA дома: {home_stats['home_xga']:.2f}")
    print(f"   Общий xG: {home_stats['overall_xg']:.2f}")
    
    print(f"\n✈️  {result['away_team']}:")
    print(f"   xG в гостях: {away_stats['away_xg']:.2f}")
    print(f"   xGA в гостях: {away_stats['away_xga']:.2f}")
    print(f"   Общий xG: {away_stats['overall_xg']:.2f}")
    
    print("\n" + "="*70)
    print("🎯 ПРОГНОЗ МАТЧА")
    print("="*70)
    
    print(f"\nОжидаемые голы (с учетом домашнего преимущества):")
    print(f"  {result['home_team']}: {pred['expected_home_goals']:.2f} xG")
    print(f"  {result['away_team']}: {pred['expected_away_goals']:.2f} xG")
    
    print(f"\nВероятности исходов:")
    print(f"  П1 (победа {result['home_team']}): {pred['home_win']:.1%}")
    print(f"  X  (ничья):                        {pred['draw']:.1%}")
    print(f"  П2 (победа {result['away_team']}): {pred['away_win']:.1%}")
    
    # Определяем фаворита
    if pred['home_win'] > pred['away_win'] and pred['home_win'] > pred['draw']:
        print(f"\n  👑 Фаворит: {result['home_team']}")
    elif pred['away_win'] > pred['home_win'] and pred['away_win'] > pred['draw']:
        print(f"\n  👑 Фаворит: {result['away_team']}")
    else:
        print(f"\n  ⚖️  Равные шансы")
    
    print(f"\nВероятности тоталов:")
    print(f"  ТБ 2.5: {pred['over_2.5']:.1%}")
    print(f"  ТМ 2.5: {pred['under_2.5']:.1%}")
    print(f"  ТБ 1.5: {pred['over_1.5']:.1%}")
    print(f"  Обе забьют (BTTS): {pred['btts']:.1%}")
    
    # Value ставки
    if result['recommendation']:
        print("\n" + "="*70)
        print("💰 VALUE СТАВКИ - РЕКОМЕНДАЦИИ")
        print("="*70 + "\n")
        
        for i, rec in enumerate(result['recommendation'], 1):
            print(f"{i}. Рынок: {rec['market']}")
            print(f"   Коэффициент букмекера: {rec['odds']}")
            print(f"   Твоя оценка вероятности: {rec['true_prob']}")
            print(f"   Вероятность букмекера: {rec['implied_prob']}")
            print(f"   ✅ Edge (твое преимущество): {rec['edge']}")
            print(f"   💎 Value: {rec['value']}")
            print(f"   💵 Размер ставки (Kelly 25%): {rec['kelly_stake']} от банка")
            print()
    else:
        print("\n" + "="*70)
        print("⚠️  VALUE СТАВОК НЕ НАЙДЕНО")
        print("="*70)
        print("\nВсе коэффициенты букмекера близки к справедливым.")
        print("Рекомендация: пропустить этот матч или ставить минимально.")
    
    print("\n" + "="*70 + "\n")


def quick_manual_analysis(home_team, away_team, home_xg, away_xg, odds):
    """
    Быстрый анализ без парсинга - вводишь xG вручную
    """
    model = FootballBettingModel()
    
    result = model.analyze_match(
        home_team=home_team,
        away_team=away_team,
        home_xg=home_xg,
        away_xg=away_xg,
        bookmaker_odds=odds
    )
    
    pred = result['prediction']
    
    print("\n" + "="*70)
    print(f"БЫСТРЫЙ АНАЛИЗ: {home_team} vs {away_team}")
    print("="*70 + "\n")
    
    print(f"Вероятности: П1={pred['home_win']:.1%} | X={pred['draw']:.1%} | П2={pred['away_win']:.1%}")
    print(f"Тоталы: ТБ2.5={pred['over_2.5']:.1%} | ТМ2.5={pred['under_2.5']:.1%} | ОЗ={pred['btts']:.1%}")
    
    if result['recommendation']:
        print(f"\n✅ Найдено {len(result['recommendation'])} value ставок:")
        for rec in result['recommendation']:
            print(f"   • {rec['market']}: коэф {rec['odds']}, edge {rec['edge']}, ставка {rec['kelly_stake']}")
    else:
        print("\n⚠️  Value не найдено")
    
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    
    # ============================================
    # ПРИМЕР 1: Полный анализ с парсингом данных
    # ============================================
    
    print("\n🔥 ПРИМЕР 1: АВТОМАТИЧЕСКИЙ АНАЛИЗ С ПАРСИНГОМ")
    
    # Важно: названия должны точно соответствовать understat
    # Проверяй на сайте https://understat.com/league/epl
    
    analyze_upcoming_match(
        home_team="Manchester City",
        away_team="Arsenal",
        league='EPL',
        bookmaker_odds={
            'home_win': 1.75,
            'draw': 4.00,
            'away_win': 4.50,
            'over_2.5': 1.60,
            'under_2.5': 2.30,
            'btts': 1.85
        },
        home_advantage=0.30  # Стандартное преимущество дома
    )
    
    print("\n\n")
    
    # ============================================
    # ПРИМЕР 2: Быстрый анализ с ручным вводом xG
    # ============================================
    
    print("\n🔥 ПРИМЕР 2: БЫСТРЫЙ АНАЛИЗ (РУЧНОЙ ВВОД)")
    print("Если не можешь спарсить данные - вводишь xG вручную\n")
    
    quick_manual_analysis(
        home_team="Барселона",
        away_team="Реал Мадрид",
        home_xg=2.3,  # Средний xG Барсы дома
        away_xg=1.8,  # Средний xG Реала в гостях
        odds={
            'home_win': 2.10,
            'draw': 3.60,
            'away_win': 3.40,
            'over_2.5': 1.50,
            'under_2.5': 2.60,
            'btts': 1.70
        }
    )
    
    # ============================================
    # ПРИМЕР 3: Низкорезультативный матч
    # ============================================
    
    print("\n🔥 ПРИМЕР 3: ОБОРОНИТЕЛЬНЫЙ МАТЧ")
    
    quick_manual_analysis(
        home_team="Атлетико",
        away_team="Интер",
        home_xg=1.2,
        away_xg=1.0,
        odds={
            'home_win': 2.30,
            'draw': 3.20,
            'away_win': 3.30,
            'over_2.5': 2.20,
            'under_2.5': 1.70,
            'btts': 1.95
        }
    )
    
    print("\n" + "="*70)
    print("📝 КАК ИСПОЛЬЗОВАТЬ:")
    print("="*70)
    print("""
1. Автоматический анализ (с парсингом):
   analyze_upcoming_match("Команда 1", "Команда 2", "EPL", odds)
   
2. Ручной анализ (быстрый):
   quick_manual_analysis("Команда 1", "Команда 2", xG1, xG2, odds)
   
3. Адаптируй под себя:
   - Измени home_advantage (обычно 0.2-0.4)
   - Измени kelly_fraction (по умолчанию 0.25 = четверть Келли)
   - Добавь свои рынки в bookmaker_odds
   
4. Правила использования:
   - Ставь только когда edge > 3%
   - Максимум 5% банка на одну ставку
   - Ведь лог всех ставок в Excel/Google Sheets
   - Анализируй результаты каждый месяц
    """)
    
    print("="*70 + "\n")
