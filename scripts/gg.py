import requests
import pandas as pd
import re

url = "https://www.google.com/intl/en_ALL/ipv6/statistics/data/worldmap.js"
text = requests.get(url).text

# Extract only the data array
match = re.search(r'data:\s*(\[[\s\S]*?\])\s*}', text)
data = eval(match.group(1))

rows = []
for item in data:
    rows.append({
        "country_code": item[0],
        "country": item[1],
        "google_ipv6": item[2]   # ✅ THIS is the real value
    })

df = pd.DataFrame(rows)
df.to_csv("google_ipv6.csv", index=False)

print("✅ Google dataset DONE")