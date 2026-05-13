import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import numpy as np

df = pd.read_excel("Kazakhstan_Water_Pollution_Dataset.xlsx")

print(df.head())

# Extract year if not present
df["Year"] = pd.to_datetime(df["Date"]).dt.year

# Ratio
df["ratio"] = df["Concentration"] / df["MPC"]

# Mean WQI
print("Mean WQI:", df["WQI_Score"].mean())

# Regional average
print(df.groupby("Region")["WQI_Score"].mean())

# Yearly trend
trend = df.groupby("Year")["WQI_Score"].mean().reset_index()
print(trend)

# ── Models on yearly trend data ──────────────────────────────────────────────
data = trend.dropna(subset=["Year", "WQI_Score"])

X = data[["Year"]]
y = data["WQI_Score"]

future_year = pd.DataFrame({"Year": [2025]})

# 1. Linear Regression
lr_model = LinearRegression()
lr_model.fit(X, y)
lr_pred_2025 = lr_model.predict(future_year)[0]
lr_y_pred   = lr_model.predict(X)
lr_r2       = r2_score(y, lr_y_pred)
lr_mae      = mean_absolute_error(y, lr_y_pred)
lr_rmse     = np.sqrt(mean_squared_error(y, lr_y_pred))

print("\n── Linear Regression ──")
print(f"  Predicted WQI for 2025 : {lr_pred_2025:.4f}")
print(f"  R²  : {lr_r2:.4f}")
print(f"  MAE : {lr_mae:.4f}")
print(f"  RMSE: {lr_rmse:.4f}")

# 2. Random Forest Regressor
rf_model = RandomForestRegressor(n_estimators=200, random_state=42)
rf_model.fit(X, y)
rf_pred_2025 = rf_model.predict(future_year)[0]
rf_y_pred    = rf_model.predict(X)
rf_r2        = r2_score(y, rf_y_pred)
rf_mae       = mean_absolute_error(y, rf_y_pred)
rf_rmse      = np.sqrt(mean_squared_error(y, rf_y_pred))

print("\n── Random Forest Regressor ──")
print(f"  Predicted WQI for 2025 : {rf_pred_2025:.4f}")
print(f"  R²  : {rf_r2:.4f}")
print(f"  MAE : {rf_mae:.4f}")
print(f"  RMSE: {rf_rmse:.4f}")

# ── Comparison summary ────────────────────────────────────────────────────────
print("\n── Model Comparison ──")
comparison = pd.DataFrame({
    "Model":     ["Linear Regression", "Random Forest"],
    "Pred_2025": [lr_pred_2025, rf_pred_2025],
    "R2":        [lr_r2,        rf_r2],
    "MAE":       [lr_mae,       rf_mae],
    "RMSE":      [lr_rmse,      rf_rmse],
})
print(comparison.to_string(index=False))

# ── Plot ──────────────────────────────────────────────────────────────────────
plt.figure(figsize=(10, 6))

plt.plot(data["Year"], y, marker="o", color="steelblue",
         linewidth=2, label="Actual trend")

plt.plot(data["Year"], lr_y_pred, linestyle="--", color="orange",
         linewidth=1.5, label="Linear Regression fit")

plt.plot(data["Year"], rf_y_pred, linestyle="--", color="green",
         linewidth=1.5, label="Random Forest fit")

plt.scatter([2025], [lr_pred_2025], color="orange", marker="^",
            s=120, zorder=5, label=f"LR pred 2025: {lr_pred_2025:.2f}")

plt.scatter([2025], [rf_pred_2025], color="green", marker="^",
            s=120, zorder=5, label=f"RF pred 2025: {rf_pred_2025:.2f}")

plt.xlabel("Year")
plt.ylabel("Average WQI")
plt.title("Average WQI Trend and Forecast\n(Linear Regression vs Random Forest)")
plt.legend()
plt.grid(True, alpha=0.4)
plt.tight_layout()
plt.savefig("wqi_trend.png", dpi=300, bbox_inches="tight")
plt.show()