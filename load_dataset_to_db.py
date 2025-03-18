from sqlalchemy import create_engine
import pandas as pd


def load_data_to_db():
    data = pd.read_csv("GlobalWeatherRepository.csv")

    selected_columns = ['last_updated', 'wind_kph', 'temperature_celsius', 'feels_like_celsius', 'location_name']

    data = data[selected_columns]  # вибираємо лише потрібні колонки
    data["last_updated"] = pd.to_datetime(data["last_updated"])  # типизуємо last_update у datetime

    # Підключення до PostgreSQL
    engine = create_engine('postgresql://test_user:test@localhost:5432/winds_db')

    # Завантаження даних у таблицю
    data.to_sql('winds_data', engine, if_exists='replace', index=False)



if __name__ == "__main__":
    load_data_to_db()
