from dash import Dash, html, dcc, callback, Output, Input
from dash_extensions.javascript import assign
import dash_leaflet as dl
import geopandas as gpd
import plotly.express as px
import pandas as pd
import os

# Load data
df = pd.read_csv(os.path.join("Traffic_colisions_toronto_2022.csv"))

# Define column mappings
cols_to_labels = {
    'OCC_DOW': 'WeekDay',
    'OCC_MONTH': 'Month',
    'NEIGHBOURHOOD_158': 'Neighbourhood'
}

#sort values by days - Convert OCC_dpw to a categorical type 
df['OCC_DOW'] = pd.Categorical(df['OCC_DOW'], categories=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'], 
    ordered=True)

# Extract unique values for dropdowns
dropdowns = [
    html.Div([
        html.B(label),
        dcc.Dropdown(
            options=[{'label': val, 'value': val} for val in df[col].unique()],
            value=[df[col].unique()[0]],  # Default: first value as a list (for multi-selection)
            multi=True,
            id=f'filter_{i+1}_dropdown'
        )
    ], style={'flex': '1', 'minWidth': '150px'}) for i, (col, label) in enumerate(cols_to_labels.items())
]

# Convert DataFrame to GeoDataFrame
gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.LONG_WGS84, df.LAT_WGS84))
gdf['active_col'] = 'WeekDay'
points_geojson = gdf.__geo_interface__

def assign_point_to_layer():
    point_to_layer = assign("""function(feature, latlng, context){
    const {circleOptions} = context.hideout;
    return L.circleMarker(latlng, circleOptions);  // render a simple circle marker
    }""")
    return point_to_layer

# Create a dictionary for unique values for each label based on cols_to_labels
labels_unique_values_dict = {label: df[col].unique().tolist() for col, label in cols_to_labels.items()}

# Create dropdowns using only the labels from cols_to_labels
x_axis_dropdown = dcc.Dropdown(
    options=[{'label': label, 'value': label} for label in cols_to_labels.values()],
    value=list(cols_to_labels.values())[0],  # Default to the first label
    id='x_axis_dropdown',
    style={'width': '100%'}  # Set width to 100%
)
# color scheme
color_stack_dropdown = dcc.Dropdown(
    options=[{'label': label, 'value': label} for label in cols_to_labels.values()],
    value=list(cols_to_labels.values())[1],  # Default to the second label
    id='color_stack_dropdown',
    style={'width': '100%'}  # Set width to 100%
)

# Function to generate bar graph
def graph_generator(df, x_col, color_stack_col):
    gb_df = df.groupby([x_col, color_stack_col]).size().reset_index(name='count')
    fig = px.bar(gb_df, x=x_col, y='count', color=color_stack_col, template='plotly_white')
    fig.update_layout(xaxis={'tickmode': 'linear'}, margin={'l': 0, 'r': 0, 't': 25, 'b': 25}, height=400)
    fig.update_xaxes(title_text=cols_to_labels[x_col])
    fig.update_yaxes(title_text='Number of Accidents')
    fig.update_layout(legend_title_text=cols_to_labels[color_stack_col])
    return fig

# Function to generate an empty graph with a message
def empty_graph():
    fig = px.scatter()
    fig.add_annotation(
        text="Cannot produce a graph",
        xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font={'size': 20, 'color': "red"}
    )
    fig.update_layout(
        xaxis={'visible': False},
        yaxis={'visible': False},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin={'l': 0, 'r': 0, 't': 40, 'b': 0},
        height=300
    )
    return fig

# Initial graph
fig = graph_generator(df, x_col='OCC_DOW', color_stack_col='OCC_MONTH')

# Hideout dictionary for map
hide_out_dict = {
    'active_col': 'WeekDay', 
    'circleOptions': {'fillOpacity': 1, 'stroke': False, 'radius': 3.5},
    'color_dict': dict(hex='#119DFF')
}

# Create the map and add points
dah_main_map = dl.Map([
                    dl.TileLayer(
                        url='https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png'),
                     dl.GeoJSON(
                        id='points_geojson', data=points_geojson,
                        pointToLayer=assign_point_to_layer(),  # how to draw points
                        hideout=hide_out_dict,
                     ),
                    dl.LocateControl(
                        locateOptions={'enableHighAccuracy': True})
                ],
                    center=[43.51, -79.2],
                    zoom=8,
                    style={'height': '100%'},
                    id='main_map',
                    dragging=True,
                    zoomControl=True,
                    scrollWheelZoom=True,
                    doubleClickZoom=True,
                    boxZoom=True,
                )

# Populate filter divs based on cols_to_labels using dropdowns
list_filter_divs = []
for i, (col, label) in enumerate(cols_to_labels.items()):
    new_filter_div = html.Div([
        html.B(label),
        dcc.Dropdown(
            options=[{'label': str(value), 'value': value} for value in labels_unique_values_dict[label]],
            value=[],  # Default to no selected values
            multi=True,  # Allow multiple selections
            id=f'filter_{i+1}_dropdown',
            style={'width': '100%'}  # Set width to 100%
        )
    ], style={'width': '100%'})  # Ensure the parent div also takes full width
    list_filter_divs.append(new_filter_div)

# Initialize the Dash app
app = Dash()

# Set the layout
app.layout = html.Div(
    style={
        'display': 'grid',
        'gridTemplateColumns': '33% 33% 33%',
        'gridTemplateRows': '26% 37% 37%',
        'gap': '10px',
        'height': '100vh',
        'width': '100vw'
    },
    children=[
        html.Div(html.H1('Car Accidents in GTA 2022'), style={'padding': '20px'}),
        html.Div(list_filter_divs, style={'gridColumn': 'span 2', 'display': 'flex', 'flexDirection': 'column', 'padding': '20px'}),
        html.Div(dah_main_map, style={'gridColumn': 'span 2', 'gridRow': 'span 2'}),
        html.Div([
            dcc.Graph(figure=fig, id='contextual_graph'),
            html.Div([
                html.Div(x_axis_dropdown, style={'flex': '1', 'textAlign': 'left'}),
                html.Div(color_stack_dropdown, style={'flex': '1', 'textAlign': 'left'})
            ], style={'display': 'flex'}),
            dcc.Checklist(['Filter Map-view'])
        ])
    ]
)

# Callback to update the contextual graph based on user inputs
@app.callback(
    Output('contextual_graph', 'figure'),
    Output('points_geojson', 'data'),
    Output('points_geojson', 'hideout'),
    Output('main_map', 'center'),  # Add output for map center
    Input('x_axis_dropdown', 'value'),
    Input('color_stack_dropdown', 'value'),
    Input('points_geojson', 'hideout'),
    *[Input(f'filter_{i+1}_dropdown', 'value') for i in range(len(cols_to_labels))]
)
def update_contextual_graph_map(x_axis, color_stack, hideout, *filter_values):
    df_filtered = df.copy()
    
    # Create a filter mask
    filter_mask = pd.Series([True] * len(df_filtered))
    
    for i, (col, label) in enumerate(cols_to_labels.items()):
        current_filter_values = filter_values[i]
        if current_filter_values:  # Only apply filter if there are selected values
            filter_mask &= df_filtered[col].isin(current_filter_values)
  
    df_filtered = df_filtered[filter_mask]
    
    # Update map points
    gdf_filtered = gpd.GeoDataFrame(df_filtered, geometry=gpd.points_from_xy(df_filtered.LONG_WGS84, df_filtered.LAT_WGS84))
    points_geojson_updated = gdf_filtered.__geo_interface__
    
    if df_filtered.empty or x_axis == color_stack or x_axis is None:
        fig = empty_graph()
    else:
        fig = graph_generator(df_filtered, x_col=list(cols_to_labels.keys())[list(cols_to_labels.values()).index(x_axis)], 
                                             color_stack_col=list(cols_to_labels.keys())[list(cols_to_labels.values()).index(color_stack)])
    
    # Get the center of the first point in the filtered data for the map
    if not df_filtered.empty:
        center_lat = df_filtered.iloc[0]['LAT_WGS84']
        center_lon = df_filtered.iloc[0]['LONG_WGS84']
        return fig, points_geojson_updated, hideout, [center_lat, center_lon]  # Return new center
    return fig, points_geojson_updated, hideout, [43.51, -79.2]  # Default center if no data

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False, port=8054)