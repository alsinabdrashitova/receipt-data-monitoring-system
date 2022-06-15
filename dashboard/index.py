from app import app
from dash import Dash, dcc, html, Input, Output

from apps import vis, vis2


# app.layout = html.Div([
#     dcc.Location(id='url', refresh=False),
#     html.Div([
#         dcc.Link('Video Games|', href='/apps/vis'),
#         dcc.Link('Other Products', href='/apps/vis2'),
#     ], className="row"),
#     html.Div(id='page-content', children=[])
# ])
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])


@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/apps/vis':
        return vis.layout
    if pathname == '/apps/vis2':
        return vis2.layout
    else:
        return vis2.layout


if __name__ == '__main__':
    app.run_server("0.0.0.0", 8050, debug=True)