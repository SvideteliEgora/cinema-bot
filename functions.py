from datetime import datetime


def unique_titles(list_to_list: list[list], element_index: int) -> tuple:
    """
    Extracts unique cinemas names from a 2D list of movie, cinema, and time data.

    :param list_to_list: 2D list with movie, cinema, and time data.
    :return: tuple of unique cinemas names
    """
    elements = []

    for item in list_to_list:
        elements.append(item[element_index])

    return tuple(set(elements))


def convert_to_movie_schedule(list_to_list: list[list]) -> dict:
    """
    Transforms a two-dimensional list with movie, cinema, and time data into a dictionary structure.

    :param list_to_list: Two-dimensional list with movie, cinema, and time information.
    :return: Dictionary structure {cinema: {movie: [time]}}
    """
    data = {}
    for lst_of_movies in list_to_list:
        cinema = lst_of_movies[1]
        if cinema not in data:
            data[cinema] = {}

        film = lst_of_movies[0]
        if film not in data[cinema]:
            data[cinema][film] = []

        for dt in lst_of_movies[2:]:
            if dt != '':
                data[cinema][film].append(datetime.fromtimestamp(float(dt)))

    return data


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


def convert_to_movie_schedule_from_list2(list_to_list: list[list]) -> dict:
    """
    Transforms a two-dimensional list with movie, cinema, and time data into a dictionary structure.

    :param list_to_list: Two-dimensional list with movie, cinema, and time information.
    :return: Dictionary structure {movie: {description: [params]}}
    """
    data = {}
    for lst_of_movies in list_to_list:
        movie = lst_of_movies[0]
        if movie not in data:
            data[movie] = {}

        description = lst_of_movies[1]
        if description not in data[movie]:
            data[movie][description] = []

        for param in lst_of_movies[2:]:
            if param != '':
                data[movie][description].append(param)

    return data


def dict_cleaner(selected_user_cinema: dict, selected_user_date: dict, user_id: int) -> None:
    try:
        del selected_user_cinema[user_id]
        del selected_user_date[user_id]
    except KeyError:
        pass


def get_indexes(all_titles: list | tuple, title_for_indexes: list | tuple) -> list | tuple:
    indexes = []
    for title in title_for_indexes:
        indexes.append(all_titles.index(title))

    return tuple(indexes)