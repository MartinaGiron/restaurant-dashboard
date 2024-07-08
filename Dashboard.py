import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import plotly.graph_objects as go
import numpy as np
import folium
from folium import plugins
from streamlit_folium import st_folium

date_info = pd.read_csv("date_info.csv", parse_dates= ['calendar_date'])
air_reserve = pd.read_csv("air_reserve.csv", parse_dates = ["reserve_datetime", "visit_datetime"])
air_store_info = pd.read_csv("air_store_info.csv")
store_id_relation = pd.read_csv("store_id_relation.csv")


air = pd.merge(air_reserve, air_store_info, on = "air_store_id")
air['visit_date'] = air['visit_datetime'].dt.date
air['visit_date'] = pd.to_datetime(air['visit_date']) 
air['reserve_date'] = air['reserve_datetime'].dt.date
air['reserve_date'] = pd.to_datetime(air['reserve_date']) 
air['visit_time'] = air['visit_datetime'].dt.time
air['reserve_time'] = air['reserve_datetime'].dt.time



air = air.merge(date_info, left_on = "reserve_date", right_on = "calendar_date", how = "left")
air = air.merge(date_info, left_on = "visit_date", right_on = "calendar_date", how = "left", suffixes = ("_visit", "_reserve"))







st.write("""
# Restaurant Dashboard

""")
min_date = air['visit_date'].min()
max_date = air['visit_date'].max()


st.sidebar.title("Filters")

date_range = st.sidebar.date_input("Visit Dates", 
                           (min_date, max_date),
                           min_value=min_date, max_value=max_date)
genres = st.sidebar.multiselect('Genres', options=air['air_genre_name'].unique(), default=air['air_genre_name'].unique())
areas = st.sidebar.multiselect('Areas', options=air['air_area_name'].unique(), default=air['air_area_name'].unique())

filtered_df = air[(air['air_genre_name'].isin(genres)) & 
                  (air['air_area_name'].isin(areas)) &
                  (air['visit_date'] > np.datetime64(date_range[0])) &  (air['visit_date'] < np.datetime64(date_range[1]))]

visit_counts_df = filtered_df['visit_date'].value_counts().sort_index()
visit_counts_df = visit_counts_df.reset_index()
visit_counts_df.columns = ['date', 'count']

time_visit_counts = filtered_df['visit_time'].value_counts().sort_index().reset_index()
time_visit_counts.columns = ['time', 'count']


time_reserve_counts = filtered_df['reserve_time'].value_counts().sort_index().reset_index()
time_reserve_counts.columns = ['time', 'count']

filtered_df['reserve_to_visit'] = filtered_df['visit_datetime'] - filtered_df['reserve_datetime']
diff_time_counts = filtered_df['reserve_to_visit'].value_counts().sort_index().reset_index()
diff_time_counts.columns = ['time', 'count']
idx_2 = diff_time_counts['count'].nlargest(2).index[1]

visit_most = time_visit_counts.loc[time_visit_counts['count'].idxmax() , "time"]
reserve_most = time_visit_counts.loc[time_reserve_counts['count'].idxmax(), "time"]
time_diff = diff_time_counts.loc[idx_2, 'time']



st.text("\n")

col1, col2, col3, col4 = st.columns(4)

with col1:
   st.metric("Restaurants", len(filtered_df.air_store_id.unique()), delta=None, delta_color="normal", help=None, label_visibility="visible")
   st.metric("Average # Visitors", filtered_df.reserve_visitors.median(), delta=None, delta_color="normal", help=None, label_visibility="visible")

with col2:
   st.metric("Genres", len(filtered_df.air_genre_name.unique()), delta=None, delta_color="normal", help=None, label_visibility="visible")
   st.metric("Most visited time", visit_most.strftime('%H:%M'), delta=None, delta_color="normal", help=None, label_visibility="visible")

with col3:
   st.metric("Areas", len(filtered_df.air_area_name.unique()), delta=None, delta_color="normal", help=None, label_visibility="visible")
   st.metric("Most reserved time", reserve_most.strftime('%H:%M'), delta=None, delta_color="normal", help=None, label_visibility="visible")

with col4:
   st.metric("Total Visits", len(filtered_df), delta=None, delta_color="normal", help=None, label_visibility="visible")
   st.metric("Reservation to Visit (Hours)", str(time_diff.total_seconds()/3600), delta=None, delta_color="normal", help=None, label_visibility="visible")

st.text("")
st.text("")

col1, col2 = st.columns(2)


with col1:
   air_locations = filtered_df[['air_store_id', 'latitude', 'longitude', 'air_genre_name']].drop_duplicates()
   m = folium.Map(location=[38.2048, 140], tiles="CartoDB Positron", zoom_start=4.2)

   for index, row in air_locations.iterrows():
    folium.CircleMarker(location=[row["latitude"], row["longitude"]],
                        popup="Store ID: " + row['air_store_id'] 
                        + "<br>"
                        + "Genre: " + row['air_genre_name'],
                        color="cornflowerblue",
    stroke=False,
    fill=True,
    fill_opacity=0.1,
    radius = 3).add_to(m)


# call to render Folium map in Streamlit
   st_data = st_folium(m, width = 400, height = 300)

with col2:
   line_chart = px.line(visit_counts_df, x='date', y="count", title = "Daily Visits")
   line_chart.update_layout(height=300)
   st.plotly_chart(line_chart)



genre_counts = filtered_df['air_genre_name'].value_counts().sort_index().reset_index()
genre_counts.columns =  ['genre', 'count']

col1, col2 = st.columns(2, gap = "large")

with col1:
   bar_chart = px.bar(time_visit_counts, x='time', y="count", title = "Time of Visiting")
   bar_chart.update_layout(height=300)
   st.plotly_chart(bar_chart)

with col2:
   bar_chart = px.bar(time_reserve_counts, x='time', y="count", title = "Time of Reserving")
   bar_chart.update_layout(height=300)
   st.plotly_chart(bar_chart)

tree = px.treemap(genre_counts, path = ['genre'], values = 'count', title = "Genres", color="count", color_continuous_scale='Viridis')
tree.update_traces(texttemplate='<b>%{label}</b><br>%{value}', textfont_size=12)

st.plotly_chart(tree)










