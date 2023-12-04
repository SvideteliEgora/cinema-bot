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
from aiogram.utils.keyboard import InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardBuilder, InlineKeyboardButton
from aiogram.utils.markdown import hbold

from functions import get_movies_and_showtime

from config import TOKEN


logging.basicConfig(level=logging.INFO, stream=sys.stdout)

bot = Bot(token=TOKEN)
dp = Dispatcher(skip_updates=True)


# google sheets
gs = gspread.service_account('venv\\true-sprite-405907-da4b97639184.json')
sht = gs.open_by_url('https://docs.google.com/spreadsheets/d/12ccv7iv0kmbs8i2sbFy7FX6gETAc5_r2kAx1AoAVvu8/edit#gid=245321756')
worksheet1 = sht.get_worksheet(0)
worksheet2 = sht.get_worksheet(1)


# get list1 and list1 from Google sheets
dt_list1 = worksheet1.get_all_values()
dt_list2 = worksheet2.get_all_values()


selected_user_cinema = {}
selected_user_date = {}
selected_user_movie = {}


all_cinemas_titles = []
for item in dt_list1:
    all_cinemas_titles.append(item[1])
all_cinemas_titles = tuple(set(all_cinemas_titles))


all_movies_titles = []
for item in dt_list1:
    all_movies_titles.append(item[0])
all_movies_titles = tuple(set(all_movies_titles))


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
kb = [
    [KeyboardButton(text='Дата✅'), KeyboardButton(text='Кинотеатр✅')]
]
start_kb = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


async def ikb_cinemas(cinemas: list, all_cinemas_titles: list | tuple, current_page=1) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    buttons_on_page = 10
    pages_count = (len(cinemas) - 1) // buttons_on_page + 1

    for cin in cinemas[:buttons_on_page]:
        builder.button(text=cin, callback_data=f'cinema_{all_cinemas_titles.index(cin)}')
    builder.adjust(1)

    if len(cinemas) > buttons_on_page:
        builder.button(text=f'{current_page} / {pages_count}', callback_data='pages_count')
        builder.adjust(1)
        builder.button(text='>>', callback_data=f'next_cinema_{current_page + 1}')

    if current_page > 1:
        builder = InlineKeyboardBuilder()
        for cin in cinemas[(current_page - 1) * buttons_on_page:current_page * buttons_on_page]:
            builder.button(text=cin, callback_data=f'cinema_{all_cinemas_titles.index(cin)}')
        builder.adjust(1)

        builder.button(text='<<', callback_data=f'next_cinema_{current_page - 1}')
        builder.adjust(1)
        builder.button(text=f'{current_page} / {pages_count}', callback_data='pages_count')

        if current_page < pages_count:
            builder.button(text='>>', callback_data=f'next_cinema_{current_page + 1}')

    ikb = builder.as_markup()

    return ikb


async def ikb_movies(movies_data: list | tuple, all_movies_titles: list | tuple) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for movie in movies_data:
        builder.button(text=f'{movie}', callback_data=f'movie_{all_movies_titles.index(movie)}')
    builder.adjust(1)

    return builder.as_markup()


# functions
async def clear_user_selections(user_id: int) -> None:
    global selected_user_date, selected_user_cinema, selected_user_movie
    try:
        print(f"До очистки: {selected_user_date.get(user_id)}")
        selected_user_date[user_id] = None

        print(f"До очистки: {selected_user_cinema.get(user_id)}")
        selected_user_cinema[user_id] = None

        print(f"До очистки: {selected_user_movie.get(user_id)}")
        selected_user_movie[user_id] = None
    except KeyError:
        pass
    finally:
        print(f"После очистки: {selected_user_date.get(user_id)}")
        print(f"После очистки: {selected_user_cinema.get(user_id)}")
        print(f"После очистки: {selected_user_movie.get(user_id)}")


async def send_movie_schedule(callback_query, movie_and_showtime, user_date, user_cinema, all_movies_titles) -> None:
    for item in movie_and_showtime:
        for movie, showtime in item.items():
            ikb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=movie, callback_data=f'movie_{all_movies_titles.index(movie)}')]])
            await callback_query.message.answer(text=f'Дата: {user_date.strftime("%d.%m.%Y")}\n'
                                                     f'Кинотеатр: "{user_cinema}"\n'
                                                     f'Время сеансов: {", ".join(showtime)}\n'
                                                     f'Фильм:⬇️',
                                                reply_markup=ikb)


# handlers
@dp.message(Command('start'))
async def command_start_handler(message: Message) -> None:
    await clear_user_selections(message.from_user.id)
    await message.reply(text=f'Приветствую, {hbold(message.from_user.full_name)}!\n'
                             f'Выберите начальный критерий для поиска сеанса:',
                        reply_markup=start_kb,
                        parse_mode=ParseMode.HTML)


@dp.message(F.text == 'Дата✅')
async def date_handler(message: Message) -> None:

    await message.answer(text='Выберите дату:',
                         reply_markup=await SimpleCalendar().start_calendar())


@dp.message(F.text == 'Кинотеатр✅')
async def cinema_handler(message: Message) -> None:

    await message.answer(text='Выберите кинотеатр:',
                         reply_markup=await ikb_cinemas(cinemas=all_cinemas_titles,
                                                        all_cinemas_titles=all_cinemas_titles))


@dp.message(F.text)
async def handler_text_messages(message: Message):
    movies = []

    await clear_user_selections(message.from_user.id)
    for movie in all_movies_titles:
        if fuzz.WRatio(movie, message.text) == 100:
            ikb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=movie, callback_data=f'movie_{all_movies_titles.index(movie)}')]])
            await message.answer(text='Фильм по вашему запросу:',
                                 reply_markup=ikb)
        elif fuzz.WRatio(movie, message.text) >= 85:
            movies.append(movie)

    if movies:
        await message.answer(text='Фильмы по вашему запросу:',
                             reply_markup=await ikb_movies(movies_data=movies,
                                                           all_movies_titles=all_movies_titles))
    else:
        await message.answer(text='По вашему запросу нет совпадений.')


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

        selected_user_date[callback_query.from_user.id] = user_date
        user_cinema = selected_user_cinema.get(callback_query.from_user.id)
        user_movie = selected_user_movie.get(callback_query.from_user.id)

        if user_cinema:
            movie_and_showtime = get_movies_and_showtime(schedule_data_from_list1, user_cinema, user_date)
            await send_movie_schedule(callback_query, movie_and_showtime, user_date, user_cinema, all_movies_titles)
            await clear_user_selections(callback_query.from_user.id)

        elif user_movie:
            for cinema, movie_and_showtime in schedule_data_from_list1.items():
                for movie, showtime in movie_and_showtime.items():
                    if movie == user_movie:
                        showtime_list = []
                        for st in showtime:
                            if st.date() == user_date:
                                showtime_list.append(st.strftime('%H:%M'))
                        await callback_query.message.answer(text=f'Кинотеатр: "{cinema}"\n'
                                                                 f'Фильм: "{user_movie}"\n'
                                                                 f'Дата: {user_date.strftime("%d.%m.%Y")}\n'
                                                                 f'Время сеансов: {", ".join(showtime_list)}')
                        await clear_user_selections(callback_query.from_user.id)
        else:
            await callback_query.message.edit_text(text=f'Теперь выберите кинотеатр:',
                                                   reply_markup=await ikb_cinemas(cinemas=all_cinemas_titles,
                                                                                  all_cinemas_titles=all_cinemas_titles))


@dp.callback_query(F.data.startswith('next_cinema'))
async def next_cinemas_page_cb(callback_query: CallbackQuery):
    cb_data = callback_query.data.split('_')
    page = int(cb_data[2])

    await callback_query.message.edit_reply_markup(reply_markup=await ikb_cinemas(cinemas=all_cinemas_titles,
                                                                                  all_cinemas_titles=all_cinemas_titles,
                                                                                  current_page=page))


@dp.callback_query(F.data.startswith('cinema'))
async def cinema_cb(callback_query: CallbackQuery):
    cb_data = callback_query.data.split('_')
    cinema_index = int(cb_data[1])
    user_cinema = all_cinemas_titles[cinema_index]
    selected_user_cinema[callback_query.from_user.id] = user_cinema
    user_date = selected_user_date.get(callback_query.from_user.id)
    user_movie = selected_user_movie.get(callback_query.from_user.id)

    if user_date:
        movie_and_showtime = get_movies_and_showtime(schedule_data_from_list1, user_cinema, user_date)
        await send_movie_schedule(callback_query, movie_and_showtime, user_date, user_cinema, all_movies_titles)
        await clear_user_selections(callback_query.from_user.id)

    elif user_movie:
        date_and_time = schedule_data_from_list1.get(user_cinema).get(user_movie)
        if date_and_time:

            showtime_list = []
            day = None

            for item in date_and_time:
                if day == item.strftime('%d.%m.%Y'):
                    showtime_list.append(item.strftime('%H:%M'))
                elif day is None:
                    day = item.strftime('%d.%m.%Y')
                    showtime_list.append(item.strftime('%H:%M'))
                else:
                    await callback_query.message.answer(text=f'Кинотеатр: "{user_cinema}"\n'
                                                             f'Фильм: "{user_movie}"\n'
                                                             f'Дата: {day}\n'
                                                             f'Время сеансов: {", ".join(showtime_list)}')
                    showtime_list.clear()
                    day = item.strftime('%d.%m.%Y')
                    showtime_list.append(item.strftime('%H:%M'))

            if day is not None and showtime_list:
                await callback_query.message.answer(text=f'Кинотеатр: "{user_cinema}"\n'
                                                         f'Фильм: "{user_movie}"\n'
                                                         f'Дата: {day}\n'
                                                         f'Время сеансов: {", ".join(showtime_list)}')
            return
        await callback_query.message.answer(text=f'К сожалению, фильм "{user_movie}" в настоящее время не представлен в кинотеатре "{user_cinema}".')
        await clear_user_selections(callback_query.from_user.id)
    else:
        await callback_query.message.edit_text(text='Теперь выберите дату:',
                                               reply_markup=await SimpleCalendar().start_calendar())


@dp.callback_query(F.data.startswith('movie'))
async def movie_cb(callback_query: CallbackQuery):
    cb_data = callback_query.data.split('_')
    movie_ind = int(cb_data[1])
    user_movie = all_movies_titles[movie_ind]

    selected_user_movie[callback_query.from_user.id] = user_movie

    await callback_query.message.answer(text=user_movie)

    for description, params in schedule_data_from_list2[user_movie].items():
        await callback_query.message.answer(text=description)

        text = ''
        for param in params:
            text += param + '\n'
        await callback_query.message.answer(text=text)

    if not selected_user_cinema.get(callback_query.from_user.id) and not selected_user_date.get(callback_query.from_user.id):
        await callback_query.message.answer(text='Дата✅ - для выбора даты сеанса.\n'
                                                 'Кинотеатр✅ - для выбора кинотеатра.',
                                            reply_markup=start_kb)


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
