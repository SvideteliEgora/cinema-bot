from datetime import datetime


def get_movies(schedule_data: dict[dict[str]], cinema: str, user_date: datetime) -> tuple:
    """
    Get the schedule of movies and their show times for a given cinema and user datetime.

    :param schedule_data: A dictionary representing the movie schedule data.
    :param cinema: The name of the cinema.
    :param user_date: The user date.
    :return: A list of movie titles with show times within the user's date.
    """
    movies_for_cinema = schedule_data.get(cinema, {})
    movies_titles = []

    for movie, date_times in movies_for_cinema.items():
        low = 0
        high = len(date_times) - 1
        while low <= high:
            mid = (low + high) // 2
            guess_date = datetime.date(date_times[mid])

            if guess_date == user_date:
                movies_titles.append(movie)
                break
            elif guess_date > user_date:
                high = mid - 1
            else:
                low = mid + 1

    return tuple(movies_titles)


def get_indexes(all_titles: list | tuple, title_for_indexes: list | tuple) -> list | tuple:
    indexes = []
    for title in title_for_indexes:
        indexes.append(all_titles.index(title))

    return tuple(indexes)
