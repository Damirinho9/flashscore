# ⚽ Модель прогнозирования футбольных матчей на основе xG

Полноценная система для value betting: парсинг данных с understat → расчет вероятностей по Пуассону → поиск value ставок → оптимальный размер по Келли.

## 📦 Установка

```bash
pip install -r requirements.txt
```

## 🚀 Быстрый старт

### Вариант 1: Автоматический анализ с парсингом

```python
from main_analysis import analyze_upcoming_match

# Анализируем матч АПЛ
analyze_upcoming_match(
    home_team="Manchester City",
    away_team="Liverpool",
    league='EPL',
    bookmaker_odds={
        'home_win': 1.80,
        'draw': 4.20,
        'away_win': 4.00,
        'over_2.5': 1.65,
        'under_2.5': 2.20,
        'btts': 1.80
    }
)
```

### Вариант 2: Быстрый анализ (ручной ввод xG)

```python
from main_analysis import quick_manual_analysis

quick_manual_analysis(
    home_team="Барселона",
    away_team="Реал Мадрид",
    home_xg=2.1,  # Твоя оценка xG хозяев
    away_xg=1.6,  # Твоя оценка xG гостей
    odds={
        'home_win': 2.00,
        'draw': 3.50,
        'away_win': 3.60,
        'over_2.5': 1.55,
        'under_2.5': 2.45,
        'btts': 1.75
    }
)
```

## 📁 Структура проекта

### Основные модули
- **football_betting_model.py** - Основная модель (Пуассон, Kelly, value betting)
- **data_parser.py** - Парсер для understat.com (xG данные)
- **main_analysis.py** - Простой анализ одного матча
- **integrated_analysis.py** - 🌟 **ГЛАВНЫЙ СКРИПТ** - полный анализ со всеми факторами

### Парсеры и источники данных
- **flashscore_parser.py** - Парсер/интеграция с Flashscore (коэффициенты, форма)
- **advanced_features.py** - Учет травм, формы, мотивации, места в таблице

### Расширенные функции
- **batch_analyzer.py** - Batch-анализ нескольких матчей одновременно
- **team_elo.py** - Система ELO-рейтинга для команд
- **visualizer.py** - Генератор HTML-отчетов
- **betting_logger.py** - Инструменты для логирования ставок

### Файлы данных
- **odds_template.csv** - Шаблон для коэффициентов
- **team_cache.json** - Кэш xG данных (создается автоматически)

## 🎯 Возможности

### 1. Парсинг реальных данных
- Автоматический сбор xG с understat.com
- Статистика последних 10 матчей команды
- Кэширование на 24 часа (чтобы не спамить сайт)

### 2. Математическая модель
- **Распределение Пуассона** для расчета вероятностей счетов
- Учет домашнего преимущества (0.2-0.4 xG)
- Вероятности всех основных рынков: П1/X/П2, тоталы, обе забьют

### 3. Value betting
- Автоматический поиск value (когда твоя вероятность > букмекера)
- Расчет edge (преимущества)
- Критерий Келли для оптимального размера ставки

### 4. Batch-анализ (НОВОЕ!)
- Анализ нескольких матчей одновременно
- Автоматический поиск лучших value ставок из всех матчей
- Экспорт результатов в JSON для дальнейшего анализа

### 5. ELO-рейтинг (НОВОЕ!)
- Система ELO для оценки силы команд
- Комбинирование прогнозов xG + ELO для повышения точности
- Обновление рейтингов после каждого матча

### 6. HTML-отчеты (НОВОЕ!)
- Красивые визуальные отчеты без внешних библиотек
- Анализ betting log с графиками ROI и winrate
- Готовые отчеты для открытия в браузере

## 🔧 Доступные лиги

```python
leagues = {
    'EPL': 'epl',              # Англия
    'La_Liga': 'la_liga',      # Испания
    'Bundesliga': 'bundesliga', # Германия
    'Serie_A': 'serie_a',      # Италия
    'Ligue_1': 'ligue_1',      # Франция
    'RFPL': 'rfpl'             # Россия
}
```

## 📊 Пример вывода

```
==================================================================
🎯 ПРОГНОЗ МАТЧА
==================================================================

Ожидаемые голы (с учетом домашнего преимущества):
  Manchester City: 2.40 xG
  Arsenal: 1.40 xG

Вероятности исходов:
  П1 (победа Manchester City): 54.2%
  X  (ничья):                   23.1%
  П2 (победа Arsenal):          22.7%

  👑 Фаворит: Manchester City

==================================================================
💰 VALUE СТАВКИ - РЕКОМЕНДАЦИИ
==================================================================

1. Рынок: П1
   Коэффициент букмекера: 1.75
   Твоя оценка вероятности: 54.2%
   Вероятность букмекера: 57.1%
   ✅ Edge (твое преимущество): -3.0%
   💎 Value: -5.1%
   💵 Размер ставки: 0% (нет value)

2. Рынок: ТБ 2.5
   Коэффициент букмекера: 1.60
   Твоя оценка вероятности: 68.5%
   Вероятность букмекера: 62.5%
   ✅ Edge (твое преимущество): +6.0%
   💎 Value: +9.6%
   💵 Размер ставки: 3.2% от банка ✅
```

## ⚙️ Настройка параметров

### Изменить домашнее преимущество

```python
analyze_upcoming_match(
    ...,
    home_advantage=0.35  # По умолчанию 0.30
)
```

### Изменить консервативность Келли

В `football_betting_model.py`:

```python
def kelly_criterion(self, true_prob, odds, fraction=0.25):
    # fraction=0.25 → четверть Келли (консервативно)
    # fraction=0.50 → половина Келли (агрессивно)
    # fraction=1.00 → полный Келли (очень агрессивно)
```

### Добавить свои рынки

```python
bookmaker_odds = {
    'home_win': 1.80,
    'draw': 4.20,
    'away_win': 4.00,
    'over_2.5': 1.65,
    'under_2.5': 2.20,
    'btts': 1.80,
    # Можешь добавить свои:
    # 'over_1.5': 1.25,
    # 'under_3.5': 1.40,
}
```

## 🎓 Как собирать xG вручную (если парсер не работает)

### Источники данных:
1. **understat.com** - лучший источник xG
2. **fbref.com** - расширенная статистика
3. **footystats.org** - альтернатива

### Что смотреть:
- Средний xG команды дома/в гостях за последние 10 матчей
- xGA (пропущенные xG) - показывает качество обороны
- Форма команды (последние 5 игр)

### Пример:
```
Манчестер Сити (дома):
- Последние 10 матчей дома: xG = 2.3, xGA = 0.8
- Форма: 4W 1D 0L

Арсенал (в гостях):
- Последние 10 матчей в гостях: xG = 1.5, xGA = 1.2
- Форма: 3W 1D 1L

→ В модель подаешь: home_xg=2.3, away_xg=1.5
```

## 💡 Советы по использованию

### ✅ Делай так:
- Используй модель как фильтр - только матчи с edge > 3%
- Веди лог всех ставок в таблице (дата, матч, рынок, коэф, результат)
- Анализируй статистику каждые 50-100 ставок
- При серии из 5+ проигрышей - пауза и анализ

### ❌ Не делай так:
- Не ставь на каждый матч подряд
- Не увеличивай ставку после проигрыша
- Не игнорируй рекомендации по размеру ставки
- Не ставь на любимую команду без объективной оценки

## 📈 Реалистичные ожидания

- **ROI 3-5%** - отличный результат для долгосрочной дистанции
- **Выборка 500+ ставок** - минимум для оценки модели
- **Просадки 20-30%** - это нормально, не паникуй
- **95% беттеров** проигрывают - дисциплина важнее модели

## 🛠️ Расширение функционала

### Добавить новые факторы:
```python
def calculate_adjusted_xg(self, base_xg, injuries=0, motivation=1.0):
    """
    injuries: количество травмированных ключевых игроков
    motivation: коэффициент мотивации (0.8-1.2)
    """
    adjusted = base_xg
    adjusted -= injuries * 0.3  # -0.3 xG за каждого травмированного
    adjusted *= motivation
    return adjusted
```

### Анализ H2H (личные встречи):
```python
def get_h2h_adjustment(self, team1, team2):
    """Корректировка на основе личных встреч"""
    # Собери данные предыдущих матчей
    # Если одна команда регулярно обыгрывает другую
    # → добавь 0.1-0.2 к xG фаворита
    pass
```

## 🐛 Troubleshooting

### Ошибка "Команда не найдена"
- Проверь точное написание на understat.com
- Возможно команда называется иначе ("Man City" vs "Manchester City")

### Парсер не работает
- Используй ручной ввод xG (`quick_manual_analysis`)
- Проверь интернет-соединение
- Возможно understat изменил структуру сайта

### Нет value ставок
- Это нормально! Большинство матчей не имеют value
- Букмекеры тоже используют xG модели
- Ищи матчи где есть специфика (травмы, мотивация, etc)

## 📝 Лицензия

MIT - делай что хочешь, но на свой риск.

## 📊 Источники данных

### 1. xG данные - Understat.com
- Автоматический парсинг средних xG команд
- Статистика последних 10 матчей
- Кэширование на 24 часа

### 2. Коэффициенты - Flashscore / Букмекеры
**Варианты получения:**

#### A. Ручной ввод (рекомендуется для начала)
```python
from flashscore_parser import manual_odds_input

odds = manual_odds_input("Manchester City", "Liverpool")
```

#### B. CSV файл (для batch-анализа)
```python
from flashscore_parser import get_odds_from_csv

odds = get_odds_from_csv('odds_template.csv', 'Manchester City', 'Liverpool')
```

#### C. API (для автоматизации)
```python
from flashscore_parser import FlashscoreAPIClient

# API-Football: 100 запросов/день бесплатно
# Регистрация: https://www.api-football.com/

client = FlashscoreAPIClient(api_key='твой_ключ', provider='api-football')
odds = client.get_odds(fixture_id=12345)
```

### 3. Дополнительные факторы
- Форма команд (последние 5-10 матчей)
- Травмы и дисквалификации
- Место в таблице (мотивация)
- Дни отдыха (усталость)
- H2H статистика
- Эффект нового тренера

## 🌟 Полный анализ матча (РЕКОМЕНДУЕТСЯ)

```python
from integrated_analysis import IntegratedMatchAnalyzer
from advanced_features import TeamContext, MatchImportance
from flashscore_parser import get_odds_from_csv

# 1. Создаем анализатор
analyzer = IntegratedMatchAnalyzer()

# 2. Опционально: добавляем контекст команд
home_context = TeamContext(
    team_name="Manchester City",
    base_xg=2.3,  # Будет получен автоматически
    base_xga=0.8,
    last_5_results=['W', 'W', 'D', 'W', 'W'],  # Из Flashscore
    goals_scored_last_5=14,
    goals_conceded_last_5=3,
    league_position=2,
    points=45,
    goal_difference=28,
    key_players_missing=1,  # Травмированные ключевые игроки
    missing_players_impact=0.4,  # 0.0-1.0 влияние травм
    match_importance=MatchImportance.HIGH,
    rest_days=4
)

# 3. Полный анализ
result = analyzer.full_analysis(
    home_team="Manchester City",
    away_team="Liverpool",
    league='EPL',
    odds=get_odds_from_csv('odds.csv', 'Manchester City', 'Liverpool'),
    home_context=home_context,  # Опционально
    away_context=away_context,  # Опционально
    use_elo=True  # Комбинировать с ELO-рейтингом
)
```

## 🆕 Новые возможности

### Batch-анализ матчей

```python
from batch_analyzer import BatchAnalyzer

matches = [
    {
        'home_team': 'Manchester City',
        'away_team': 'Liverpool',
        'league': 'EPL',
        'odds': {'home_win': 1.85, 'draw': 4.00, 'away_win': 4.20, 'over_2.5': 1.60, 'btts': 1.75}
    },
    # ... добавь остальные матчи
]

analyzer = BatchAnalyzer()
df = analyzer.analyze_matches(matches)
analyzer.print_best_bets(min_edge=0.03)  # Показать ставки с edge > 3%
```

### ELO-рейтинг

```python
from team_elo import EloRatingSystem, initialize_league_ratings, combine_xg_and_elo

# Инициализация с базовыми рейтингами АПЛ
elo = initialize_league_ratings('EPL')

# Прогноз на основе ELO
elo_prediction = elo.predict_match("Arsenal", "Chelsea")

# Комбинируем с xG (70% xG + 30% ELO)
combined = combine_xg_and_elo(xg_prediction, elo_prediction, weight_xg=0.7)

# Обновляем рейтинг после матча (Арсенал 2:1 Челси)
elo.update_ratings("Arsenal", "Chelsea", 2, 1)
elo.save_ratings()  # Сохраняем для следующего использования
```

### HTML-отчеты

```python
from visualizer import HTMLReportGenerator, generate_betting_log_report

# Отчет по матчам
generator = HTMLReportGenerator()
filename = generator.generate_match_report(analyzer.results)
print(f"Отчет создан: {filename}")

# Отчет по betting log
generate_betting_log_report('betting_log_20241114.csv')
```

## ⚠️ Disclaimer

Это инструмент для образовательных целей и анализа данных. Беттинг несет финансовые риски. Ставь только те деньги, которые можешь потерять. Модель не гарантирует прибыль.

---

**Удачи на дистанции! 🍀**
