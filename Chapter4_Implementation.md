# Chapter 4 — Implementation (Frontend & Product)

## 4.1 User Interface
The software product is implemented as an interactive web application using Streamlit.  
The interface is designed for non-technical users and includes a sidebar for filtering and a main dashboard for visual analytics.

Implemented filters:
- Region
- Year
- Indicator (Pollutant)

## 4.2 Dashboard Structure
The dashboard includes four required visual blocks:

1. Kazakhstan choropleth map (regional average WQI)
2. Line chart for yearly trend analysis
3. Bar chart for cross-regional comparison
4. Prediction chart with linear regression forecast

Additional KPI cards are displayed at the top:
- total records
- mean WQI
- mean MPC ratio
- high-risk share

## 4.3 Visualization and Interactivity
Plotly is used to render interactive charts.  
Users can hover, zoom, and inspect chart values dynamically.  
All charts react to selected filters, enabling focused analysis by region, year, and indicator.

## 4.4 Export Functionality
Two export features are implemented:
- CSV export of filtered records
- PNG export of selected chart

This supports reporting, presentation, and external analysis workflows.

## 4.5 Technical Notes
- Main frontend file: `app.py`
- Dataset: `db/Kazakhstan_Water_Pollution_Dataset.csv`
- Start command: `streamlit run app.py`
- Dependencies: listed in `requirements.txt`
