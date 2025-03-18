CREATE TABLE winds_data (
    id SERIAL PRIMARY KEY,
    last_updated TIMESTAMP,
    wind_kph FLOAT,
    temperature_celsius FLOAT,
    feels_like_celsius FLOAT,
    location_name VARCHAR(100)
);