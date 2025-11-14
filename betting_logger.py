"""
Генератор шаблона для логирования ставок
Используй для отслеживания результатов
"""

import pandas as pd
from datetime import datetime


def create_betting_log_template():
    """Создать CSV шаблон для ведения логов ставок"""
    
    # Примеры записей
    sample_data = {
        'Дата': [
            '2024-11-10',
            '2024-11-10',
            '2024-11-11'
        ],
        'Матч': [
            'Манчестер Сити - Арсенал',
            'Барселона - Реал Мадрид',
            'Бавария - Боруссия'
        ],
        'Лига': [
            'АПЛ',
            'Ла Лига',
            'Бундеслига'
        ],
        'Рынок': [
            'П1',
            'ТБ 2.5',
            'ОЗ'
        ],
        'Коэффициент': [
            1.75,
            1.60,
            1.85
        ],
        'Твоя_вероятность': [
            0.542,
            0.685,
            0.620
        ],
        'Edge_%': [
            -3.0,
            6.0,
            8.2
        ],
        'Размер_ставки_%': [
            0,
            3.2,
            2.8
        ],
        'Сумма_ставки': [
            0,
            3200,
            2800
        ],
        'Результат': [
            'Пропущена',
            'Выигрыш',
            'Ожидание'
        ],
        'Прибыль': [
            0,
            1920,
            None
        ],
        'Банк_после': [
            100000,
            104920,
            None
        ],
        'Комментарий': [
            'Нет value',
            'Отличный edge, Сити доминировали в xG',
            'Обе команды атакуют'
        ]
    }
    
    df = pd.DataFrame(sample_data)
    
    # Сохраняем шаблон
    filename = f'betting_log_{datetime.now().strftime("%Y%m%d")}.csv'
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    
    print(f"✅ Шаблон создан: {filename}")
    print("\nКак использовать:")
    print("1. Открой файл в Excel/Google Sheets")
    print("2. После каждой ставки добавляй новую строку")
    print("3. Заполняй все колонки честно")
    print("4. Раз в месяц анализируй статистику")
    
    return filename


def analyze_betting_log(csv_file):
    """Анализ твоих результатов из CSV лога"""
    
    df = pd.read_csv(csv_file, encoding='utf-8-sig')
    
    # Фильтруем завершенные ставки
    completed = df[df['Результат'].isin(['Выигрыш', 'Проигрыш'])].copy()
    
    if len(completed) == 0:
        print("Пока нет завершенных ставок для анализа")
        return
    
    total_bets = len(completed)
    wins = len(completed[completed['Результат'] == 'Выигрыш'])
    losses = len(completed[completed['Результат'] == 'Проигрыш'])
    
    total_staked = completed['Сумма_ставки'].sum()
    total_profit = completed['Прибыль'].sum()
    roi = (total_profit / total_staked) * 100 if total_staked > 0 else 0
    
    win_rate = (wins / total_bets) * 100
    avg_odds = completed['Коэффициент'].mean()
    
    print("\n" + "="*60)
    print("📊 АНАЛИЗ РЕЗУЛЬТАТОВ")
    print("="*60 + "\n")
    
    print(f"Всего ставок: {total_bets}")
    print(f"  Выигрышей: {wins} ({win_rate:.1f}%)")
    print(f"  Проигрышей: {losses} ({100-win_rate:.1f}%)")
    
    print(f"\nФинансовые показатели:")
    print(f"  Поставлено: {total_staked:,.0f} ₽")
    print(f"  Прибыль: {total_profit:,.0f} ₽")
    print(f"  ROI: {roi:.2f}%")
    
    print(f"\nСредний коэффициент: {avg_odds:.2f}")
    print(f"Средний edge: {completed['Edge_%'].mean():.1f}%")
    
    # Анализ по рынкам
    print("\n" + "-"*60)
    print("Статистика по рынкам:")
    print("-"*60)
    
    market_stats = completed.groupby('Рынок').agg({
        'Результат': lambda x: (x == 'Выигрыш').sum() / len(x) * 100,
        'Прибыль': 'sum',
        'Сумма_ставки': 'sum'
    }).round(2)
    
    market_stats.columns = ['Win_Rate_%', 'Profit', 'Staked']
    market_stats['ROI_%'] = (market_stats['Profit'] / market_stats['Staked'] * 100).round(2)
    
    print(market_stats)
    
    # Рекомендации
    print("\n" + "="*60)
    print("💡 РЕКОМЕНДАЦИИ")
    print("="*60 + "\n")
    
    if roi > 5:
        print("✅ Отличные результаты! Продолжай в том же духе.")
    elif roi > 0:
        print("✅ Положительный ROI - хорошо. Работай над увеличением edge.")
    elif roi > -5:
        print("⚠️  Небольшой минус. Пересмотри выбор матчей и размеры ставок.")
    else:
        print("❌ Большие потери. Остановись и проанализируй ошибки.")
    
    if win_rate < 50 and avg_odds < 2.0:
        print("\n⚠️  Винрейт низкий при небольших коэффициентах.")
        print("   Совет: Ставь только на матчи с edge > 5%")
    
    if completed['Размер_ставки_%'].max() > 5:
        print("\n⚠️  Есть ставки больше 5% банка - слишком рискованно!")
    
    print("\n" + "="*60 + "\n")


def calculate_bankroll_stats(initial_bank, current_bank, bets_count, days):
    """Расчет статистики по банкроллу"""
    
    profit = current_bank - initial_bank
    roi = (profit / initial_bank) * 100
    daily_return = roi / days if days > 0 else 0
    monthly_return = daily_return * 30
    
    print("\n" + "="*60)
    print("💰 СТАТИСТИКА БАНКРОЛЛА")
    print("="*60 + "\n")
    
    print(f"Начальный банк: {initial_bank:,.0f} ₽")
    print(f"Текущий банк: {current_bank:,.0f} ₽")
    print(f"Прибыль/убыток: {profit:,.0f} ₽ ({roi:+.2f}%)")
    
    print(f"\nКоличество ставок: {bets_count}")
    print(f"Дней в работе: {days}")
    print(f"Ставок в день: {bets_count/days:.1f}" if days > 0 else "0")
    
    print(f"\nДневная доходность: {daily_return:+.3f}%")
    print(f"Проекция месячной доходности: {monthly_return:+.2f}%")
    
    # Риск разорения (упрощенно)
    if roi > 0:
        risk = "Низкий" if roi > 10 else "Средний"
    else:
        risk = "Высокий"
    
    print(f"\nРиск разорения: {risk}")
    
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    
    print("\n🔧 ИНСТРУМЕНТЫ ДЛЯ ЛОГИРОВАНИЯ СТАВОК\n")
    
    # Создаем шаблон
    template_file = create_betting_log_template()
    
    print("\n" + "-"*60 + "\n")
    
    # Пример анализа (если у тебя уже есть лог)
    print("Для анализа существующего лога используй:")
    print("analyze_betting_log('твой_файл.csv')")
    
    print("\n" + "-"*60 + "\n")
    
    # Пример расчета статистики банкролла
    print("Пример статистики банкролла:\n")
    calculate_bankroll_stats(
        initial_bank=100000,
        current_bank=108500,
        bets_count=45,
        days=30
    )
    
    print("\n" + "="*60)
    print("📝 ВАЖНЫЕ ПРАВИЛА ЛОГИРОВАНИЯ")
    print("="*60)
    print("""
1. Записывай КАЖДУЮ ставку - без исключений
2. Будь честен с собой - не скрывай проигрыши
3. Анализируй каждые 50 ставок минимум
4. Ищи паттерны: какие рынки/лиги работают лучше
5. Если ROI отрицательный на 100+ ставках - меняй подход

Дисциплина в ведении логов важнее самой модели!
    """)
    print("="*60 + "\n")
