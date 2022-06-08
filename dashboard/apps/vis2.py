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
import plotly.express as px
from dash.dependencies import Input, Output

data = pd.read_excel("data.xlsx", sheet_name='Sheet1')
data = data.iloc[:, 1:]
data["dateTime"] = pd.to_datetime(data["dateTime"], format="%Y-%m-%d")
data.sort_values("dateTime", inplace=True)
city = data[['city']].drop_duplicates(['city'])
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
                html.H3(children='Анализ продаж проудкта',
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


#
# city[['latitude', 'longitude']] = city.city.apply(lambda x: custom_geocoder(x))
# city = city.set_index(['city'])

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
                        get_navbar('page2'),
                    ]
                ),
                html.Div(
                    children=[
                        html.Div(
                            children=[
                                html.Div(children="Товар", className="menu-title"),
                                dcc.Dropdown(
                                    id="region-filter",
                                    options=[
                                        {
                                            "label": f'{str(data[data["clusters_count"] == cluster]["Vid"].to_list()[0]).title()}, {str(data[data["clusters_count"] == cluster]["brand"].to_list()[0]).title()}',
                                            "value": cluster}
                                        for cluster in np.sort(data.clusters_count.unique())
                                    ],
                                    # clearable=False,
                                    className="dropdown",
                                    style={'width': '300px'},
                                    searchable=True
                                ),
                            ]
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
                            ],
                            style={'width': '315px'}
                        ),
                    ],
                    className="menu-selects",
                ),
                html.Div(
                    children=[
                        html.Div(
                            children=[
                                html.Div(
                                    children="Место покупки",
                                    className="menu-title"
                                ),
                                dcc.Dropdown(
                                    id="city-filter",
                                    options=[
                                        {"label": city_filter.replace('Республика Татарстан, ', ''),
                                         "value": city_filter}
                                        for city_filter in np.sort(data.city.unique())
                                    ],
                                    value=['Республика Татарстан, Буинский район',
                                           'Республика Татарстан, Тетюшский район',
                                           'Республика Татарстан, Альметьевский район'],
                                    multi=True,
                                    className="dropdown-city",
                                    style={'width': '885px'}
                                ),
                            ]
                        ),
                    ],
                    className="city-selects",
                    style={'width': '885px'}
                ),
                html.Div(
                    children=[
                        html.Div(
                            children=
                            dcc.RadioItems(
                                id='candidate',
                                options=["Количество", "Цена"],
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
                        id="prod_an", config={"displayModeBar": False},
                    ),
                    className="prod_an",
                ),
            ],
            className="wrapper",
        ),
    ]
)


@app.callback(
    Output("prod_an", "figure"),
    [
        Input("region-filter", "value"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
        Input("city-filter", "value"),
        Input("candidate", 'value')
    ],
)
def update_charts(cluster, start_date, end_date, city_filter, candidate):
    print(cluster)
    print(type(cluster))
    if cluster:
        if city_filter:
            mask = (
                    (data.clusters_count == cluster)
                    & (data.dateTime >= start_date)
                    & (data.dateTime <= end_date)
                    & (data['city'].isin(city_filter))
            )
        else:
            mask = (
                    (data.clusters_count == cluster)
                    & (data.dateTime >= start_date)
                    & (data.dateTime <= end_date)
            )
        filtered_data = data.loc[mask, :]
        print(filtered_data)
        if candidate == 'Цена':
            fig = px.line(filtered_data, x='dateTime', y='items.price', markers=True, color='city', height=600,
                          width=1000)
            fig.update_traces(textposition='bottom right')
            fig.update_layout(xaxis_title='Дата', yaxis_title='Цена')
        else:
            new_dat = pd.DataFrame(columns=['city', 'count', 'dateTime'])
            for i in filtered_data.city.unique():
                mask_filt = (
                    (filtered_data.city == i)
                )
                cities = filtered_data.loc[mask_filt, :]
                print(cities)
                for j in filtered_data.dateTime.unique():
                    new_dat = new_dat.append(
                        pd.Series([i, cities[cities['dateTime'] == j]['items.quantity'].sum(), j], new_dat.columns),
                        ignore_index=True)
                    # new_dat['count'] = cities[cities['dateTime'] == j]['items.quantity'].sum()
                    print(new_dat)
            fig = px.line(new_dat, x='dateTime', y='count', color='city', markers=True, height=600, width=1000)
            fig.update_layout(xaxis_title='Дата', yaxis_title='Количество')
            fig.update_traces(textposition='bottom right')
        return fig

    else:
        fig_brand = px.bar(height=600, width=1000)

        return fig_brand