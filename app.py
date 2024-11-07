import streamlit as st
import pandas as pd
import geopandas as gpd
import numpy as np
import folium
import streamlit.components.v1 as components

APP_TITLE = "William K*nt*l"

def main():
    #Settings
    pd.set_option("display.max_columns", None)

    #Title
    st.set_page_config(APP_TITLE)
    st.title(APP_TITLE)

    #Import Data
    gdf = gpd.read_file('C:/Users/923007690/Jupyter/Project_Kecamatan/Kabupaten_Final.shp')
    LT = pd.read_excel('C:/Users/923007690/Jupyter/Project_Kecamatan/CB_FB_LT.xlsx')

    #Data Cleaning
    gdf = gdf.rename(columns={'Toko Podes': 'Podes'})
    gdf = gdf[['kode_kab_s', 'nama_kab', 'kode_prop_','nama_prop','jumlah_pen', 'wil2', 'Depo', 'TEST', 'Podes', 'geometry']]
    LT['Kode'] = pd.to_numeric(LT['Kode'], errors='coerce')

    gdf = gdf.merge(LT, how='left', left_on ='kode_kab_s', right_on = 'Kode')

    column_options = LT.columns.tolist()
    # Create columns for %Qty selectors
    col1, col2 = st.columns(2)
    with col1:
        qty_numerator = st.selectbox("Select numerator for %Qty", options=column_options, index=column_options.index('Qty_FB') if 'Qty_FB' in column_options else 0)
    with col2:
        qty_denominator = st.selectbox("Select denominator for %Qty", options=column_options, index=column_options.index('Qty_CB') if 'Qty_CB' in column_options else 0)

    # Create columns for %LT selectors
    col3, col4 = st.columns(2)
    with col3:
        lt_numerator = st.selectbox("Select numerator for %LT", options=column_options, index=column_options.index('LT_FB') if 'LT_FB' in column_options else 0)
    with col4:
        lt_denominator = st.selectbox("Select denominator for %LT", options=column_options, index=column_options.index('LT_CB') if 'LT_CB' in column_options else 0)

    # Calculate %Qty and %LT based on selected columns
    gdf['%Qty'] = np.where(gdf[qty_denominator] != 0, gdf[qty_numerator] / gdf[qty_denominator], 0) * 100
    gdf['%LT'] = np.where(gdf[lt_denominator] != 0, gdf[lt_numerator] / gdf[lt_denominator], 0) * 100

    #gdf['%Qty'] = np.where(gdf['Qty_CB'] != 0, gdf['Qty_FB'] / gdf['Qty_CB'], 0)*100
    #gdf['%LT'] = np.where(gdf['LT_CB'] != 0, gdf['LT_FB'] / gdf['LT_CB'], 0)*100

    WIL_options = sorted([wil for wil in gdf['wil2'].unique() if wil is not None])
    selected_WIL = st.multiselect("Select Wilayah (WIL)", WIL_options, default=WIL_options[0:1])
    gdf = gdf[gdf['wil2'].isin(selected_WIL)]

    #Map
    heat_column = st.selectbox("Select Heat Column", ['%LT', '%Qty'])

    col5, col6 = st.columns(2)
    with col5:
        lower_bound = st.number_input("Enter minimum threshold", min_value=0, max_value=100000, value=0)
    with col6:
        upper_bound = st.number_input("Enter maximum threshold", min_value=0, max_value=100000, value=100)

    gdf['heat'] = np.clip(gdf[heat_column], lower_bound, upper_bound)

    m = folium.Map(location=[gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean()], zoom_start=10)

    folium.Choropleth(
        geo_data=gdf,  # GeoJSON/Geo Database
        name='choropleth',
        data=gdf,  # Data to bind with the geo_data
        columns=['kode_kab_s', 'heat'],  # Columns from the DataFrame
        key_on='feature.properties.kode_kab_s',  # Match feature.id to code place column in geo_data
        fill_color= 'YlOrRd',   #Gradient color (Yellow to Green to Blue, customizable)
        # fill_opacity=0.7,
        # line_opacity=0.2,
        legend_name='LT'
    ).add_to(m)

    folium.GeoJson(
        gdf,
        tooltip=folium.GeoJsonTooltip(
            fields=['nama_kab', 'wil2', 'Podes', '%Qty', '%LT', 'Qty_FB', 'Qty_CB', 'LT_FB', 'LT_CB', 'jumlah_pen'],
            aliases=['Nama Kabupaten:', 'Wilayah:', 'Podes:', '%Qty:', '%LT:', 'Qty FB:', 'Qty CB:', 'LT FB:', 'LT CB:', 'Jumlah Pen:'],
            localize=True
        ),
        style_function=lambda x: {'fillColor': 'transparent', 'color': 'black', 'weight': 0.5}
    ).add_to(m)

    for _, row in gdf.iterrows():
        centroid = row['geometry'].centroid
        short_label = row['nama_kab']
        folium.Marker(
            location=[centroid.y, centroid.x],
            icon=folium.DivIcon(
                html=f'<div style="font-size: 8px; color: black; margin-left: -10px;">{short_label}</div>'
            )
        ).add_to(m)
    
    m.save('app.html')
    p = open("app.html")
    components.html(p.read(), height=600)

         

if __name__ == "__main__":
    main()