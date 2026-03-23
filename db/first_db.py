import plotly.express as px
import pandas as pd
import json

# Load your dataset into a pandas DataFrame
df = pd.read_csv('Kazakhstan_Water_Pollution_Dataset.csv')  # Make sure to use the correct file path

# Load the geojson file
with open('kz.json', 'r') as f:
    geojson = json.load(f)


# Create the choropleth map
fig = px.choropleth(
    df,  # Your loaded DataFrame
    geojson=geojson,  # Loaded GeoJSON file
    locations='Region',  # Column with region names in your DataFrame
    featureidkey="properties.name",  # Key in the GeoJSON file to match region names
    color='WQI_Score',  # The value column used for coloring
    color_continuous_scale="RdYlGn_r",  # Color scale from red to green
    title="Water Quality Index by Region"
)

fig.show()
