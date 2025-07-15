import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd
import os
import datetime as dt


s_dict = dict()
pth = 'outfiles'
#for i in range(1,10, 3):
for i in [1,5,7,9]:
    sensor = f'T0{i}'
    pthi = os.path.join(pth, sensor + '.csv')
    df_ = pd.read_csv(pthi, parse_dates = ['timestamp'])
    df_ = df_.copy()[df_.timestamp >= dt.datetime(2025,7,5)]
    s_dict[sensor] = df_

places = {'T01': 'La Paz', 'T05':'Caranavi', 
          'T07':'Sapecho', 'T09':'San Buenaventura'}

def get_lats_lon():
    sensors = []
    #for i in range(1,10):
    for i in [1,5,7,9]:
        sensor = f'T0{i}'
        dff = s_dict[sensor]
        lst_row = dff.iloc[-1, :]
        lat = lst_row.latitude
        lon = lst_row.longitude
        pm10last = str(lst_row.mcpm10) + 'ug/m3'
        last_update = lst_row.timestamp
        #place = places[sensor]
        sensors.append([sensor, lat, lon, pm10last, last_update])
        
    df_places = pd.DataFrame(sensors, columns=['id', 'lat', 'lon', 'pm10', 'last_update'])
    return df_places

def get_series(sensor):
    dff = s_dict[sensor]
    dff = dff.copy()[['timestamp', 'mcpm10']]
    dff['id'] = sensor
    return dff


df_places = get_lats_lon()
lat0 = df_places.lat.mean()
lon0 = df_places.lon.mean()


# Combine all for default view
all_ts = pd.concat([get_series(sid) for sid in df_places['id']])

# Initial time series with all sensors
def get_all_ts_plot():
    return px.line(all_ts, x="timestamp", y="mcpm10", color="id", title="All Sensors - Time Series")



# Dash app
app = dash.Dash(__name__)

fig = px.scatter_map(
    df_places,
    lat="lat", lon="lon", hover_name="id",
    hover_data={'pm10':True, 'lat':False, 'lon':False,
                'last_update':True},
    #color="pm10", #not working
    #color_continuous_scale="Rainbow",  # or e.g. "Jet", "Plasma", etc.
    zoom=7, height=500,size_max=15
)
fig.update_layout(
    mapbox_style="open-street-map",
    mapbox_center={"lat": lat0, "lon": lon0},
    mapbox_zoom=8
)
fig.update_traces(marker=dict(size=20, color='red'))


# Layout
app.layout = html.Div([
    dcc.Graph(id='map', figure=fig),
    html.Button("Show All Sensors", id="reset-button", n_clicks=0),
    dcc.Graph(id='timeseries', figure=get_all_ts_plot())
])


# Callback logic
@app.callback(
    Output('timeseries', 'figure'),
    Input('map', 'clickData'),
    Input('reset-button', 'n_clicks'),
    prevent_initial_call=True
)
def update_timeseries(clickData, n_clicks):
    triggered_id = dash.callback_context.triggered[0]['prop_id'].split('.')[0]

    if triggered_id == 'map' and clickData:
        sensor_id = clickData['points'][0]['hovertext']
        ts = get_series(sensor_id)
        return px.line(ts, x='timestamp', y='mcpm10', title=f"PM10 {sensor_id}-{places[sensor_id]}")
    
    # If reset button clicked
    return get_all_ts_plot()
    
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8050))  # Use Render's assigned port
    app.run_server(host="0.0.0.0", port=port)
