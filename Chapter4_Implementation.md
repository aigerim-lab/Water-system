# Chapter 4 — Implementation (Frontend & Product)

## 4.1 User Interface
The software product is implemented as an interactive web application using Streamlit.  
The interface is designed for non-technical users and includes a sidebar for filtering and a main dashboard for visual analytics.  
The product also includes light/dark theme control and a structured layout with fixed navigation, KPI cards, and chart containers.

Implemented filters:
- Region
- Year
- Indicator (Pollutant)

## 4.2 Dashboard Structure
The dashboard includes core visual blocks:

1. Kazakhstan choropleth map (regional average WQI)
2. Line chart for yearly trend analysis
3. Bar chart for cross-regional comparison
4. Prediction chart with linear regression forecast

Additional KPI cards are displayed at the top:
- total records
- mean WQI
- mean MPC ratio
- high-risk share

Additional analytical blocks:
- Risk Alerts module
- Top Risk Regions table
- Compare Mode (Region/Period A vs Region/Period B)

## 4.3 Visualization and Interactivity
Plotly is used to render interactive charts.  
Users can hover, zoom, and inspect chart values dynamically.  
All charts react to selected filters, enabling focused analysis by region, year, and indicator.  
The selected dashboard state is preserved on refresh via URL query parameters, ensuring reproducibility of the selected analytical view.

## 4.4 Risk Monitoring and Comparative Analysis
The implemented Risk Alerts block automatically identifies:
- high-risk observations (Ratio > 2),
- moderate-risk observations (1 <= Ratio <= 2),
- regional risk concentration through ranked summary tables.

The Compare Mode supports side-by-side comparison between two selected region-period combinations and computes:
- delta of mean WQI,
- delta of mean Ratio,
- delta of high-risk share.

This module helps transform visual analysis into practical decision support.

## 4.5 Machine Learning Evaluation
The prediction module uses a baseline linear regression model for yearly forecasting (WQI or Concentration).  
For transparent model quality assessment, the dashboard computes and displays:
- R² coefficient,
- MAE (Mean Absolute Error),
- RMSE (Root Mean Squared Error).

This allows users to interpret not only forecast values, but also confidence and fit quality.

## 4.6 Export Functionality
Two export features are implemented:
- CSV export of filtered records
- PNG export of selected chart

This supports reporting, presentation, and external analysis workflows.

## 4.7 Technical Notes
- Main frontend file: `app.py`
- Dataset: `db/Kazakhstan_Water_Pollution_Dataset.csv`
- Start command: `streamlit run app.py`
- Dependencies: listed in `requirements.txt`
