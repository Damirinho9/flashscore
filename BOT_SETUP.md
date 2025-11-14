# 🤖 Telegram Бот - Анализ матчей с телефона

## Зачем это нужно?

Вместо того чтобы:
1. Открывать компьютер
2. Запускать Python скрипты
3. Вводить команды

Теперь просто:
1. **Кидаешь скриншот** из Flashscore в Telegram
2. **Получаешь полный анализ** через 30 секунд
3. **Profit!** ⚽

## 📱 Быстрый старт (5 минут)

### Шаг 1: Создай Telegram бота

1. Открой Telegram → найди **@BotFather**
2. Отправь `/newbot`
3. Выбери имя: `Football Betting Bot`
4. Выбери username: `your_football_bot` (должен заканчиваться на `bot`)
5. **Скопируй токен** (будет выглядеть так: `123456:ABC-DEF1234...`)

### Шаг 2: Установи зависимости

```bash
pip install python-telegram-bot pillow pytesseract

# Для OCR (распознавание скриншотов):
# Linux:
sudo apt-get install tesseract-ocr tesseract-ocr-rus

# Mac:
brew install tesseract tesseract-lang

# Windows:
# Скачай с https://github.com/UB-Mannheim/tesseract/wiki
```

### Шаг 3: Запусти бота

```bash
python telegram_bot.py \
  --bot-token 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11 \
  --api-key ВАШ_API_КЛЮЧ_ОТ_API_FOOTBALL
```

### Шаг 4: Используй!

1. Найди своего бота в Telegram (по username)
2. Отправь `/start`
3. Кидай скриншоты или используй команды!

## 🎯 Как использовать

### Вариант 1: Скриншот (САМЫЙ УДОБНЫЙ)

```
1. Открой Flashscore в браузере/приложении
2. Скриншот страницы с матчами
3. Кинь фото боту в Telegram
4. Бот распознает матчи и предложит выбрать
5. Получишь полный анализ!
```

**Пример:**
```
[Кидаешь скриншот]

Бот: Найдены матчи:
1. Arsenal vs Chelsea
2. Manchester City vs Liverpool
3. Tottenham vs Manchester United

Выбери номер матча для анализа (1-3):

[Пишешь: 1]

Бот: [Полный анализ Arsenal vs Chelsea]
```

### Вариант 2: Команда

```
/analyze Arsenal vs Chelsea
```

или

```
/analyze Barcelona vs Real Madrid La_Liga
```

### Вариант 3: Топ матчи дня

```
/today
```

Бот покажет интересные матчи на сегодня с потенциальным value.

## 📋 Все команды

| Команда | Описание |
|---------|----------|
| `/start` | Начать работу |
| `/help` | Помощь |
| `/analyze Team1 vs Team2` | Анализ конкретного матча |
| `/analyze Team1 vs Team2 EPL` | Анализ с указанием лиги |
| `/leagues` | Список доступных лиг |
| `/today` | Топ матчи сегодня |
| `/stats` | Твоя статистика ставок |
| `/set_league EPL` | Лига по умолчанию |
| `/set_min_edge 5` | Минимальный edge (%) |

## 💡 Пример использования

### Утром:

```
Ты: [Скриншот матчей дня из Flashscore]

Бот: 📸 Получил скриншот! Распознаю матчи...

     Найдены матчи:
     1. Manchester City vs Liverpool (22:00)
     2. Arsenal vs Chelsea (19:45)
     3. Tottenham vs Manchester United (17:30)

     Выбери номер для анализа:

Ты: 1

Бот: 🔄 Анализирую: Manchester City vs Liverpool...
     ⏳ Это займет ~30 секунд...

     [Через 30 секунд]

     ⚽ **Manchester City vs Liverpool**

     📊 ПРОГНОЗ
     П1: 55.4% | X: 22.6% | П2: 22.0%
     ТБ 2.5: 65.4% | ТМ 2.5: 34.6%
     Обе забьют: 62.3%

     ⚽ Ожидаемые голы:
     Manchester City: 2.35
     Liverpool: 1.68

     💰 VALUE СТАВКИ:

     1. ТБ 2.5
        Коэффициент: 1.60
        Вероятность: 65.4%
        Edge: +9.1%
        💵 Ставка: 3.2% от банка

     ---
     ⚠️ Это не финансовый совет. Ставь ответственно!
```

### Вечером (быстрый запрос):

```
Ты: /analyze Arsenal vs Chelsea

Бот: [Полный анализ через 30 секунд]
```

## 🔧 Продвинутые настройки

### Запуск в фоне (Linux/Mac)

```bash
# Создай screen сессию
screen -S football_bot

# Запусти бота
python telegram_bot.py --bot-token YOUR_TOKEN --api-key YOUR_KEY

# Отсоединись: Ctrl+A, затем D
# Вернуться: screen -r football_bot
```

### Запуск как сервис (systemd)

Создай файл `/etc/systemd/system/football-bot.service`:

```ini
[Unit]
Description=Football Betting Telegram Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/flashscore
ExecStart=/usr/bin/python3 telegram_bot.py --bot-token YOUR_TOKEN --api-key YOUR_KEY
Restart=always

[Install]
WantedBy=multi-user.target
```

Запусти:
```bash
sudo systemctl enable football-bot
sudo systemctl start football-bot
sudo systemctl status football-bot
```

### Переменные окружения

Вместо передачи ключей в командной строке:

```bash
export TELEGRAM_BOT_TOKEN="your_token"
export API_FOOTBALL_KEY="your_key"

python telegram_bot.py
```

Обнови код:
```python
import os

bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
api_key = os.getenv('API_FOOTBALL_KEY')
```

## 📊 Что бот делает автоматически

При получении скриншота или команды:

1. ✅ **Распознает** названия команд (OCR)
2. ✅ **Находит матч** в расписании API-Football
3. ✅ **Собирает данные:**
   - Коэффициенты от букмекеров
   - Форма команд (W-W-D-L-W)
   - xG данные из Understat
   - Травмы и дисквалификации
   - H2H статистика
   - Место в таблице
4. ✅ **Корректирует** прогноз (форма, травмы, мотивация)
5. ✅ **Рассчитывает** вероятности (Пуассон + ELO)
6. ✅ **Находит** value ставки (edge > 5%)
7. ✅ **Рекомендует** размер ставки (Kelly criterion)

Всё это за **30 секунд**!

## ⚠️ Ограничения

### API-Football лимиты:
- **Бесплатно**: 100 запросов/день
- **1 матч** = ~10-12 запросов
- **Итого**: ~8-10 матчей/день

### OCR точность:
- Работает лучше с четкими скриншотами
- Английские названия команд распознаются лучше
- При проблемах - используй команду `/analyze`

## 🐛 Troubleshooting

### Бот не отвечает
```bash
# Проверь процесс
ps aux | grep telegram_bot.py

# Проверь логи
tail -f bot.log
```

### Ошибка "pytesseract not found"
```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# Mac
brew install tesseract

# Проверь установку
tesseract --version
```

### Не распознает скриншоты
- Сделай более четкий скриншот
- Используй вместо этого: `/analyze Team1 vs Team2`

### Ошибка API
- Проверь лимиты API-Football (100 запросов/день)
- Проверь правильность API ключа

## 🎁 Бонус: Уведомления

Настрой бота для отправки daily дайджеста:

```python
# В telegram_bot.py добавь:
async def daily_digest(context: ContextTypes.DEFAULT_TYPE):
    """Ежедневный дайджест матчей"""
    # Получи топ матчи
    # Отправь пользователям

# При запуске:
app.job_queue.run_daily(daily_digest, time=datetime.time(hour=9))
```

Теперь каждое утро в 9:00 будешь получать топ матчи дня!

## 📱 Для продвинутых: Web-версия

Если хочешь веб-интерфейс вместо Telegram:

```bash
python web_app.py --api-key YOUR_KEY
```

Открой браузер: `http://localhost:5000`

Загружай скриншоты прямо в браузере!

---

**Готово! Теперь анализ матчей всегда с тобой в телефоне! 🚀**
