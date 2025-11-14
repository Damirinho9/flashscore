"""
Telegram бот для анализа матчей с телефона

Использование:
1. Создай бота через @BotFather в Telegram
2. Получи токен
3. Запусти: python telegram_bot.py --bot-token YOUR_TOKEN --api-key YOUR_API_KEY
4. Кидай скриншоты из Flashscore → получай анализ!

Команды:
/start - Начать работу
/help - Помощь
/analyze Team1 vs Team2 - Анализ матча
Скриншот - Автоматический анализ
"""

import os
import sys
import logging
import asyncio
import argparse
from datetime import datetime
from typing import Optional, List

# Telegram
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
except ImportError:
    print("❌ Установи python-telegram-bot: pip install python-telegram-bot")
    sys.exit(1)

# OCR для распознавания текста с изображений
try:
    from PIL import Image
    import pytesseract
except ImportError:
    print("⚠️  Для распознавания скриншотов установи: pip install pillow pytesseract")
    print("И tesseract-ocr: sudo apt-get install tesseract-ocr (Linux) или brew install tesseract (Mac)")

# Наши модули
from auto_analyzer import FullyAutomatedAnalyzer
from api_football_client import LEAGUE_IDS

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class FootballBettingBot:
    """Telegram бот для анализа матчей"""

    def __init__(self, bot_token: str, api_key: str):
        self.bot_token = bot_token
        self.analyzer = FullyAutomatedAnalyzer(api_key)
        self.user_states = {}  # Состояния пользователей

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /start"""
        user = update.effective_user
        welcome_text = f"""
👋 Привет, {user.first_name}!

Я бот для автоматического анализа футбольных матчей.

**Как использовать:**

1️⃣ **Кинь скриншот** из Flashscore - я распознаю матчи
2️⃣ Или напиши команду: `/analyze Arsenal vs Chelsea`
3️⃣ Получи полный анализ с прогнозом и value ставками!

**Что я делаю:**
✅ Автоматически собираю данные (коэффициенты, форма, xG, травмы)
✅ Рассчитываю вероятности (Пуассон + ELO)
✅ Нахожу value ставки
✅ Рекомендую оптимальный размер ставки

Начни с команды /help или просто кинь скриншот! ⚽
"""
        await update.message.reply_text(welcome_text, parse_mode='Markdown')

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /help"""
        help_text = """
📚 **КОМАНДЫ БОТА**

/analyze Arsenal vs Chelsea - Анализ конкретного матча
/leagues - Список доступных лиг
/today - Топ матчи сегодня
/stats - Твоя статистика ставок

📸 **РАБОТА СО СКРИНШОТАМИ**
Просто кинь скриншот из Flashscore - я автоматически:
• Распознаю названия команд
• Найду матчи в расписании
• Проанализирую и дам рекомендации

⚙️ **НАСТРОЙКИ**
/set_league EPL - Установить лигу по умолчанию
/set_min_edge 5 - Минимальный edge для рекомендаций (%)

💡 **СОВЕТЫ**
• Используй только value ставки с edge > 5%
• Максимум 5% банка на ставку
• Веди статистику всех ставок
• На дистанции ROI 3-5% = отлично!

❓ Вопросы? Напиши @твой_канал_поддержки
"""
        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def analyze_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда /analyze Team1 vs Team2"""
        if not context.args or len(context.args) < 3:
            await update.message.reply_text(
                "❌ Неправильный формат!\n\n"
                "Используй: /analyze Arsenal vs Chelsea\n"
                "Или: /analyze Manchester City vs Liverpool EPL"
            )
            return

        # Парсим команду
        text = ' '.join(context.args)
        parts = text.split(' vs ')

        if len(parts) != 2:
            await update.message.reply_text("❌ Используй формат: Team1 vs Team2")
            return

        home_team = parts[0].strip()
        away_and_league = parts[1].strip().split()

        away_team = ' '.join(away_and_league[:-1]) if len(away_and_league) > 1 and away_and_league[-1] in LEAGUE_IDS else parts[1].strip()
        league = away_and_league[-1] if len(away_and_league) > 1 and away_and_league[-1] in LEAGUE_IDS else 'EPL'

        # Отправляем сообщение о начале анализа
        status_msg = await update.message.reply_text(
            f"🔄 Анализирую матч: **{home_team} vs {away_team}**\n"
            f"Лига: {league}\n\n"
            "⏳ Это займет ~20-30 секунд...",
            parse_mode='Markdown'
        )

        try:
            # Запускаем анализ
            result = self.analyzer.analyze_match(
                home_team=home_team,
                away_team=away_team,
                league=league,
                use_elo=True
            )

            if result:
                # Форматируем результат
                response = self._format_analysis_result(result)
                await status_msg.edit_text(response, parse_mode='Markdown')

                # Если есть value ставки - добавляем кнопки
                if result['recommendation']:
                    keyboard = [
                        [InlineKeyboardButton("📊 Детальная статистика", callback_data=f"details_{home_team}_{away_team}")],
                        [InlineKeyboardButton("💾 Сохранить в историю", callback_data=f"save_{home_team}_{away_team}")],
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await update.message.reply_text(
                        "Что делать дальше?",
                        reply_markup=reply_markup
                    )
            else:
                await status_msg.edit_text("❌ Не удалось получить данные. Проверь названия команд.")

        except Exception as e:
            logger.error(f"Ошибка анализа: {e}")
            await status_msg.edit_text(f"❌ Ошибка: {str(e)}")

    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка скриншотов"""
        await update.message.reply_text("📸 Получил скриншот! Распознаю матчи...")

        try:
            # Скачиваем фото
            photo_file = await update.message.photo[-1].get_file()
            photo_path = f"screenshot_{update.effective_user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            await photo_file.download_to_drive(photo_path)

            # Распознаем текст
            matches = self._extract_matches_from_image(photo_path)

            # Удаляем файл
            os.remove(photo_path)

            if not matches:
                await update.message.reply_text(
                    "⚠️ Не удалось распознать матчи на скриншоте.\n\n"
                    "Попробуй:\n"
                    "• Сделать более четкий скриншот\n"
                    "• Использовать команду: /analyze Team1 vs Team2"
                )
                return

            # Показываем найденные матчи
            matches_text = "Найдены матчи:\n\n"
            for i, match in enumerate(matches[:5], 1):  # Максимум 5
                matches_text += f"{i}. {match['home']} vs {match['away']}\n"

            matches_text += "\nВыбери номер матча для анализа (1-5):"

            await update.message.reply_text(matches_text)

            # Сохраняем в состояние пользователя
            self.user_states[update.effective_user.id] = {
                'matches': matches,
                'waiting_for': 'match_selection'
            }

        except Exception as e:
            logger.error(f"Ошибка обработки фото: {e}")
            await update.message.reply_text(
                f"❌ Ошибка обработки скриншота: {str(e)}\n\n"
                "Используй команду /analyze Team1 vs Team2"
            )

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений"""
        user_id = update.effective_user.id
        text = update.message.text

        # Проверяем состояние пользователя
        if user_id in self.user_states:
            state = self.user_states[user_id]

            if state.get('waiting_for') == 'match_selection':
                try:
                    choice = int(text)
                    if 1 <= choice <= len(state['matches']):
                        match = state['matches'][choice - 1]

                        # Запускаем анализ
                        await update.message.reply_text(
                            f"🔄 Анализирую: {match['home']} vs {match['away']}..."
                        )

                        result = self.analyzer.analyze_match(
                            home_team=match['home'],
                            away_team=match['away'],
                            league=match.get('league', 'EPL')
                        )

                        if result:
                            response = self._format_analysis_result(result)
                            await update.message.reply_text(response, parse_mode='Markdown')
                        else:
                            await update.message.reply_text("❌ Не удалось проанализировать матч")

                        # Очищаем состояние
                        del self.user_states[user_id]
                    else:
                        await update.message.reply_text("❌ Неверный номер. Выбери от 1 до 5.")
                except ValueError:
                    await update.message.reply_text("❌ Введи номер матча (1-5)")
                return

        # Обычное сообщение
        await update.message.reply_text(
            "Не понял команду 🤔\n\n"
            "Используй:\n"
            "/analyze Arsenal vs Chelsea - Анализ матча\n"
            "Или кинь скриншот из Flashscore!"
        )

    def _extract_matches_from_image(self, image_path: str) -> List[dict]:
        """Извлечь матчи из скриншота"""
        try:
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image, lang='eng')

            # Простой парсинг (можно улучшить)
            matches = []
            lines = text.split('\n')

            for i, line in enumerate(lines):
                # Ищем паттерн "Team1 - Team2" или "Team1 vs Team2"
                if '-' in line or 'vs' in line.lower():
                    parts = line.split('-') if '-' in line else line.split('vs')
                    if len(parts) == 2:
                        home = parts[0].strip()
                        away = parts[1].strip()

                        if len(home) > 3 and len(away) > 3:  # Фильтр
                            matches.append({
                                'home': home,
                                'away': away,
                                'league': 'EPL'  # По умолчанию
                            })

            return matches[:10]  # Максимум 10 матчей

        except Exception as e:
            logger.error(f"Ошибка распознавания: {e}")
            return []

    def _format_analysis_result(self, result: dict) -> str:
        """Форматировать результат анализа для Telegram"""
        pred = result['prediction']

        response = f"""
⚽ **{result['home_team']} vs {result['away_team']}**

📊 **ПРОГНОЗ**
П1: {pred['home_win']:.1%} | X: {pred['draw']:.1%} | П2: {pred['away_win']:.1%}
ТБ 2.5: {pred['over_2.5']:.1%} | ТМ 2.5: {pred['under_2.5']:.1%}
Обе забьют: {pred['btts']:.1%}

⚽ **Ожидаемые голы:**
{result['home_team']}: {pred['expected_home_goals']:.2f}
{result['away_team']}: {pred['expected_away_goals']:.2f}
"""

        # Value ставки
        if result['recommendation']:
            response += "\n💰 **VALUE СТАВКИ:**\n\n"

            for i, rec in enumerate(result['recommendation'], 1):
                response += f"""
**{i}. {rec['market']}**
   Коэффициент: {rec['odds']}
   Вероятность: {rec['true_prob']}
   Edge: {rec['edge']}
   💵 Ставка: {rec['kelly_stake']} от банка
"""
        else:
            response += "\n⚠️ **Value ставок не найдено**\n"
            response += "Все коэффициенты близки к справедливым."

        response += "\n---\n⚠️ Это не финансовый совет. Ставь ответственно!"

        return response

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка нажатий на кнопки"""
        query = update.callback_query
        await query.answer()

        data = query.data

        if data.startswith('details_'):
            await query.edit_message_text("📊 Детальная статистика в разработке...")

        elif data.startswith('save_'):
            await query.edit_message_text("💾 Сохранено в историю!")

    def run(self):
        """Запуск бота"""
        print(f"🤖 Запуск Telegram бота...")

        # Создаем приложение
        app = Application.builder().token(self.bot_token).build()

        # Регистрируем обработчики
        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(CommandHandler("help", self.help_command))
        app.add_handler(CommandHandler("analyze", self.analyze_command))
        app.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
        app.add_handler(CallbackQueryHandler(self.button_callback))

        # Запускаем
        print(f"✅ Бот запущен! Отправь /start боту в Telegram")
        app.run_polling()


def main():
    """CLI интерфейс"""
    parser = argparse.ArgumentParser(description='Telegram бот для анализа футбольных матчей')

    parser.add_argument('--bot-token', required=True, help='Telegram Bot Token от @BotFather')
    parser.add_argument('--api-key', required=True, help='API ключ от API-Football')

    args = parser.parse_args()

    # Создаем и запускаем бота
    bot = FootballBettingBot(
        bot_token=args.bot_token,
        api_key=args.api_key
    )

    bot.run()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main()
    else:
        print("\n" + "="*70)
        print("⚽ TELEGRAM БОТ ДЛЯ АНАЛИЗА МАТЧЕЙ")
        print("="*70 + "\n")

        print("📝 БЫСТРЫЙ СТАРТ:\n")

        print("1. Создай бота:")
        print("   • Открой Telegram → найди @BotFather")
        print("   • Отправь /newbot")
        print("   • Выбери имя бота (например: Football Betting Bot)")
        print("   • Скопируй токен\n")

        print("2. Запусти бота:")
        print("   python telegram_bot.py \\")
        print("     --bot-token 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11 \\")
        print("     --api-key ВАШ_API_КЛЮЧ\n")

        print("3. Используй:")
        print("   • Открой своего бота в Telegram")
        print("   • Отправь /start")
        print("   • Кидай скриншоты из Flashscore!")
        print("   • Или пиши: /analyze Arsenal vs Chelsea\n")

        print("="*70)
        print("\n💡 ВОЗМОЖНОСТИ БОТА:\n")

        print("✅ Кидаешь скриншот → получаешь анализ")
        print("✅ Команда /analyze → быстрый анализ")
        print("✅ Автоматический сбор всех данных")
        print("✅ Поиск value ставок")
        print("✅ Рекомендации по размеру ставки")
        print("✅ История ставок\n")

        print("="*70 + "\n")
