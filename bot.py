from fuzzywuzzy import fuzz
from datetime import datetime
import asyncio
import logging
import gspread
import sys

from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardBuilder
from aiogram.utils.markdown import hbold

from functions import get_movies, get_indexes

from config import TOKEN


logging.basicConfig(level=logging.INFO, stream=sys.stdout)

# google sheets
gs = gspread.service_account('venv\\true-sprite-405907-da4b97639184.json')
sht = gs.open_by_url('https://docs.google.com/spreadsheets/d/12ccv7iv0kmbs8i2sbFy7FX6gETAc5_r2kAx1AoAVvu8/edit#gid=245321756')
worksheet1 = sht.get_worksheet(0)
worksheet2 = sht.get_worksheet(1)

# get list1 and list1 from Google sheets
dt_list1 = worksheet1.get_all_values()
dt_list2 = worksheet2.get_all_values()


unique_cinemas_titles = []
for item in dt_list1:
    unique_cinemas_titles.append(item[1])
unique_cinemas_titles = tuple(set(unique_cinemas_titles))


unique_movies_titles = []
for item in dt_list1:
    unique_movies_titles.append(item[0])
unique_movies_titles = tuple(set(unique_movies_titles))


# structure of type: {cinema: {movie: [time]}}
schedule_data_from_list1 = {}
for item in dt_list1:
    cinema = item[1]
    if cinema not in schedule_data_from_list1:
        schedule_data_from_list1[cinema] = {}

    movie = item[0]
    if movie not in schedule_data_from_list1[cinema]:
        schedule_data_from_list1[cinema][movie] = []

    for dt in item[2:]:
        if dt != '':
            schedule_data_from_list1[cinema][movie].append(datetime.fromtimestamp(float(dt)))


# structure of type: {movie: {description: [params]}}
schedule_data_from_list2 = {}
for item in dt_list2:
    movie = item[0]
    if movie not in schedule_data_from_list2:
        schedule_data_from_list2[movie] = {}

    description = item[1]
    if description not in schedule_data_from_list2[movie]:
        schedule_data_from_list2[movie][description] = []

    for param in item[2:]:
        if param != '':
            schedule_data_from_list2[movie][description].append(param)


# murkups
async def ikb_options(indexes: tuple | list, element_type: str, titles: tuple | list, current_page=1) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    buttons_on_page = 10
    pages_count = (len(indexes) - 1) // buttons_on_page + 1

    for ind in indexes[:buttons_on_page]:
        builder.button(text=titles[ind], callback_data=f'{element_type}_{ind}')
    builder.adjust(1)

    if len(indexes) > buttons_on_page:
        builder.button(text=f'{current_page} / {pages_count}', callback_data='pages_count')
        builder.adjust(1)
        builder.button(text='>>', callback_data=f'next_{current_page + 1}_{element_type}')

    if current_page > 1:
        builder = InlineKeyboardBuilder()
        for ind in indexes[(current_page - 1) * buttons_on_page:current_page * buttons_on_page]:
            builder.button(text=titles[ind], callback_data=f'{element_type}_{ind}')
        builder.adjust(1)

        builder.button(text='<<', callback_data=f'next_{current_page - 1}_{element_type}')
        builder.adjust(1)
        builder.button(text=f'{current_page} / {pages_count}', callback_data='pages_count')

        if current_page < pages_count:
            builder.button(text='>>', callback_data=f'next_{current_page + 1}_{element_type}')

    ikb = builder.as_markup()

    return ikb


bot = Bot(token=TOKEN)
dp = Dispatcher(skip_updates=True)

selected_user_cinema = {}
selected_user_date = {}


@dp.message(Command('start'))
async def command_start_handler(message: Message) -> None:

    kb = [
        [KeyboardButton(text='Дата✅'), KeyboardButton(text='Кинотеатр✅')]
    ]
    start_kb = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

    await message.reply(text=f'Приветствую, {hbold(message.from_user.full_name)}!\n'
                             f'Выберите начальный критерий для поиска сеанса:',
                        reply_markup=start_kb,
                        parse_mode=ParseMode.HTML)


@dp.message(F.text.lower() == 'дата✅')
async def handler_text_date(message: Message):
    try:
        del selected_user_date[message.from_user.id]
        del selected_user_cinema[message.from_user.id]
    except KeyError:
        pass

    await message.answer(text='Выберите дату:',
                         reply_markup=await SimpleCalendar().start_calendar())


@dp.message(F.text.lower() == 'кинотеатр✅')
async def handler_text_cinema(message: Message):
    try:
        del selected_user_date[message.from_user.id]
        del selected_user_cinema[message.from_user.id]
    except KeyError:
        pass

    cinemas_indexes = get_indexes(unique_cinemas_titles, unique_cinemas_titles)
    await message.answer(text='Выберите кинотеатр:',
                         reply_markup=await ikb_options(indexes=cinemas_indexes,
                                                        titles=unique_cinemas_titles,
                                                        element_type='cinema'))


@dp.message(F.text)
async def handler_text_messages(message: Message):
    movies = []
    for movie in unique_movies_titles:
        if fuzz.WRatio(movie, message.text) >= 70:
            movies.append(movie)

    if movies:
        indexes = get_indexes(unique_movies_titles, movies)
        await message.answer(text='Фильмы по вашему запросу:',
                             reply_markup=await ikb_options(indexes=indexes,
                                                            element_type='movie',
                                                            titles=unique_movies_titles))
    else:
        await message.answer(text='Фильмов по вашему запросу не найдено.')


@dp.callback_query(SimpleCalendarCallback.filter())
async def process_simple_calendar(callback_query: CallbackQuery, callback_data: CallbackData):
    selected, date = await SimpleCalendar().process_selection(callback_query, callback_data)
    if selected:
        user_date = datetime.date(date)
        current_date = datetime.now().date()

        if user_date < current_date:
            await callback_query.message.edit_text(text='Выбранная вами дата уже прошла, пожалуйста, выберите другую дату:',
                                                   reply_markup=await SimpleCalendar().start_calendar())
            return

        cinemas_indexes = get_indexes(unique_cinemas_titles, unique_cinemas_titles)

        selected_user_date[callback_query.from_user.id] = user_date
        cinema_ind = selected_user_cinema.get(callback_query.from_user.id)

        if cinema_ind:
            cinema = unique_cinemas_titles[cinema_ind]
            movies_titles = get_movies(schedule_data_from_list1, cinema, user_date)
            movies_titles_indexes = get_indexes(unique_movies_titles, movies_titles)

            await callback_query.message.edit_text(text=f'Фильмы которые пройдут {user_date.strftime("%d.%m.%Y")} в кинотеатре - "{cinema}":',
                                                   reply_markup=await ikb_options(titles=unique_movies_titles,
                                                                                  indexes=movies_titles_indexes,
                                                                                  element_type='movie'))
            return

        await callback_query.message.edit_text(text=f'Теперь выберите кинотеатр:',
                                               reply_markup=await ikb_options(titles=unique_cinemas_titles,
                                                                              indexes=cinemas_indexes,
                                                                              element_type='cinema'))


@dp.callback_query(F.data.startswith('next'))
async def cb_next_page(callback_query: CallbackQuery):
    cb_data = callback_query.data.split('_')
    page = int(cb_data[1])
    element_type = cb_data[2]

    titles = None
    indexes = None

    if element_type == 'cinema':
        titles = unique_cinemas_titles
        indexes = get_indexes(titles, titles)

    elif element_type == 'movie':
        cinema_ind = selected_user_cinema.get(callback_query.from_user.id)
        cinema = unique_cinemas_titles[cinema_ind]

        movies_titles = get_movies(schedule_data=schedule_data_from_list1,
                                   cinema=cinema,
                                   user_date=selected_user_date.get(callback_query.from_user.id))

        titles = unique_movies_titles
        indexes = get_indexes(titles, movies_titles)

    await callback_query.message.edit_reply_markup(reply_markup=await ikb_options(titles=titles,
                                                                                  indexes=indexes,
                                                                                  element_type=element_type,
                                                                                  current_page=page))


@dp.callback_query(F.data.startswith('cinema'))
async def cb_cinema(callback_query: CallbackQuery):
    cinema_ind = int(callback_query.data.split('_')[1])
    cinema = unique_cinemas_titles[cinema_ind]
    selected_user_cinema[callback_query.from_user.id] = cinema_ind
    user_date = selected_user_date.get(callback_query.from_user.id)

    if user_date:
        movies_titles = get_movies(schedule_data_from_list1, cinema, user_date)
        movies_titles_indexes = get_indexes(unique_movies_titles, movies_titles)

        await callback_query.message.edit_text(text=f'Фильмы которые пройдут {user_date.strftime("%d.%m.%Y")} в кинотеатре - "{cinema}":',
                                               reply_markup=await ikb_options(titles=unique_movies_titles,
                                                                              indexes=movies_titles_indexes,
                                                                              element_type='movie'))
    else:
        await callback_query.message.edit_text(text='Теперь выберите дату:',
                                               reply_markup=await SimpleCalendar().start_calendar())


@dp.callback_query(F.data.startswith('movie'))
async def cb_movie(callback_query: CallbackQuery):
    cb_data = callback_query.data.split('_')
    movie_ind = int(cb_data[1])
    movie = unique_movies_titles[movie_ind]

    await callback_query.message.answer(text=movie)

    for description, params in schedule_data_from_list2[movie].items():
        await callback_query.message.answer(text=description)

        text = ''
        for param in params:
            text += param + '\n'
        await callback_query.message.answer(text=text)


async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
