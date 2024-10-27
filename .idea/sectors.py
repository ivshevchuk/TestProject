import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from sqlalchemy import create_engine
from shapely.geometry import Point, Polygon

# Підключення до бази даних
engine = create_engine('postgresql+psycopg2://postgres:07072003@localhost:5432/UkraineDatabase')

# Завантаження вершин квадратів з бази даних
vertices_gdf = gpd.read_postgis("SELECT * FROM grid_vertices", con=engine, geom_col='geometry')

# Параметри секторів
azimuths = [0, 120, 240]
angle_span = 60  # градусів
radius = 8 / 110.574

# Функція для генерації сектору
def generate_sector(center, azimuth, radius, angle_span):
    # Створюємо точки сектора
    angles = np.linspace(azimuth - angle_span / 2, azimuth + angle_span / 2, 100)
    points = [Point(center.x + radius * np.cos(np.radians(a)), center.y + radius * np.sin(np.radians(a))) for a in angles]

    # Додаємо крайні точки та закриваємо сектор
    sector_polygon = Polygon([center] + points)
    return sector_polygon

# Перетин секторів з вершинами
intersections = []

# Створення просторового індексу для швидкого доступу до вершин
sindex = vertices_gdf.sindex

# Генерація секторів для кожної вершини
for idx, row in vertices_gdf.iterrows():
    vertex_point = row.geometry
    for azimuth in azimuths:
        sector = generate_sector(vertex_point, azimuth, radius, angle_span)

        # Використовуємо межі сектора для пошуку можливих перетинів
        possible_matches_index = list(sindex.intersection(sector.bounds))
        possible_matches = vertices_gdf.iloc[possible_matches_index]

        # Перевірка перетину з можливими вершинами
        for square_idx, square_row in possible_matches.iterrows():
            if sector.intersects(square_row.geometry):
                intersections.append({
                    'vertex_id': idx,
                    'square_vertex_id': square_idx,
                    'sector': sector
                })

ukraine_map = gpd.read_postgis(
    "SELECT * FROM ukraine_border",
    con=engine,
    geom_col='geometry'
)

# Перетворення даних у GeoDataFrame
intersections_gdf = gpd.GeoDataFrame(
    {
        'vertex_id': [item['vertex_id'] for item in intersections],
        'square_vertex_id': [item['square_vertex_id'] for item in intersections],
        'sector': [item['sector'] for item in intersections]
    },
    geometry='sector',  # Вказуємо, що поле 'sector' є геометричним
    crs="EPSG:4326"
)

# Збереження перетинів в базу даних
intersections_gdf.to_postgis(name='sector_intersections', con=engine, if_exists='replace', index=False)


# Візуалізація результату
fig, ax = plt.subplots(figsize=(10, 10))
vertices_gdf.plot(ax=ax, color='red', markersize=10)  # Вершини

intersections_gdf.plot(ax=ax, color='pink', linewidth=1, alpha=0.3);

ukraine_map.boundary.plot(ax=ax, color='black', linewidth=1)  # Кордон України
plt.title('Сектори на карті квадратів з перетинами', fontsize=16)
plt.legend()
plt.show()
