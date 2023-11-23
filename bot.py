import asyncio
import logging
import gspread
import sys

from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.types import Message, CallbackQuery
from aiogram.utils.markdown import hbold

from config import TOKEN

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

# google sheets
gs = gspread.service_account('venv\\true-sprite-405907-da4b97639184.json')
sht = gs.open_by_url('https://docs.google.com/spreadsheets/d/12ccv7iv0kmbs8i2sbFy7FX6gETAc5_r2kAx1AoAVvu8/edit#gid=245321756')
worksheet1 = sht.get_worksheet(0)
worksheet2 = sht.get_worksheet(1)

dt_list1 = worksheet1.get_all_values()
dt_list2 = worksheet2.get_all_values()


bot = Bot(token=TOKEN)
dp = Dispatcher(skip_updates=True)


@dp.message(Command('start'))
async def command_start_handler(message: Message) -> None:
    await message.reply(f"Hello, {hbold(message.from_user.full_name)}! Pick a calendar", reply_markup=await SimpleCalendar().start_calendar(),
                        parse_mode=ParseMode.HTML)


# simple calendar usage - filtering callbacks of calendar format
@dp.callback_query(SimpleCalendarCallback.filter())
async def process_simple_calendar(callback_query: CallbackQuery, callback_data: CallbackData):
    selected, date = await SimpleCalendar().process_selection(callback_query, callback_data)
    if selected:
        await callback_query.message.answer(
            f'You selected {date.strftime("%d/%m/%Y")}',
        )




async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
