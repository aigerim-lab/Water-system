import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from sklearn.linear_model    import LinearRegression
from sklearn.tree            import DecisionTreeRegressor
from sklearn.ensemble        import RandomForestRegressor
from sklearn.metrics         import r2_score, mean_absolute_error, mean_squared_error

# XGBoost — install with:  pip install xgboost
from xgboost import XGBRegressor

# ── 1. Load & prepare data ────────────────────────────────────────────────────
df = pd.read_excel("Kazakhstan_Water_Pollution_Dataset.xlsx")
print(df.head())

df["Year"]  = pd.to_datetime(df["Date"]).dt.year
df["ratio"] = df["Concentration"] / df["MPC"]

print("\nMean WQI          :", df["WQI_Score"].mean())
print("\nRegional averages :\n", df.groupby("Region")["WQI_Score"].mean())

trend = df.groupby("Year")["WQI_Score"].mean().reset_index()
print("\nYearly trend :\n", trend)

# ── 2. Model setup ────────────────────────────────────────────────────────────
data = trend.dropna(subset=["Year", "WQI_Score"])
X    = data[["Year"]]
y    = data["WQI_Score"]

future_year   = pd.DataFrame({"Year": [2025]})
years_plot    = np.linspace(X["Year"].min(), 2025, 200).reshape(-1, 1)

MODELS = {
    "Linear Regression": LinearRegression(),
    "Decision Tree":     DecisionTreeRegressor(max_depth=3, random_state=42),
    "Random Forest":     RandomForestRegressor(n_estimators=200, random_state=42),
    "XGBoost":           XGBRegressor(n_estimators=200, learning_rate=0.1,
                                      max_depth=3, random_state=42,
                                      verbosity=0),
}

COLORS = {
    "Linear Regression": "orange",
    "Decision Tree":     "purple",
    "Random Forest":     "green",
    "XGBoost":           "crimson",
}

results = {}

print("\n" + "=" * 55)
for name, model in MODELS.items():
    model.fit(X, y)
    y_pred   = model.predict(X)
    pred2025 = float(model.predict(future_year)[0])

    r2   = r2_score(y, y_pred)
    mae  = mean_absolute_error(y, y_pred)
    rmse = np.sqrt(mean_squared_error(y, y_pred))

    results[name] = {
        "model":     model,
        "y_pred":    y_pred,
        "pred2025":  pred2025,
        "curve":     model.predict(years_plot),
        "r2":        r2,
        "mae":       mae,
        "rmse":      rmse,
    }

    print(f"\n── {name} ──")
    print(f"  Predicted WQI 2025 : {pred2025:.4f}")
    print(f"  R²                 : {r2:.4f}")
    print(f"  MAE                : {mae:.4f}")
    print(f"  RMSE               : {rmse:.4f}")

# ── 3. Comparison table ───────────────────────────────────────────────────────
print("\n" + "=" * 55)
print("── Model Comparison ──")
comp_df = pd.DataFrame(
    {
        "Model":      list(results.keys()),
        "Pred_2025":  [v["pred2025"] for v in results.values()],
        "R2":         [v["r2"]       for v in results.values()],
        "MAE":        [v["mae"]      for v in results.values()],
        "RMSE":       [v["rmse"]     for v in results.values()],
    }
)
print(comp_df.to_string(index=False))

# ── 4. Figure 1 — Trend + Forecast (all 4 models) ────────────────────────────
fig1, ax1 = plt.subplots(figsize=(11, 6))

ax1.plot(data["Year"], y, marker="o", color="steelblue",
         linewidth=2.5, zorder=5, label="Actual WQI (yearly mean)")

for name, res in results.items():
    ax1.plot(years_plot, res["curve"],
             linestyle="--", color=COLORS[name], linewidth=1.6,
             label=f"{name} fit")
    ax1.scatter([2025], [res["pred2025"]],
                color=COLORS[name], marker="^", s=130, zorder=6,
                label=f"{name} → {res['pred2025']:.2f}")

ax1.axvline(x=2024.5, color="grey", linestyle=":", linewidth=1, alpha=0.7)
ax1.set_xlabel("Year", fontsize=12)
ax1.set_ylabel("Average WQI", fontsize=12)
ax1.set_title("Average WQI Trend & 2025 Forecast\n"
              "(Linear Regression · Decision Tree · Random Forest · XGBoost)",
              fontsize=13, fontweight="bold")
ax1.legend(fontsize=8, ncol=2, loc="upper right")
ax1.grid(True, alpha=0.35)
plt.tight_layout()
plt.savefig("wqi_trend_4models.png", dpi=300, bbox_inches="tight")
plt.show()
print("Saved: wqi_trend_4models.png")

# ── 5. Figure 2 — Actual vs Predicted bar chart (2x2) ────────────────────────
fig2 = plt.figure(figsize=(13, 10))
fig2.suptitle("Actual vs Predicted WQI — All 4 Models",
              fontsize=15, fontweight="bold", y=1.01)
gs = gridspec.GridSpec(2, 2, figure=fig2, hspace=0.45, wspace=0.35)

y_vals = y.to_numpy()

for idx, (name, res) in enumerate(results.items()):
    ax = fig2.add_subplot(gs[idx // 2, idx % 2])
    color = COLORS[name]
    y_hat = res["y_pred"]
    years = data["Year"].to_numpy()
    x_pos = np.arange(len(years))
    width = 0.38

    ax.bar(x_pos - width/2, y_vals, width, label="Actual",
           color="steelblue", alpha=0.85, zorder=3)
    ax.bar(x_pos + width/2, y_hat,  width, label="Predicted",
           color=color,      alpha=0.85, zorder=3)

    for i, (a, p) in enumerate(zip(y_vals, y_hat)):
        diff = p - a
        ax.annotate(f"{diff:+.1f}",
                    xy=(x_pos[i] + width/2, max(a, p) + 0.3),
                    ha="center", va="bottom", fontsize=7.5,
                    color="darkred" if diff > 0 else "darkgreen")

    ax.set_xticks(x_pos)
    ax.set_xticklabels(years, fontsize=9)
    ax.set_xlabel("Year", fontsize=10)
    ax.set_ylabel("WQI Score", fontsize=10)
    ax.set_title(
        f"{name}\nR²={res['r2']:.3f}  MAE={res['mae']:.3f}  RMSE={res['rmse']:.3f}",
        fontsize=10, fontweight="bold")
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.3, zorder=0)
    ax.set_ylim(bottom=min(y_vals.min(), float(y_hat.min())) * 0.97)

plt.tight_layout()
plt.savefig("wqi_actual_vs_predicted.png", dpi=300, bbox_inches="tight")
plt.show()
print("Saved: wqi_actual_vs_predicted.png")

# ── 6. Figure 3 — Scatter Actual vs Predicted ────────────────────────────────
fig3, axes = plt.subplots(1, 4, figsize=(17, 4.5))
fig3.suptitle("Scatter: Actual vs Predicted WQI", fontsize=13, fontweight="bold")

all_preds = [r["y_pred"] for r in results.values()]
min_val   = min(y_vals.min(), min(p.min() for p in all_preds)) - 1
max_val   = max(y_vals.max(), max(p.max() for p in all_preds)) + 1

for ax, (name, res) in zip(axes, results.items()):
    ax.scatter(y_vals, res["y_pred"], color=COLORS[name],
               s=90, edgecolors="black", linewidths=0.6, zorder=4)
    ax.plot([min_val, max_val], [min_val, max_val],
            "k--", linewidth=1.2, label="Perfect fit")

    for xi, yi, yr in zip(y_vals, res["y_pred"], data["Year"]):
        ax.annotate(str(int(yr)), (xi, yi),
                    textcoords="offset points", xytext=(5, 4),
                    fontsize=7.5, color="dimgray")

    ax.set_xlim(min_val, max_val)
    ax.set_ylim(min_val, max_val)
    ax.set_xlabel("Actual WQI", fontsize=10)
    ax.set_ylabel("Predicted WQI", fontsize=10)
    ax.set_title(f"{name}\nR²={res['r2']:.3f}", fontsize=10, fontweight="bold")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)

plt.tight_layout()
plt.savefig("wqi_scatter_actual_vs_predicted.png", dpi=300, bbox_inches="tight")
plt.show()
print("Saved: wqi_scatter_actual_vs_predicted.png")