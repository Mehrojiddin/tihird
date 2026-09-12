import os
import random
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, PollAnswerHandler

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

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
user_choices = {}

web = Flask(__name__)

@web.get("/")
def health():
    return "Footballbozibot is running", 200


def run_web():
    port = int(os.getenv("PORT", "10000"))
    web.run(host="0.0.0.0", port=port, use_reloader=False)


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
        options=["✅ Бале", "❌ Не"],
        is_anonymous=False,
        allows_multiple_answers=False,
    )

    if msg.poll:
        poll_chats[msg.poll.id] = update.effective_chat.id


async def poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.poll_answer
    if not answer or not answer.user:
        return

    chat_id = poll_chats.get(answer.poll_id)
    if not chat_id:
        return

    user = answer.user
    name = user.first_name or user.full_name or "Дӯстам"

    if not answer.option_ids:
        return

    choice = answer.option_ids[0]
    key = (answer.poll_id, user.id)
    previous = user_choices.get(key)
    user_choices[key] = choice

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

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("football", football))
    app.add_handler(PollAnswerHandler(poll_answer))
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
