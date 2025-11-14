"""
Визуализация результатов анализа и статистики ставок
Генерирует HTML-отчеты с графиками
"""

import pandas as pd
import json
from datetime import datetime
from typing import List, Dict, Optional


class HTMLReportGenerator:
    """Генератор HTML-отчетов без внешних зависимостей"""

    def __init__(self):
        self.html_template = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Football Betting Analysis Report</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #f5f5f5;
            color: #333;
            padding: 20px;
            line-height: 1.6;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 32px;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }
        h2 {
            color: #34495e;
            margin-top: 30px;
            margin-bottom: 15px;
            font-size: 24px;
        }
        .meta {
            color: #7f8c8d;
            margin-bottom: 30px;
            font-size: 14px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .stat-card.green {
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        }
        .stat-card.red {
            background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
        }
        .stat-card.blue {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }
        .stat-label {
            font-size: 14px;
            opacity: 0.9;
            margin-bottom: 5px;
        }
        .stat-value {
            font-size: 32px;
            font-weight: bold;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
        }
        th {
            background: #34495e;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }
        td {
            padding: 12px;
            border-bottom: 1px solid #ecf0f1;
        }
        tr:hover {
            background: #f8f9fa;
        }
        .value-bet {
            background: #d4edda;
            color: #155724;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: bold;
        }
        .no-value {
            color: #999;
        }
        .prob-bar {
            height: 20px;
            background: #3498db;
            border-radius: 4px;
            display: inline-block;
            min-width: 20px;
        }
        .recommendation {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 15px 0;
            border-radius: 4px;
        }
        .match-card {
            background: #f8f9fa;
            padding: 15px;
            margin: 15px 0;
            border-radius: 8px;
            border-left: 4px solid #3498db;
        }
        .match-title {
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        }
        .prediction-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            margin: 10px 0;
        }
        .prediction-item {
            text-align: center;
            padding: 10px;
            background: white;
            border-radius: 4px;
        }
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ecf0f1;
            color: #7f8c8d;
            text-align: center;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        {CONTENT}
    </div>
</body>
</html>
        """

    def generate_match_report(self, match_results: List[Dict], filename: str = None) -> str:
        """
        Генерировать HTML-отчет по матчам

        Args:
            match_results: Список результатов из batch_analyzer
            filename: Имя файла для сохранения (опционально)
        """
        if not filename:
            filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

        # Генерируем контент
        content = self._generate_header()
        content += self._generate_summary_stats(match_results)
        content += self._generate_matches_section(match_results)
        content += self._generate_best_bets_section(match_results)
        content += self._generate_footer()

        # Вставляем в шаблон
        html = self.html_template.replace('{CONTENT}', content)

        # Сохраняем
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)

        return filename

    def _generate_header(self) -> str:
        return f"""
        <h1>⚽ Football Betting Analysis Report</h1>
        <div class="meta">
            Сгенерирован: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
        </div>
        """

    def _generate_summary_stats(self, results: List[Dict]) -> str:
        total_matches = len(results)
        total_value_bets = sum(len(r['value_bets']) for r in results)
        matches_with_value = sum(1 for r in results if r['value_bets'])

        avg_home_xg = sum(r['home_xg'] for r in results) / total_matches if total_matches > 0 else 0
        avg_away_xg = sum(r['away_xg'] for r in results) / total_matches if total_matches > 0 else 0

        return f"""
        <h2>📊 Общая статистика</h2>
        <div class="stats-grid">
            <div class="stat-card blue">
                <div class="stat-label">Всего матчей</div>
                <div class="stat-value">{total_matches}</div>
            </div>
            <div class="stat-card green">
                <div class="stat-label">Value ставок найдено</div>
                <div class="stat-value">{total_value_bets}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Матчи с value</div>
                <div class="stat-value">{matches_with_value}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Средний xG (дома/гости)</div>
                <div class="stat-value">{avg_home_xg:.2f} / {avg_away_xg:.2f}</div>
            </div>
        </div>
        """

    def _generate_matches_section(self, results: List[Dict]) -> str:
        html = '<h2>🎯 Анализ матчей</h2>'

        for r in results:
            html += f"""
            <div class="match-card">
                <div class="match-title">{r['home_team']} vs {r['away_team']} ({r['league']})</div>

                <div style="margin: 10px 0;">
                    <strong>Expected Goals:</strong> {r['adjusted_home_xg']:.2f} - {r['adjusted_away_xg']:.2f}
                </div>

                <div class="prediction-grid">
                    <div class="prediction-item">
                        <div style="color: #7f8c8d; font-size: 12px;">П1</div>
                        <div style="font-size: 20px; font-weight: bold; color: #2c3e50;">
                            {r['prob_home_win']:.1%}
                        </div>
                    </div>
                    <div class="prediction-item">
                        <div style="color: #7f8c8d; font-size: 12px;">X</div>
                        <div style="font-size: 20px; font-weight: bold; color: #2c3e50;">
                            {r['prob_draw']:.1%}
                        </div>
                    </div>
                    <div class="prediction-item">
                        <div style="color: #7f8c8d; font-size: 12px;">П2</div>
                        <div style="font-size: 20px; font-weight: bold; color: #2c3e50;">
                            {r['prob_away_win']:.1%}
                        </div>
                    </div>
                </div>

                <div style="margin-top: 10px;">
                    <strong>ТБ 2.5:</strong> {r['prob_over_2_5']:.1%} |
                    <strong>Обе забьют:</strong> {r['prob_btts']:.1%}
                </div>
            """

            if r['value_bets']:
                html += '<div style="margin-top: 15px; padding: 10px; background: #d4edda; border-radius: 4px;">'
                html += '<strong style="color: #155724;">💰 Value ставки:</strong><br>'
                for bet in r['value_bets']:
                    html += f'• {bet["market"]}: коэф {bet["odds"]}, edge {bet["edge"]}, ставка {bet["kelly_stake"]}<br>'
                html += '</div>'
            else:
                html += '<div style="margin-top: 10px; color: #999;">⚠️ Value не найдено</div>'

            html += '</div>'

        return html

    def _generate_best_bets_section(self, results: List[Dict]) -> str:
        # Собираем все value ставки
        all_bets = []
        for r in results:
            for bet in r['value_bets']:
                edge_value = float(bet['edge'].rstrip('%')) / 100
                all_bets.append({
                    'match': f"{r['home_team']} - {r['away_team']}",
                    'league': r['league'],
                    'market': bet['market'],
                    'odds': bet['odds'],
                    'edge': edge_value,
                    'kelly': bet['kelly_stake'],
                    'prob': bet['true_prob']
                })

        # Сортируем по edge
        all_bets.sort(key=lambda x: x['edge'], reverse=True)

        html = '<h2>🏆 Лучшие value ставки</h2>'

        if not all_bets:
            html += '<p style="color: #999;">Value ставок не найдено</p>'
            return html

        html += '<table><thead><tr>'
        html += '<th>№</th><th>Матч</th><th>Лига</th><th>Рынок</th><th>Коэф</th><th>Вероятность</th><th>Edge</th><th>Ставка</th>'
        html += '</tr></thead><tbody>'

        for i, bet in enumerate(all_bets[:20], 1):  # Топ-20
            html += f"""
            <tr>
                <td>{i}</td>
                <td>{bet['match']}</td>
                <td>{bet['league']}</td>
                <td><strong>{bet['market']}</strong></td>
                <td>{bet['odds']}</td>
                <td>{bet['prob']}</td>
                <td><span class="value-bet">{bet['edge']:.2%}</span></td>
                <td>{bet['kelly']}</td>
            </tr>
            """

        html += '</tbody></table>'

        return html

    def _generate_footer(self) -> str:
        return """
        <div class="footer">
            <p>⚠️ Disclaimer: Этот отчет создан для образовательных целей. Беттинг несет финансовые риски.</p>
            <p>Ставь только те деньги, которые можешь потерять.</p>
        </div>
        """


def generate_betting_log_report(csv_file: str, output_file: str = None) -> str:
    """
    Генерировать HTML-отчет по логу ставок

    Args:
        csv_file: Путь к CSV файлу с логом
        output_file: Имя выходного файла
    """
    if not output_file:
        output_file = f"betting_log_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"

    # Читаем данные
    df = pd.read_csv(csv_file, encoding='utf-8-sig')

    # Фильтруем завершенные ставки
    completed = df[df['Результат'].isin(['Выигрыш', 'Проигрыш'])].copy()

    if len(completed) == 0:
        print("Нет завершенных ставок для отчета")
        return None

    # Подсчитываем статистику
    total_bets = len(completed)
    wins = len(completed[completed['Результат'] == 'Выигрыш'])
    losses = total_bets - wins
    win_rate = (wins / total_bets) * 100

    total_staked = completed['Сумма_ставки'].sum()
    total_profit = completed['Прибыль'].sum()
    roi = (total_profit / total_staked) * 100 if total_staked > 0 else 0

    # Генерируем HTML
    html = f"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Betting Log Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }}
        .stat-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; }}
        .stat-card.green {{ background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }}
        .stat-card.red {{ background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%); }}
        .stat-label {{ font-size: 14px; opacity: 0.9; }}
        .stat-value {{ font-size: 28px; font-weight: bold; margin-top: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th {{ background: #34495e; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #ecf0f1; }}
        tr:hover {{ background: #f8f9fa; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Betting Log Report</h1>
        <p style="color: #7f8c8d;">Сгенерирован: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</p>

        <h2>Общая статистика</h2>
        <div class="stats">
            <div class="stat-card">
                <div class="stat-label">Всего ставок</div>
                <div class="stat-value">{total_bets}</div>
            </div>
            <div class="stat-card green">
                <div class="stat-label">Выигрышей</div>
                <div class="stat-value">{wins} ({win_rate:.1f}%)</div>
            </div>
            <div class="stat-card red">
                <div class="stat-label">Проигрышей</div>
                <div class="stat-value">{losses} ({100-win_rate:.1f}%)</div>
            </div>
            <div class="stat-card {'green' if roi > 0 else 'red'}">
                <div class="stat-label">ROI</div>
                <div class="stat-value">{roi:+.2f}%</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Поставлено</div>
                <div class="stat-value">{total_staked:,.0f} ₽</div>
            </div>
            <div class="stat-card {'green' if total_profit > 0 else 'red'}">
                <div class="stat-label">Прибыль</div>
                <div class="stat-value">{total_profit:+,.0f} ₽</div>
            </div>
        </div>

        <h2>Последние ставки</h2>
        <table>
            <thead>
                <tr><th>Дата</th><th>Матч</th><th>Рынок</th><th>Коэф</th><th>Ставка</th><th>Результат</th><th>Прибыль</th></tr>
            </thead>
            <tbody>
    """

    for _, row in completed.tail(20).iterrows():
        profit_color = 'green' if row['Прибыль'] > 0 else 'red'
        html += f"""
                <tr>
                    <td>{row['Дата']}</td>
                    <td>{row['Матч']}</td>
                    <td>{row['Рынок']}</td>
                    <td>{row['Коэффициент']}</td>
                    <td>{row['Сумма_ставки']:,.0f} ₽</td>
                    <td>{row['Результат']}</td>
                    <td style="color: {profit_color}; font-weight: bold;">{row['Прибыль']:+,.0f} ₽</td>
                </tr>
        """

    html += """
            </tbody>
        </table>
    </div>
</body>
</html>
    """

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✅ Отчет сохранен: {output_file}")
    return output_file


if __name__ == "__main__":
    print("\n📊 VISUALIZER - Генератор HTML-отчетов\n")

    # Пример: генерация отчета по матчам
    print("Пример 1: Генерация отчета по batch-анализу")
    print("-" * 70)
    print("""
Используй после batch_analyzer:

from batch_analyzer import BatchAnalyzer
from visualizer import HTMLReportGenerator

analyzer = BatchAnalyzer()
analyzer.analyze_matches(matches)

# Генерируем HTML-отчет
generator = HTMLReportGenerator()
filename = generator.generate_match_report(analyzer.results)
print(f"Отчет создан: {filename}")
    """)

    print("\n" + "="*70)
    print("Пример 2: Отчет по логу ставок")
    print("-" * 70)
    print("""
generate_betting_log_report('betting_log_20241114.csv')
    """)

    print("\n" + "="*70)
    print("💡 ВОЗМОЖНОСТИ")
    print("="*70)
    print("""
✅ HTML-отчеты без внешних библиотек (чистый HTML/CSS)
✅ Красивый адаптивный дизайн
✅ Статистика по матчам и ставкам
✅ Топ value ставок с сортировкой
✅ Анализ betting log с ROI и winrate
✅ Готово для открытия в любом браузере

📝 Отчеты сохраняются в текущей директории с timestamp
    """)
    print("="*70 + "\n")
