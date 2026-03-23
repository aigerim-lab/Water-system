import pandas as pd
import plotly.express as px
import os

# 1. Исправляем путь: поднимаемся на уровень выше и заходим в папку db
# Это сработает, даже если ты запускаешь скрипт из папки visualization
file_path = os.path.join("..", "db", "Kazakhstan_Water_Pollution_Dataset.xlsx")

try:
    df = pd.read_excel(file_path)
    
    # 2. Создаем колонку 'Year' из колонки 'Date'
    df['Date'] = pd.to_datetime(df['Date'])
    df['Year'] = df['Date'].dt.year

    # 3. Группируем по году
    trend = df.groupby("Year")["WQI_Score"].mean().reset_index()

    # 4. Строим график
    fig = px.line(
        trend,
        x="Year",
        y="WQI_Score",
        markers=True,
        title="Average Water Quality Index Over Time in Kazakhstan"
    )

    fig.show()

except FileNotFoundError:
    print(f"Ошибка: Файл не найден по пути {file_path}")
    print("Проверь, что папка db находится рядом с папкой visualization.")