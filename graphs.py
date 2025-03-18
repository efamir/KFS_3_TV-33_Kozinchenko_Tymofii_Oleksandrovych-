import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
from sqlalchemy import create_engine
from uuid import uuid4
import os

# Глобальна змінна для зберігання списку міст.  Ініціалізується в get_data().
cities = None


def get_data():
    """
    Отримує дані про погоду з бази даних PostgreSQL.
    """
    global cities  # Використовуємо глобальну змінну cities

    # З'єднання з базою даних
    engine = create_engine('postgresql://test_user:test@localhost:5432/winds_db')
    # Запит на отримання всіх даних
    query = "SELECT * FROM winds_data"
    # Зчитування даних у DataFrame
    data = pd.read_sql(query, engine)
    # Отримання списку унікальних міст і збереження в глобальну змінну
    cities = pd.read_sql("SELECT DISTINCT location_name FROM winds_data", engine)['location_name'].tolist()

    return data

# Отримання даних при запуску модуля. Змінна data буде доступна в глобальній області видимості.
data = get_data()


def generate_plots(selected_location=None):
    """
    Генерує набір графіків, що аналізують дані про вітер.
    """
    # Аналіз впливу вітру на температуру
    wind_temperature_effects = analyze_wind_temperature_effect(data, selected_location)
    # Список шляхів до всіх графіків
    imgs_links = [plot_wind_power(data, selected_location), plot_average_wind_by_day_of_year(data, selected_location),
                  wind_temperature_effects[0], wind_temperature_effects[1]]

    return imgs_links


def plot_wind_power(data, location=None):
    """
    Будує графік швидкості вітру за часом.
    """
    # Фільтруємо викиди (швидкість вітру > 60 км/год)
    data = data[data['wind_kph'] <= 60].copy()

    # Фільтруємо дані за локацією, якщо вона вказана
    if location:
        data = data[data['location_name'] == location].copy()

    # Обчислюємо середню швидкість вітру
    mean_wind = data['wind_kph'].mean()

    # Будуємо графік
    plt.figure(figsize=(14, 7))
    plt.plot(data['last_updated'], data['wind_kph'],
             label=f'Швидкість вітру {"(" + location + ")" if location else ""}', color='blue', linewidth=1, alpha=0.5)
    # Лінія середньої швидкості
    plt.axhline(y=mean_wind, color='orange', linestyle='-',
                label=f'Середня швидкість ({mean_wind:.1f} км/год)')
    # Лінії для позначення сильного та слабкого вітру
    plt.axhline(y=20, color='red', linestyle='--', label='Сильний вітер (>20 км/год)')
    plt.axhline(y=10, color='green', linestyle='--', label='Слабкий вітер (<10 км/год)')

    # Налаштування графіка
    plt.title(f'Швидкість вітру за часом {"(" + location + ")" if location else ""}', fontsize=14)
    plt.xlabel('Дата і час', fontsize=12)
    plt.ylabel('Швидкість вітру (км/год)', fontsize=12)
    plt.xticks(rotation=45)  # Поворот підписів на осі X
    plt.grid(True, linestyle='--', alpha=0.7)  # Сітка
    plt.legend()  # Легенда
    plt.tight_layout()  # Автоматичне коригування розміщення елементів

    # Генеруємо унікальну назву файлу
    filename = f"{uuid4()}.png"
    filepath = os.path.join('static', 'img', filename)
    # Зберігаємо графік у файл
    plt.savefig(filepath)
    plt.close()  # Закриваємо фігуру, щоб звільнити пам'ять

    return os.path.join('img', filename)  # Повертаємо відносний шлях


def plot_average_wind_by_day_of_year(data, location=None, frac=0.2):
    """
    Будує графік середньої швидкості вітру по днях року, усередненої за всі роки,
    з використанням зглажування LOESS для плавної кривої.
    """
    # Фільтруємо викиди
    data = data[data['wind_kph'] <= 60].copy()

    # Фільтруємо дані за локацією
    if location:
        data = data[data['location_name'] == location].copy()

    # Додаємо стовпець із номером дня в році (1-365/366)
    data['day_of_year'] = data['last_updated'].dt.dayofyear

    # Групуємо за днем року та обчислюємо середню швидкість вітру за всі роки
    daily_average = data.groupby('day_of_year')['wind_kph'].mean()

    # Застосовуємо LOESS для згладжування
    loess = sm.nonparametric.lowess(daily_average.values, daily_average.index, frac=frac)

    # Побудова графіка
    plt.figure(figsize=(14, 6))
    plt.plot(loess[:, 0], loess[:, 1], color='royalblue', linewidth=2)  # Згладжена крива
    plt.title(f'Середня швидкість вітру по днях року (усереднена за всі роки) - {location}')
    plt.xlabel('День року')
    plt.ylabel('Середня швидкість вітру (км/год)')
    plt.axhline(y=20, color='red', linestyle='--', label='Сильний вітер (>20 км/год)')
    plt.axhline(y=10, color='green', linestyle='--', label='Слабкий вітер (<10 км/год)')

    # Додаємо позначки для місяців (приблизно)
    month_starts = [1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335]
    month_names = ['Січ', 'Лют', 'Бер', 'Квіт', 'Трав', 'Черв', 'Лип', 'Серп', 'Вер', 'Жовт', 'Лист', 'Груд']
    plt.xticks(month_starts, month_names)  # Мітки місяців на осі X

    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend()
    plt.tight_layout()

    # Генеруємо унікальну назву файлу
    filename = f"{uuid4()}.png"
    filepath = os.path.join('static', 'img', filename)
    plt.savefig(filepath)
    plt.close()

    return os.path.join('img', filename)


def analyze_wind_temperature_effect(data, location=None, frac=0.5):
    """
    Аналізує вплив швидкості вітру на температуру та відчуття температури з додаванням усередненої лінії.
    """
    # Фільтруємо викиди
    data = data[data['wind_kph'] <= 60].copy()

    # Фільтруємо дані за локацією
    if location:
        data = data[data['location_name'] == location].copy()

    # Обчислюємо різницю між реальною температурою та відчуттям
    data.loc[:, 'temp_difference'] = data['feels_like_celsius'] - data['temperature_celsius']

    # Графік 1: Залежність швидкості вітру від різниці в температурі
    plt.figure(figsize=(14, 6))
    plt.scatter(data['wind_kph'], data['temp_difference'], alpha=0.3, color='purple', label='Дані')

    # Додаємо усереднену лінію (LOESS)
    loess_temp_diff = sm.nonparametric.lowess(data['temp_difference'], data['wind_kph'], frac=frac)
    plt.plot(loess_temp_diff[:, 0], loess_temp_diff[:, 1], color='orange', linewidth=2, label='Тенденція (LOESS)')

    # Додаткові лінії та налаштування
    plt.axhline(y=-2, color='red', linestyle='--', label='Холодніше на 2°C')
    plt.axhline(y=2, color='green', linestyle='--', label='Тепліше на 2°C')
    plt.title(f'Вплив швидкості вітру на відчуття температури {"(" + location + ")" if location else ""}')
    plt.xlabel('Швидкість вітру (км/год)')
    plt.ylabel('Різниця відчуття температури (°C)')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend()
    plt.tight_layout()

    # Генеруємо унікальну назву файлу
    filename1 = f"{uuid4()}.png"
    filepath1 = os.path.join('static', 'img', filename1)
    plt.savefig(filepath1)
    plt.close()

    # Графік 2: Залежність температури від швидкості вітру
    plt.figure(figsize=(14, 6))
    plt.scatter(data['wind_kph'], data['temperature_celsius'], alpha=0.3, color='blue', label='Дані')

    # Додаємо усереднену лінію (LOESS)
    loess_temp = sm.nonparametric.lowess(data['temperature_celsius'], data['wind_kph'], frac=frac)
    plt.plot(loess_temp[:, 0], loess_temp[:, 1], color='orange', linewidth=2, label='Тенденція (LOESS)')

    # Налаштування другого графіка
    plt.title(f'Залежність температури від швидкості вітру {"(" + location + ")" if location else ""}')
    plt.xlabel('Швидкість вітру (км/год)')
    plt.ylabel('Температура (°C)')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend()
    plt.tight_layout()

    # Генеруємо унікальну назву файлу
    filename2 = f"{uuid4()}.png"
    filepath2 = os.path.join('static', 'img', filename2)
    plt.savefig(filepath2)
    plt.close()

    return os.path.join('img', filename1), os.path.join('img', filename2) # Повертаємо шляхи до обох графіків
