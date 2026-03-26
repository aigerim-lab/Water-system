import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

df = pd.read_excel("Kazakhstan_Water_Pollution_Dataset.xlsx")

print(df.head())

# если Year еще нет
df["Year"] = pd.to_datetime(df["Date"]).dt.year 

# ratio
df["ratio"] = df["Concentration"] / df["MPC"]

# mean WQI
print("Mean WQI:", df["WQI_Score"].mean())

# regional average
print(df.groupby("Region")["WQI_Score"].mean())

# trend
trend = df.groupby("Year")["WQI_Score"].mean().reset_index()
print(trend)

# ML baseline
data = trend.dropna(subset=["Year", "WQI_Score"])

X = data[["Year"]]
y = data["WQI_Score"]

model = LinearRegression()
model.fit(X, y)

future_year = pd.DataFrame({"Year": [2025]})
pred = model.predict(future_year)

print("Predicted WQI for 2025:", pred[0])

y_pred = model.predict(X)
r2 = r2_score(y, y_pred)
print("R2 score:", r2)

# graph
plt.figure(figsize=(8,5))
plt.plot(data["Year"], data["WQI_Score"], marker="o", label="Actual trend")
plt.scatter([2025], pred, color="red", label="Predicted 2025")

plt.xlabel("Year")
plt.ylabel("Average WQI")
plt.title("Average WQI Trend and Forecast")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("wqi_trend.png", dpi=300, bbox_inches="tight")
plt.show()