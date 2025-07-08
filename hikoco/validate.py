import pandas as pd

total_pages_df = pd.read_json("total-products.json")
total_pages_df["Total products"] = total_pages_df["Total products"].astype(int)

total_scraped_df = pd.read_json("product-links.json")
print("Total products:", total_pages_df["Total products"].sum())
print("Total scraped products:", total_scraped_df.shape[0])
