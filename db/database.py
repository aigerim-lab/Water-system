import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

# Настройки для генерации
n_rows = 520
basins = ['Aralo-Syrdarya', 'Balkash-Alakol', 'Ertis', 'Esil', 'Nura-Sarysu', 'Zhaiyk-Kaspian', 'Tobyl-Torgay', 'Shu-Talas']
regions = ['Kyzylorda', 'Almaty', 'VKO', 'Akmoal', 'Karaganda', 'Atyrau', 'Kostanay', 'Zhambyl']
pollutants = {
    'Nitrates': [45.0, 1], # [ПДК, Класс опасности]
    'Copper': [0.001, 2],
    'Sulfates': [500.0, 4],
    'Zinc': [0.01, 3],
    'Phenols': [0.001, 2],
    'Oil Products': [0.05, 3]
}

data = []

for i in range(n_rows):
    date = datetime(2020, 1, 1) + timedelta(days=random.randint(0, 1500))
    basin_idx = random.randint(0, len(basins)-1)
    p_name = random.choice(list(pollutants.keys()))
    mpc = pollutants[p_name][0]
    
    # Генерация концентрации (иногда выше ПДК, иногда ниже)
    conc = round(random.uniform(0.1 * mpc, 3.0 * mpc), 4)
    wqi = round((conc / mpc) * 50 + random.randint(10, 30), 1) # Имитация WQI
    
    data.append([
        i + 1, date.strftime('%Y-%m-%d'), basins[basin_idx], 
        regions[basin_idx], p_name, conc, mpc, 
        wqi, pollutants[p_name][1]
    ])

df = pd.DataFrame(data, columns=['ID', 'Date', 'Basin', 'Region', 'Pollutant', 'Concentration', 'MPC', 'WQI_Score', 'Hazard_Class'])

# Сохранение в Excel
df.to_excel("Kazakhstan_Water_Pollution_Dataset.xlsx", index=False)
print("Файл Kazakhstan_Water_Pollution_Dataset.xlsx успешно создан!")