import geopandas as gpd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine
from shapely.geometry import Point, Polygon
import pandas as pd

# Підключення до бази даних
engine = create_engine('postgresql+psycopg2://postgres:07072003@localhost:5432/UkraineDatabase')

# Завантаження меж України
gdf = gpd.read_postgis(
    "SELECT * FROM ukraine_border",
    con=engine,
    geom_col='geometry'
)

# Параметри сітки (10 км ≈ 0.09° широти, 0.14° довготи)
min_lat, max_lat = 42.38, 52.37  # Межі широти
min_lon, max_lon = 22.13, 40.23  # Межі довготи
delta_lat, delta_lon = 0.09, 0.14  # Кроки сітки (10×10 км)

# Генерація квадратів
polygons = []
vertices = set()  # Використовуємо множину для зберігання унікальних вершин
lat = max_lat
while lat > min_lat:
    lon = min_lon
    while lon < max_lon:
        # Створення квадрата 10×10 км
        square = Polygon([
            (lon, lat),
            (lon + delta_lon, lat),
            (lon + delta_lon, lat - delta_lat),
            (lon, lat - delta_lat)
        ])
        polygons.append(square)

        # Додавання вершин квадрата до множини
        vertices.update([(lon, lat), (lon + delta_lon, lat),
                         (lon + delta_lon, lat - delta_lat),
                         (lon, lat - delta_lat)])

        lon += delta_lon  # Зміщення довготи
    lat -= delta_lat  # Зміщення широти

# Створення GeoDataFrame з квадратами
grid = gpd.GeoDataFrame({'geometry': polygons}, crs="EPSG:4326")

# Перетин сітки з територією України
grid = gpd.overlay(grid, gdf, how='intersection')

# Зберігання унікальних вершин у базі даних
vertices_gdf = gpd.GeoDataFrame(list(vertices), columns=['longitude', 'latitude'],
                                geometry=gpd.points_from_xy(*zip(*vertices)), crs="EPSG:4326")

vertices_filtered = gpd.overlay(vertices_gdf, gdf, how='intersection')

# Запис унікальних вершин у базу даних
vertices_filtered.to_postgis(name='grid_vertices', con=engine, if_exists='replace', index=False)

# Відображення результату
fig, ax = plt.subplots(figsize=(10, 10))
gdf.boundary.plot(ax=ax, color='black', linewidth=1)  # Кордон України
grid.plot(ax=ax, color='lightblue', alpha=0.5, edgecolor='grey')  # Квадрати
plt.title('Сітка квадратів на карті України (10 км × 10 км)', fontsize=16)
plt.show()
