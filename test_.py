# test_app.py
import pytest
from app import app  # Імпортуємо Flask-додаток
from graphs import get_data, generate_plots, cities, plot_wind_power, plot_average_wind_by_day_of_year, analyze_wind_temperature_effect  # Імпортуємо функції з graphs.py
import os
import pandas as pd
from unittest.mock import patch, MagicMock
import shutil


# 1. Health Check: Зв'язок з базою даних
def test_database_connection():
    """Перевірка підключення до БД."""
    try:
        data = get_data()
        assert data is not None
        assert isinstance(data, pd.DataFrame)
        assert not data.empty
        assert cities is not None
        assert len(cities) > 0
    except Exception as e:
        pytest.fail(f"Помилка підключення до БД: {e}")


# 2. Health Check: Flask-додаток (базові тести)
@pytest.fixture
def client():
    """Фікстура для створення тестового клієнта Flask."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index_route(client):
    """Перевірка головної сторінки."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Kyiv' in response.data # перевірка наявності тексту

def test_index_route_with_location(client):
    """Перевірка головної сторінки з параметром локації."""
    response = client.get('/?location=Kyiv')
    assert response.status_code == 200
    assert b'<img' in response.data


# 3. Health Check & Sanity: Генерація графіків (базові перевірки)
def test_generate_plots_no_location():
    """Перевірка генерації графіків без вказання локації (ALL)."""
    try:
        imgs = generate_plots()
        assert imgs is not None
        assert isinstance(imgs, list)
        assert len(imgs) == 4  # Очікуємо 4 графіки
        for img_path in imgs:
            assert os.path.exists(os.path.join('static', img_path))
    except Exception as e:
        pytest.fail(f"Помилка генерації графіків: {e}")


def test_generate_plots_with_location():
    """Перевірка генерації графіків з вказанням локації."""
    try:
        imgs = generate_plots(cities[0]) # Беремо першу локацію зі списку
        assert imgs is not None
        assert isinstance(imgs, list)
        assert len(imgs) == 4
        for img_path in imgs:
            assert os.path.exists(os.path.join('static', img_path))

    except Exception as e:
        pytest.fail(f"Помилка генерації графіків з локацією: {e}")


# 4. Sanity: Тести окремих функцій побудови графіків
@patch('matplotlib.pyplot.show')  # Мокаємо plt.show, щоб графіки не відображались
@patch('matplotlib.pyplot.savefig') # i plt.savefig
def test_plot_wind_power(mock_savefig, mock_show):
    """Sanity-тест для plot_wind_power."""
    data = pd.DataFrame({
        'last_updated': pd.to_datetime(['2025-01-01', '2025-01-02', '2025-01-03']),
        'wind_kph': [10, 20, 15],
        'location_name': ['TestCity', 'TestCity', 'TestCity']
    })
    result = plot_wind_power(data, 'TestCity')
    assert isinstance(result, str)  # Перевіряємо, чи повертається рядок (шлях до файлу)
    assert result.endswith('.png')


@patch('matplotlib.pyplot.show')
@patch('matplotlib.pyplot.savefig')
def test_plot_average_wind_by_day_of_year(mock_savefig, mock_show):
    """Sanity-тест для plot_average_wind_by_day_of_year."""
    data = pd.DataFrame({
        'last_updated': pd.to_datetime(['2024-01-01', '2024-01-02', '2024-01-03']),
        'wind_kph': [10, 20, 15],
        'location_name': ['TestCity', 'TestCity', 'TestCity']
    })
    data['day_of_year'] = data['last_updated'].dt.dayofyear
    result = plot_average_wind_by_day_of_year(data, 'TestCity')
    assert isinstance(result, str)
    assert result.endswith('.png')


@patch('matplotlib.pyplot.show')
@patch('matplotlib.pyplot.savefig')
def test_analyze_wind_temperature_effect(mock_savefig, mock_show):
    """Sanity-тест для analyze_wind_temperature_effect."""
    data = pd.DataFrame({
        'wind_kph': [10, 20, 15],
        'temperature_celsius': [20, 18, 19],
        'feels_like_celsius': [18, 15, 17],
        'location_name': ['TestCity', 'TestCity', 'TestCity']
    })
    data['temp_difference'] = data['feels_like_celsius'] - data['temperature_celsius']
    result = analyze_wind_temperature_effect(data, 'TestCity')
    assert isinstance(result, tuple)  # Перевіряємо, чи повертається кортеж
    assert len(result) == 2  # Очікуємо два шляхи до файлів
    assert result[0].endswith('.png')
    assert result[1].endswith('.png')


# Фікстура, яка буде видаляти теку 'static/img' після всіх тестів
@pytest.fixture(scope="session", autouse=True)
def cleanup_images_after_all_tests():
    """Видаляє теку з зображеннями після всіх тестів."""
    yield  # Тут виконуються всі тести
    if os.path.exists('static/img'):
        shutil.rmtree('static/img')
