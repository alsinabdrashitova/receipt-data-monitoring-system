import dash
import pandas as pd
import numpy as np
from dash import Dash, dcc, html, Input, Output
from geopandas.tools import geocode
import plotly.express as px
import plotly.graph_objs as go
from app import app
# import dash_core_components as dcc
# import dash_html_components as html
from dash.dependencies import Input, Output

data = pd.read_excel("data.xlsx", sheet_name='Sheet1')
data = data.iloc[:, 1:]
print(type(data['dateTime']))
data["dateTime"] = pd.to_datetime(data["dateTime"], format="%Y-%m-%d")
print(type(data['dateTime']))
data.sort_values("dateTime", inplace=True)
print(data[data['category'] == 'Алкоголь'].Vid.unique())
city = data[['city']].drop_duplicates(['city'])
print(len(city))
token = 'pk.eyJ1Ijoib3NlbmEiLCJhIjoiY2wzN2U2Z2hxMWFmMjNkcG9sdGUyNGpzdCJ9.o7es3L5cdhg-Rb5Fe0JGUQ'


def custom_geocoder(address):
    dataframe = geocode(address, provider="nominatim", user_agent='my_request', timeout=10)

    point = dataframe.geometry.iloc[0]
    return pd.Series({'Latitude': point.y, 'Longitude': point.x})


navbarcurrentpage = {
    'text-decoration': 'underline',
    'text-decoration-color': 'rgb(7, 154, 130)',
    'text-shadow': '0px 0px 1px rgb(7, 154, 130)'
}
nav = {
    'color': 'rgb(7, 154, 130)'
}


def get_navbar(p='sales'):
    navbar_sales = html.Div([

        html.Div([], className='col-3'),

        html.Div([
            dcc.Link(
                html.H3(children='Общий анализ продаж',
                        style=navbarcurrentpage),
                href='/apps/vis'
            )
        ],
            className='col-2'),

        html.Div([
            dcc.Link(
                html.H3(children='Анализ продаж продукта',
                        style=nav),
                href='/apps/vis2'
            )
        ],
            className='col-2'),

        html.Div([], className='col-3')

    ],
        className='wrapper-page',
    )

    navbar_page2 = html.Div([

        html.Div([], className='col-3'),

        html.Div([
            dcc.Link(
                html.H3(children='Общий анализ продаж',
                        style=nav),
                href='/apps/vis'
            )
        ],
            className='col-2'),

        html.Div([
            dcc.Link(
                html.H3(children='Анализ продаж продукта',
                        style=navbarcurrentpage),
                href='/apps/vis2'
            )
        ],
            className='col-2'),

        html.Div([], className='col-3')

    ],
        className='wrapper-page',
    )

    if p == 'sales':
        return navbar_sales
    elif p == 'page2':
        return navbar_page2


city[['latitude', 'longitude']] = city.city.apply(lambda x: custom_geocoder(x))
city = city.set_index(['city'])

external_stylesheets = [
    {
        "href": "https://fonts.googleapis.com/css2?"
                "family=Lato:wght@400;700&display=swap",
        "rel": "stylesheet",
    },
]

# app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
# app.title = "Анализ чеков"

layout = html.Div(
    children=[
        html.Div(
            children=[
                html.P(children="📊", className="header-emoji"),
                html.H1(
                    children="Анализ чеков", className="header-title"
                ),
                html.P(
                    children="Анализ проданной продукции по Татарстану",
                    className="header-description",
                ),
            ],
            className="header",
        ),
        html.Div(
            children=[
                html.Div(
                    children=[
                        get_navbar('sales'),
                    ]
                ),
                html.Div(
                    children=[
                        html.Div(
                            children=[
                                html.Div(children="Категория", className="menu-title"),
                                dcc.Dropdown(
                                    id="region-filter",
                                    options=[
                                        {"label": region, "value": region}
                                        for region in np.sort(data.category.unique())
                                    ],
                                    value='Алкоголь',
                                    # clearable=False,
                                    className="dropdown",
                                ),
                            ]
                        ),
                        html.Div(
                            children=[
                                html.Div(children="Вид товара", className="menu-title"),
                                dcc.Dropdown(
                                    id="type-filter",
                                    className="dropdown",
                                ),
                            ],
                        ),
                        html.Div(
                            children=[
                                html.Div(
                                    children="Дата",
                                    className="menu-title"
                                ),
                                dcc.DatePickerRange(
                                    id="date-range",
                                    min_date_allowed=data.dateTime.min().date(),
                                    max_date_allowed=data.dateTime.max().date(),
                                    start_date=data.dateTime.min().date(),
                                    end_date=data.dateTime.max().date(),
                                ),
                            ]
                        ),
                    ],
                    className="menu-selects"
                ),
                html.Div(
                    children=[
                        html.Div(
                            children=[
                                html.Div(
                                    children="Город",
                                    className="menu-title"
                                ),
                                dcc.Dropdown(
                                    id="city-filter",
                                    options=[
                                        {"label": city_filter, "value": city_filter}
                                        for city_filter in np.sort(data.city.unique())
                                    ],
                                    multi=True,
                                    className="dropdown-city",
                                    style={'width':'885px'}
                                ),
                            ]
                        ),
                    ],
                    className="city-selects",
                ),
                html.Div(
                    children=[
                        html.Div(
                            children=
                            dcc.RadioItems(
                                id='candidate',
                                options=["Количество", "Максимальная цена", "Минимальная цена"],
                                labelClassName="date-group-labels",
                                className="date-group-items",
                                inline=True,
                                value='Количество'
                            ),
                            className="p-3",
                        ),
                    ],
                ),
            ],
            className="menu",
        ),

        html.Div(
            children=[
                html.Div(
                    children=dcc.Graph(
                        id="volume-chart", config={"displayModeBar": False},
                    ),
                    className="card",
                ),
                html.Div(
                    children=dcc.Graph(
                        id="brands", config={"displayModeBar": False},
                    ),
                    className="card",
                ),
            ],
            className="wrapper",
        ),
    ]
)


@app.callback(
    Output("type-filter", "options"),
    [
        Input("region-filter", "value"),
    ],
)
def update_dropdown(region):
    data['Vid'] = data['Vid'].fillna('Не определено')
    col_labels = data[data['category'] == region].Vid.unique()
    print(data[data['category'] == region].Vid.unique())
    return [{'label': i, 'value': i} for i in col_labels]


@app.callback(
    [Output("volume-chart", "figure"), Output("brands", "figure")],
    [
        Input("region-filter", "value"),
        Input("type-filter", "value"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
        Input("city-filter", "value"),
        Input("candidate", 'value')
    ],
)
def update_charts(region, product_type, start_date, end_date, city_filter, candidate):
    if product_type:
        if city_filter:
            mask = (
                    (data[data['category'] == region].Vid == product_type)
                    & (data.dateTime >= start_date)
                    & (data.dateTime <= end_date)
                    & (data['city'].isin(city_filter))
            )
        else:
            mask = (
                    (data[data['category'] == region].Vid == product_type)
                    & (data.dateTime >= start_date)
                    & (data.dateTime <= end_date)
            )
        filtered_data = data.loc[mask, :]
        if candidate == 'Количество':
            df12 = filtered_data[['city', 'items.quantity']]
            df12 = df12.groupby('city').sum()
            df12['count'] = df12['items.quantity']
        elif candidate == 'Максимальная цена':
            df12 = filtered_data[['city', 'items.price']]
            df12 = df12.groupby('city').max()
            df12['count'] = df12['items.price'] / 6
        elif candidate == 'Минимальная цена':
            df12 = filtered_data[['city', 'items.price']]
            df12 = df12.groupby('city').min()
            df12['count'] = df12['items.price'] / 6
        df12 = df12.join(city)
        fig = go.Figure(
            go.Scattermapbox(
                lat=df12['latitude'],
                lon=df12['longitude'],
                mode='markers',
                marker=go.scattermapbox.Marker(
                    size=df12['count'],
                    color=df12['count'],
                    colorscale=['#079A82', '#9D44B5']
                ),
                customdata=np.stack(
                    (pd.Series(df12.index),
                     df12[df12.columns[0]]),
                    axis=-1
                ),
                hovertemplate='<extra></extra> %{customdata[0]}<br>' + f'{candidate}' + ': %{customdata[1]}'
            )
        )
        fig.update_layout(
            width=1024,
            height=600,
            mapbox=dict(
                accesstoken=token,  #
                center=go.layout.mapbox.Center(lat=55, lon=51),
                zoom=5
            )
        )
        x = list(map(str.title, sorted(filtered_data.brand.unique())))
        y = []

        for i in sorted(filtered_data.brand.unique()):
            if candidate == 'Количество':
                y.append((filtered_data[filtered_data['brand'] == i]['items.quantity'].sum()))
            elif candidate == 'Максимальная цена':
                y.append((filtered_data[filtered_data['brand'] == i]['items.price'].max()))
            elif candidate == 'Минимальная цена':
                y.append((filtered_data[filtered_data['brand'] == i]['items.price'].min()))
        fig_brand = px.bar(x=x, y=y, height=600, width=1000, color_discrete_sequence=['#079A82'])

        return fig, fig_brand
    else:
        fig = go.Figure(
            go.Scattermapbox(

            )
        )
        fig.update_layout(
            width=1024,
            height=600,
            mapbox=dict(
                accesstoken=token,  #
                center=go.layout.mapbox.Center(lat=55, lon=51),
                zoom=5
            )
        )
        fig_brand = px.bar(height=600, width=1000)

        return fig, fig_brand

# C:\Users\Al's\PycharmProjects\clope3\ml_project\project\features\path_to_file.xlsx
