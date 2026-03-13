import math
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    CallbackQueryHandler,
    ConversationHandler,
)

TOKEN = "8520825166:AAFNnP4yyjNl9ch-sTxq5NjVlVW0sENtsYY"

H5PLUS, H5MINUS, A5PLUS, A5MINUS = range(4)


def normal_cdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️: H5+\nEnter HOME team last 5 scored points\n(one per line)"
    )
    return H5PLUS


async def h5plus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["h5plus"] = list(map(int, update.message.text.split()))
    await update.message.reply_text(
        "ℹ️: H5-\nEnter HOME team last 5 conceded points"
    )
    return H5MINUS


async def h5minus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["h5minus"] = list(map(int, update.message.text.split()))
    await update.message.reply_text(
        "ℹ️: A5+\nEnter AWAY team last 5 scored points"
    )
    return A5PLUS


async def a5plus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["a5plus"] = list(map(int, update.message.text.split()))
    await update.message.reply_text(
        "ℹ️: A5-\nEnter AWAY team last 5 conceded points"
    )
    return A5MINUS


async def a5minus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["a5minus"] = list(map(int, update.message.text.split()))

    h5p = context.user_data["h5plus"]
    h5m = context.user_data["h5minus"]
    a5p = context.user_data["a5plus"]
    a5m = context.user_data["a5minus"]

    # Attack vs Defense model
    home_attack = sum(h5p) / 5
    home_def = sum(h5m) / 5
    away_attack = sum(a5p) / 5
    away_def = sum(a5m) / 5

    home_points = (home_attack + away_def) / 2
    away_points = (away_attack + home_def) / 2

    model1 = home_points + away_points

    # Last 5 totals model
    home_totals = [(h5p[i] + h5m[i]) for i in range(5)]
    away_totals = [(a5p[i] + a5m[i]) for i in range(5)]

    model2 = (sum(home_totals) / 5 + sum(away_totals) / 5) / 2

    expected = (model1 + model2) / 2

    # probability model
    line = expected - 8.5
    z = (expected - line) / 12

    prob = round(normal_cdf(z) * 100)

    if prob >= 70:
        level = "HIGH"
    elif prob >= 55:
        level = "MEDIUM"
    else:
        level = "LOW"

    keyboard = [[InlineKeyboardButton("🔄 Repeat Analysis", callback_data="repeat")]]

    await update.message.reply_text(
        f"🛜: TOTAL POINTS OVER [ {round(expected)} ]\n"
        f"✅: Confidence [ {prob}% ] | {level}",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    return ConversationHandler.END


async def repeat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.message.reply_text(
        "ℹ️: H5+\nEnter HOME team last 5 scored points"
    )

    return H5PLUS


def main():

    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            H5PLUS: [MessageHandler(filters.TEXT & ~filters.COMMAND, h5plus)],
            H5MINUS: [MessageHandler(filters.TEXT & ~filters.COMMAND, h5minus)],
            A5PLUS: [MessageHandler(filters.TEXT & ~filters.COMMAND, a5plus)],
            A5MINUS: [MessageHandler(filters.TEXT & ~filters.COMMAND, a5minus)],
        },
        fallbacks=[],
    )

    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(repeat))

    print("Bot started")

    app.run_polling()


if __name__ == "__main__":
    main()
