# Water Pollution Analysis in Kazakhstan

This project is a bachelor’s thesis prototype focused on analyzing and visualizing water pollution levels in Kazakhstan using open environmental data.

## Current Progress

At the current stage, the project includes:

- collection and preprocessing of water pollution data
- processed dataset with 500+ records
- calculation and validation of analytical indicators:
  - concentration
  - maximum permissible concentration (MPC)
  - Water Quality Index (WQI)
  - hazard classification
- baseline machine learning model for WQI trend forecasting
- initial analytical visualizations

## Project Structure


## Dataset Fields

- The processed dataset contains the following columns:

 - ID
 - Date
 - Basin
 - Region
 - Pollutant
 - Concentration
 - MPC
 - WQI_Score
 - Hazard_Class
```bash
data/            # processed datasets
analytics/       # analytical and ML scripts
outputs/         # generated visualizations

