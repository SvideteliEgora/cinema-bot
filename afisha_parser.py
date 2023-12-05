import requests
from bs4 import BeautifulSoup
from datetime import datetime
import locale
import gspread


def update_data():
    month_dict = {
        "января": "январь",
        "февраля": "февраль",
        "марта": "март",
        "апреля": "апрель",
        "мая": "май",
        "июня": "июнь",
        "июль": "июля",
        "августа": "август",
        "сентября": "сентябрь",
        "октября": "октябрь",
        "ноября": "ноябрь",
        "декабря": "декабрь",
    }

    locale.setlocale(locale.LC_ALL, "ru_RU")

    current_date_time = datetime.now()

    url = "https://afisha.relax.by/kino/minsk/"

    resp = requests.get(url)

    soup = BeautifulSoup(resp.text, "html.parser")

    link_list = []
    dt_list1 = []

    days = soup.find_all("div", class_="schedule__list")
    for day in days:
        day_t = day.find("h5").text.strip().split(",")
        day_t = day_t[0].split()
        day_t[1] = month_dict.get(day_t[1])
        day_t = " ".join(day_t)

        cinema = None
        for st in day.find_all("div", class_="schedule__table--movie__item"):
            try:
                string = st.find("a", class_="schedule__place-link link").text.strip()
                cinema = "".join(char for char in string if char.isprintable())
            except:
                pass
            film = st.find("a", class_="schedule__event-link link")
            link_list.append(film.get("href"))
            film = film.text.strip().replace("  ", "")
            buf = [film, cinema]
            for t in st.find_all("a", class_="schedule__seance-time"):
                date_string = f"{day_t} {2023} {t.text.strip()}"
                parsed_date_time = datetime.strptime(date_string, "%d %B %Y %H:%M")
                if parsed_date_time < current_date_time:
                    parsed_date_time = parsed_date_time.replace(
                        year=current_date_time.year + 1
                    )
                unix_timestamp = str(parsed_date_time.timestamp())
                buf.append(unix_timestamp)
            dt_list1.append(buf)

    link_list = list(set(link_list))

    dt_list2 = []

    for link in link_list:
        resp = requests.get(link)

        soup = BeautifulSoup(resp.text, "html.parser")

        try:
            title = soup.find(
                "h1", class_="b-afisha-layout-theater_movie-title"
            ).text.strip()
            desc = (
                soup.find("div", class_="b-afisha_cinema_description_text")
                .find("p")
                .text.strip()
                .replace("\n", "")
                .replace("\xa0", "")
            )
            buf = [title, desc]
            desc_params = soup.find(
                "div", class_="b-afisha_cinema_description_table"
            ).find_all("li")
        except Exception as e:
            print(f"{link}: {e}")
            continue

        for param in desc_params:
            param_text = param.text
            param_cleaned_text = "  ".join(param_text.split())
            buf.append(param_cleaned_text)

        dt_list2.append(buf)

    gc = gspread.service_account(filename="venv\\true-sprite-405907-da4b97639184.json")

    sht = gc.open_by_url(
        "https://docs.google.com/spreadsheets/d/12ccv7iv0kmbs8i2sbFy7FX6gETAc5_r2kAx1AoAVvu8/edit#gid=0"
    )

    worksheet1 = sht.get_worksheet(0)
    worksheet1.update("A1:Z" + str(len(dt_list1)), dt_list1)

    # worksheet2 = sht.add_worksheet("Лист2", rows=100, cols=26)
    worksheet2 = sht.get_worksheet(1)
    worksheet2.update("A1:Z" + str(len(dt_list2)), dt_list2)
