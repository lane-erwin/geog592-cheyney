#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import requests
import time


# In[2]:


url_0 = "https://www2.census.gov/geo/tiger/GENZ2024/shp/" # url for census tiger data 
url_county = "cb_2024_us_county_500k.zip" # county level
url_state = "cb_2024_us_state_500k.zip" # state level 


## Code for county level data 

counties = gpd.read_file(url_0+url_county)
nc_counties = counties.loc[counties["STATEFP"] == "37"].to_crs(6543).copy()
nc_counties.plot(edgecolor="black", facecolor="white")


# In[3]:


species = ["Pueraria montana"]
year = 2025
api = "https://api.gbif.org/v1"
records = []

for name in species:
    response = requests.get(
        f"{api}/species/match",
        params={"name": name, "strict": "true"},
        timeout=60  
    )
    response.raise_for_status()
    match = response.json()

    if (
        match.get("matchType") != "EXACT"
        or match.get("rank") != "SPECIES"
    ):
        raise ValueError(f"Check the species name: {name}")

    taxon_key = match.get("acceptedUsageKey", match["usageKey"])

    parameters = {
        "taxonKey": taxon_key,
        "country": "US",
        "year": year,
        "basisOfRecord": "HUMAN_OBSERVATION",
        "occurrenceStatus": "PRESENT",
        "hasCoordinate": "true",
        "hasGeospatialIssue": "false",
        "limit": 300,
        "offset": 0
    }

    species_records = []

    while True:
        response = requests.get(
            f"{api}/occurrence/search",
            params=parameters,
            timeout=60
        )
        response.raise_for_status()
        page = response.json()

        if page["count"] > 9000:
            raise ValueError(
                f"{name} has too many records for this example. "
                "Use a GBIF bulk download."
            )

        for record in page["results"]:
            record["queried_species"] = name

        species_records.extend(page["results"])

        if page.get("endOfRecords") or not page["results"]:
            break

        parameters["offset"] += len(page["results"])
        time.sleep(0.2)

    records.extend(species_records)

    print(f"{name}: {len(species_records):,} records")


# In[4]:


# make the kudzu records into a dataframe
kudzu_df = pd.DataFrame(records)

kudzu_df = kudzu_df[
    [
        "scientificName",
        "decimalLatitude",
        "decimalLongitude",
        "year"
    ]]


kudzu_df.head()


# In[5]:


kudzu = gpd.GeoDataFrame(
    kudzu_df,
    geometry=gpd.points_from_xy(
        kudzu_df["decimalLongitude"],
        kudzu_df["decimalLatitude"]
    ),
    crs=4326
)

# need to reproject to match NC
kudzu= kudzu.to_crs(6543)

print(len(kudzu))


# In[6]:


ax = nc_counties.plot(
    edgecolor="black",
    facecolor="white",
    figsize=(10, 10)
)

kudzu.plot(
    ax=ax,
    color="darkgreen",
    markersize=3
)

ax.set_axis_off()
plt.show()


# In[7]:


kudzu_join = gpd.sjoin(
    kudzu,
    nc_counties[["NAME", "geometry"]],
    how="inner",
    predicate="within"
)

kudzu_counts = kudzu_join.groupby("NAME").size()

nc_counties["Kudzu_Count"] = (
    nc_counties["NAME"]
    .map(kudzu_counts)
    .fillna(0)
    .astype(int)
)

nc_counties[
    ["NAME", "Kudzu_Count"]
].sort_values(
    "Kudzu_Count",
    ascending=False
).head(10)


# In[8]:


def county_map(county, ax):
    selected = nc_counties[nc_counties["NAME"] == county]

    selected.plot(
        ax=ax,
        edgecolor="black",
        facecolor="#dce8d5"
    )

    selected_kudzu = kudzu_join[
        kudzu_join["NAME"] == county
    ]

    selected_kudzu.plot(
        ax=ax,
        color="green",
        markersize=8,
        alpha=0.7
    )

    ax.set_axis_off()


# In[9]:


import inspect
print(inspect.getsource(locator_map))


# In[ ]:


def locator_map(county, ax):
    selected = nc_counties[nc_counties["NAME"] == county]
    print("selected rows:", len(selected), "| total counties:", len(nc_counties))
    nc_counties.plot(ax=ax, edgecolor="gray", facecolor="white")
    selected.plot(ax=ax, edgecolor="black", facecolor="crimson", zorder=3)
    ax.set_axis_off()
    print("axis off:", not ax.axison, "| xlim:", ax.get_xlim())


# In[ ]:


fig, ax = plt.subplots(figsize=(10, 5))
nc_counties.plot(ax=ax, edgecolor="gray", facecolor="white")
plt.show()
print(nc_counties.shape, nc_counties.crs, nc_counties.total_bounds)


# In[ ]:


def locator_map(county, ax):
    selected = nc_counties[nc_counties["NAME"] == county]
    nc_counties.plot(ax=ax, edgecolor="gray", facecolor="white")
    selected.plot(ax=ax, edgecolor="black", facecolor="crimson", zorder=3)
    ax.set_axis_off()

fig, axes = plt.subplots(1, 2, figsize=(14, 6))
county_map("Durham", axes[0])
locator_map("Durham", axes[1])
plt.show()


# In[ ]:


fig, axes = plt.subplots(
    1, 2,
    figsize=(14, 6),
    gridspec_kw={"width_ratios": [1, 2]}  # locator map gets more room
)

county_map("Durham", axes[0])
locator_map("Durham", axes[1])


plt.show()


# In[ ]:


def county_info(county, ax):

    selected = nc_counties[
        nc_counties["NAME"] == county
    ]

    count = selected["Kudzu_Count"].iloc[0]

    message = (
        "There are " + str(count) +
        " recorded kudzu occurrences in " +
        county + " County."
    )

    ax.text(
        0.05, 0.85,
        "KUDZU OCCURRENCES",
        transform=ax.transAxes,
        fontsize=13,
        fontweight="bold",
        color="darkgreen"
    )

    ax.text(
        0.05, 0.55,
        str(count),
        transform=ax.transAxes,
        fontsize=35,
        fontweight="bold",
        color="darkgreen"
    )

    ax.text(
        0.05, 0.25,
        message,
        transform=ax.transAxes,
        fontsize=12,
        wrap=True,
        va="top"
    )

    ax.set_axis_off()


# In[ ]:


fig, axes = plt.subplots(
    1, 2,
    figsize=(14, 6),
    gridspec_kw={"width_ratios": [1, 2]}  # locator map gets more room
)

county_map("Durham", axes[0])
locator_map("Durham", axes[1])

plt.tight_layout()
plt.show()


# In[ ]:


fig, axes = plt.subplots(1, 2, figsize=(12, 6))

county_map("Durham", axes[0])
locator_map("Durham", axes[1])

plt.show()


# In[ ]:


county = "Durham"

fig = plt.figure(figsize=(12, 8))

# Create map panels
def county_figure(county, pdf):
    fig = plt.figure(figsize=(12, 8))

    ax_county = fig.add_axes([0.05, 0.23, 0.55, 0.54])
    ax_locator = fig.add_axes([0.05, 0.08, 0.25, 0.12])
    ax_info = fig.add_axes([0.65, 0.30, 0.30, 0.40])

# Add maps and information
    county_map(county, ax_county)
    locator_map(county, ax_locator)
    county_info(county, ax_info)

# Page heading
    fig.text(
        0.05, 0.94,
        "NORTH CAROLINA / KUDZU OCCURRENCE ATLAS",
        fontsize=10,
        color="darkgreen"
    )

    fig.text(
        0.05, 0.87,
        county + " County",
        fontsize=28,
        fontweight="bold"
    )

# Footer
    fig.text(
        0.05, 0.03,
        "Source: GBIF occurrence records | U.S. Census Bureau county boundaries",
        fontsize=9,
        color="gray"
    )

    pdf.savefig(fig, dpi=50)
    plt.close(fig)


# In[ ]:


# def county_figure(county):
#     fig, axes = plt.subplots(
#         2, 1,
#         figsize=(8, 10),
#         gridspec_kw={"height_ratios": [3, 1]}
#     )

#     county_map(county, axes[0])
#     locator_map(county, axes[1])

#     fig.suptitle(f"{county} County", fontsize=20)

#     fig.savefig(f"{county}_County.pdf")
#     plt.close(fig)


# In[ ]:


# county_figure("Mecklenburg")


# In[ ]:


# def county_figure(county, pdf):
#     fig, axes = plt.subplots(
#         2, 1,
#         figsize=(8, 10),
#         gridspec_kw={"height_ratios": [3, 1]}
#     )

#     county_map(county, axes[0])
#     locator_map(county, axes[1])

#     fig.suptitle(f"{county} County", fontsize=20)

#     pdf.savefig(fig)
#     plt.close(fig)


# In[ ]:


from matplotlib.backends.backend_pdf import PdfPages 


# In[ ]:


nc_counties = nc_counties.sort_values(
    "NAME"
).reset_index(drop=True)

with PdfPages("NC_Kudzu_Atlas.pdf") as pdf:
    for county in nc_counties["NAME"]:
        county_figure(county, pdf)


# In[10]:


get_ipython().run_line_magic('pip', 'install nbconvert')

