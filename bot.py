import os
import random
import threading
import asyncio
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, PollAnswerHandler

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
REPORT_INTERVAL_SECONDS = 5 * 60 * 60

YES_JOKES = [
    "🔥 {name} — ана мард! ⚽ Бутсиро тайёр кун, майдон интизор аст! 😎",
    "💪 {name} «Бале» гуфт! Маълум, ки дар хона иҷозат гирифтааст 😂⚽",
    "🫡 {name} дар сафи аввал! Фақат баъд нагӯ: «поям дард кард» 😂",
    "⚽ {name} тайёр! Ана ҳамин хел одам лозим — гап кам, футбол зиёд! 🔥",
    "🏃‍♂️ {name} «Бале» гуфт! Акнун фақат дер накун, Роналду 😂",
    "😎 {name} аз футбол наметарсад! Майдон туро интизор аст, чемпион! 🏆",
]

NO_JOKES = [
    "😂 {name} имрӯз футбол намеравад. Эҳтимол навбати ҷомашӯӣ ба ӯ расидааст 🧺🤣",
    "👶 {name} «Не» гуфт. Имрӯз, маълум, кӯдаконро нигоҳ мекунад 😂",
    "🏠 {name} имрӯз хонашин шуд 😂 Футболро аз тиреза тамошо мекунад ⚽",
    "🤔 {name} «Не» гуфт... шояд корҳои хона рӯйхаташ дароз шудааст 😂",
    "🚨 Боз як футболбозро корҳои хона аз дастамон гирифтанд: {name} 😂",
    "🧹 {name} имрӯз футбол не — эҳтимол генералӣ уборка дорад 😂",
    "☕ {name} «Не» гуфт. Эҳтимол имрӯз реҷаи: чой, диван ва оромӣ 😂",
]

CHANGED_TO_YES = [
    "😂 Ана, {name} фикрашро дигар кард! Ба роҳи рост баргашт ⚽🔥",
    "👏 {name} охир фаҳмид, ки футбол аз корҳои хона беҳтар аст 😂⚽",
]

CHANGED_TO_NO = [
    "😅 {name} ақиб гашт... шояд аз хона занг заданд 😂",
    "📞 {name} фикрашро дигар кард. Эҳтимол фармони хона расид 😂",
]

poll_chats = {}
poll_votes = {}
report_tasks = {}

web = Flask(__name__)

@web.get("/")
def health():
    return "Footballbozibot is running", 200


def run_web():
    port = int(os.getenv("PORT", "10000"))
    web.run(host="0.0.0.0", port=port, use_reloader=False)


def build_report(poll_id: str) -> str:
    votes = poll_votes.get(poll_id, {})
    yes_names = [data["name"] for data in votes.values() if data["choice"] == 0]
    no_names = [data["name"] for data in votes.values() if data["choice"] == 1]

    yes_list = "\n".join(f"• {name}" for name in yes_names) if yes_names else "• Ҳоло касе нест"
    no_list = "\n".join(f"• {name}" for name in no_names) if no_names else "• Ҳоло касе нест"

    return (
        "⚽ НАТИҶАИ ОВОЗДИҲӢ\n\n"
        f"✅ Мераванд: {len(yes_names)} нафар\n"
        f"{yes_list}\n\n"
        f"❌ Намеравад: {len(no_names)} нафар\n"
        f"{no_list}\n\n"
        f"🔥 Ҳозир барои футбол {len(yes_names)} бозингар ҷамъ шуд!"
    )


async def periodic_report(bot, poll_id: str, chat_id: int):
    try:
        while True:
            await asyncio.sleep(REPORT_INTERVAL_SECONDS)
            await bot.send_message(chat_id=chat_id, text=build_report(poll_id))
    except asyncio.CancelledError:
        pass


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚽ Салом! Ман боти футболи гурӯҳ ҳастам.\n\n"
        "Барои оғоз кардани овоздиҳӣ нависед: /football"
    )


async def football(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or not update.message:
        return

    msg = await context.bot.send_poll(
        chat_id=update.effective_chat.id,
        question="⚽ Футбол мерем?",
        options=["Бале", "Не"],
        is_anonymous=False,
        allows_multiple_answers=False,
    )

    if msg.poll:
        poll_id = msg.poll.id
        poll_chats[poll_id] = update.effective_chat.id
        poll_votes[poll_id] = {}
        report_tasks[poll_id] = asyncio.create_task(
            periodic_report(context.bot, poll_id, update.effective_chat.id)
        )


async def poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.poll_answer
    if not answer or not answer.user:
        return

    chat_id = poll_chats.get(answer.poll_id)
    if not chat_id:
        return

    user = answer.user
    name = user.full_name or user.first_name or "Дӯстам"
    votes = poll_votes.setdefault(answer.poll_id, {})
    previous_data = votes.get(user.id)

    if not answer.option_ids:
        votes.pop(user.id, None)
        return

    choice = answer.option_ids[0]
    previous = previous_data["choice"] if previous_data else None
    votes[user.id] = {"name": name, "choice": choice}

    if previous is not None and previous != choice:
        text = random.choice(CHANGED_TO_YES if choice == 0 else CHANGED_TO_NO).format(name=name)
    elif choice == 0:
        text = random.choice(YES_JOKES).format(name=name)
    else:
        text = random.choice(NO_JOKES).format(name=name)

    await context.bot.send_message(chat_id=chat_id, text=text)


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set")

    threading.Thread(target=run_web, daemon=True).start()
    asyncio.set_event_loop(asyncio.new_event_loop())

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("football", football))
    app.add_handler(PollAnswerHandler(poll_answer))
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
