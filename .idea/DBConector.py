import geopandas as gpd
import psycopg2
from sqlalchemy import create_engine

# Завантажуємо GeoJSON із кордоном України
geojson_path = "C://Users//Device//Desktop//geoBoundaries-UKR-ADM0-all//geoBoundaries-UKR-ADM0.geojson"
gdf = gpd.read_file(geojson_path)

# Підключення до PostgreSQL
engine = create_engine('postgresql+psycopg2://postgres:07072003@localhost:5432/UkraineDatabase')

# Завантаження даних у таблицю PostgreSQL
gdf.to_postgis('ukraine_border', engine, if_exists='replace')
