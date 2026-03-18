from pymongo import MongoClient
import pandas as pd

client = MongoClient("mongodb+srv://ipv6_admin:nltvc_apac@cluster0.rka6zzr.mongodb.net/apac_ipv6_hub?retryWrites=true&w=majority&appName=Cluster0")

db = client["apac_ipv6_hub"]
collection = db["external_ipv6_stats"]

docs = list(collection.find({}, {"_id":0}))

df = pd.DataFrame(docs)

df = df[["country","source","ipv6_percent"]]

# FIX: handle duplicates
pivot = df.pivot_table(
    index="country",
    columns="source",
    values="ipv6_percent",
    aggfunc="mean"
)

pivot.reset_index(inplace=True)

pivot["adoption_score"] = pivot[["APNIC","Google","Cloudflare"]].mean(axis=1)

pivot.to_csv("data/ipv6_training_dataset.csv", index=False)

print("Training dataset exported successfully")
print(pivot.head())