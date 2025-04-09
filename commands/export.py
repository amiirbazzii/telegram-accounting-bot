# commands/export.py
import asyncio
import csv
import io
from telegram import Update
from telegram.ext import ContextTypes
from utils.google_sheet import get_google_sheet

async def export_expenses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        sheet = await asyncio.to_thread(get_google_sheet)
        rows = await asyncio.to_thread(sheet.get_all_records)

        if not rows:
            await update.message.reply_text("No expenses found to export.")
            return

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["Description", "Date", "Amount", "Category", "Related to"])
        writer.writeheader()
        writer.writerows(rows)
        output.seek(0)
        await update.message.reply_document(
            document=output,
            filename="expenses.csv",
            caption="Here is your exported expenses file."
        )
    except Exception as e:
        await update.message.reply_text(f"An error occurred: {str(e)}")