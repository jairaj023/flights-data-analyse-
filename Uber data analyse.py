import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
import squarify
from pandasql import sqldf

file_name = "Uber Request Data.csv"

df = pd.read_excel(file_name)

df['Request timestamp'] = pd.to_datetime(df['Request timestamp'], dayfirst=True, errors='coerce')
df['Drop timestamp'] = pd.to_datetime(df['Drop timestamp'], dayfirst=True, errors='coerce')

df['Date'] = df['Request timestamp'].dt.date
df['Hour'] = df['Request timestamp'].dt.hour

df.dropna(subset=['Request timestamp'], inplace=True)

conn = sqlite3.connect(':memory:')
df.to_sql('uber_data', conn, index=False, if_exists='replace')

print("🧾 Trip Status Summary:")
query1 = '''
SELECT Status, COUNT(*) AS total_requests
FROM uber_data
GROUP BY Status
'''
print(pd.read_sql(query1, conn))

print("\n🚖 Pickup point vs Status:")
query2 = '''
SELECT `Pickup point`, Status, COUNT(*) AS count
FROM uber_data
GROUP BY `Pickup point`, Status
ORDER BY `Pickup point`
'''
print(pd.read_sql(query2, conn))

print("\n📉 Supply-Demand Gap:")
query3 = '''
SELECT
  COUNT(*) AS total_requests,
  SUM(CASE WHEN Status = 'Trip Completed' THEN 1 ELSE 0 END) AS completed,
  SUM(CASE WHEN Status != 'Trip Completed' THEN 1 ELSE 0 END) AS not_completed,
  ROUND(SUM(CASE WHEN Status != 'Trip Completed' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS gap_percent
FROM uber_data
'''
print(pd.read_sql(query3, conn))

unfulfilled = df[df['Status'] != 'Trip Completed']

plt.figure(figsize=(12,6))
sns.countplot(data=unfulfilled, x='Hour', color='skyblue')
plt.title("Fig 1.1 - Demand Gap Based on Hours")
plt.xlabel("Hour of the Day")
plt.ylabel("Unfulfilled Requests")
plt.show()

plt.figure(figsize=(6,5))
sns.countplot(data=unfulfilled, x='Pickup point', color='orange')
plt.title("Fig 1.3 - Demand Gap by Pickup Point")
plt.show()

def get_time_slot(hour):
    if 0 <= hour < 4:
        return 'Night'
    elif 4 <= hour < 7:
        return 'Early Morning'
    elif 7 <= hour < 12:
        return 'Morning'
    elif 12 <= hour < 17:
        return 'Afternoon'
    elif 17 <= hour < 21:
        return 'Evening'
    else:
        return 'Late Night'

df['Time_slot'] = df['Hour'].apply(get_time_slot)

plt.figure(figsize=(8,5))
sns.countplot(data=unfulfilled, x='Time_slot',
              order=['Night', 'Early Morning', 'Morning', 'Afternoon', 'Evening', 'Late Night'],
              color='orange')
plt.title("Fig 1.2 - Demand Gap by Time Slot")
plt.xlabel("Time Slot")
plt.ylabel("Unfulfilled Requests")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

q1 = "SELECT Status, COUNT(*) as Count FROM df WHERE Status != 'Trip Completed' GROUP BY Status"
print(psqldf(q1, locals()))

q2 = "SELECT `Pickup point`, COUNT(*) as Unfulfilled FROM df WHERE Status != 'Trip Completed' GROUP BY `Pickup point` ORDER BY Unfulfilled DESC"
print(psqldf(q2, locals()))

q3 = "SELECT Hour, COUNT(*) as Requests FROM df WHERE Status != 'Trip Completed' GROUP BY Hour ORDER BY Requests DESC LIMIT 1"
print(psqldf(q3, locals()))

insights = """
🔍 Insights Summary:

1. Maximum supply-demand gap is during Night and Early Morning hours (Fig 1.1, 1.2).
2. Most requests go unfulfilled from the Airport pickup point (Fig 1.3).
3. 'No Cars Available' dominates Night, while 'Cancelled' dominates Early Morning.
4. Drivers cancel most during Morning; lack of cars is the main issue at Night.

✅ Recommendations:
- Introduce driver incentives during Morning and Early Morning slots.
- Launch Night shifts or fixed pay for night drivers to meet late-night demand.
"""

print(insights)
