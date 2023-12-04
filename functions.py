from datetime import datetime


def get_movies_and_showtime(schedule_data: dict[dict[str]], cinema: str, user_date: datetime) -> tuple:
    movies_for_cinema = schedule_data.get(cinema, {})
    movies_titles = []

    for movie, dt in movies_for_cinema.items():
        if dt:
            if user_date == datetime.date(dt[0]):
                showtime_list = []
                for item in dt:
                    showtime_list.append(item.strftime('%H:%M'))
                movies_titles.append({movie: showtime_list})

    return tuple(movies_titles)


def get_cinemas(schedule_data: dict[dict[str]], movie_title: str, user_date: datetime) -> tuple:
    cinemas = []
    for cinema, movie_and_time in schedule_data:
        for movie, time in movie_and_time:
            if movie == movie_title:
                date_and_time = []
                for i in time:
                    if datetime.date(i) == user_date:
                        date_and_time.append(i)
                cinemas.append({cinema: date_and_time})

    return tuple(cinemas)


def get_indexes(all_titles: list | tuple, title_for_indexes: list | tuple) -> list | tuple:
    indexes = []
    for title in title_for_indexes:
        indexes.append(all_titles.index(title))

    return tuple(indexes)
