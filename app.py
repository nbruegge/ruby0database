import numpy as np
import sys
import os
import glob
import pandas as pd
import re
import dash
from dash.dependencies import Input, Output, State
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import json
from io import StringIO
import urllib.request
import plotly.express as px
import argparse

#parser = argparse.ArgumentParser(description='Setup dash table', formatter_class=argparse.RawTextHelpFormatter)
#
#parser.add_argument('--port', metavar='port', type=int, default=8050,
#                    help='port for python server')
#iopts = parser.parse_args()

def table_type(df_column):
    # Note - this only works with Pandas >= 1.0.0

    if sys.version_info < (3, 0):  # Pandas 1.0.0 does not support Python 2
        result = 'any'

    if   (isinstance(df_column, pd.DatetimeTZDtype) or
          isinstance(df_column, pd._libs.tslibs.timestamps.Timestamp)):
        result = 'datetime'
    elif (isinstance(df_column, str) or
    #elif (isinstance(df_column, pd.StringDtype) or
    #        isinstance(df_column, pd.BooleanDtype) or
            isinstance(df_column, pd.CategoricalDtype) or
            isinstance(df_column, pd.PeriodDtype)):
        result = 'text'
    elif (isinstance(df_column, pd.SparseDtype) or
            isinstance(df_column, pd.IntervalDtype) or
            isinstance(df_column, pd.Int8Dtype) or
            isinstance(df_column, pd.Int16Dtype) or
            isinstance(df_column, pd.Int32Dtype) or
            isinstance(df_column, pd.Int64Dtype)):
        result = 'numeric'
    else:
        result = 'any'
    #print(df_column, result)
    return result

# --- load csv
#df = pd.read_csv('./out_gather_parameter_new.csv')
df = pd.read_csv('csv/ruby0_db_v003.csv')
df = df.drop('Unnamed: 0', axis=1)

# --- add numbers to column name
cols = df.columns.tolist()
for nn, col in enumerate(cols):
  new_col = f'{nn} {col}' 
  df = df.rename({col: new_col}, axis='columns')

#df.columns = pd.MultiIndex.from_tuples(zip(np.arange(len(cols)), df.columns))

# --- save data base
#df.to_pickle('ruby0.pickle')

# --- finally copy data frame 
df_show = df.copy()

types = dict()
for i in df_show.columns:
  types[i] = table_type(df_show[i][0])
#print(types)
columns=[
    {'name': i, 'id': i, 'deletable': True, 'presentation': 'markdown', 'type': types[i]} for i in df_show.columns
    # omit the id column
    if i != 'id'
]
data = df_show.to_dict('records')

# --- for plotting data
df_plot = df.copy()
#new_cols = [
#   '9 GM', '10 Redi',
#   '14 AMOC [Sv]', '15 GMT [C]', '17 min/max vol.', '18 areaMax',
#]
new_cols = df_plot.columns.tolist()
for col in new_cols:
  df_plot[col] = pd.to_numeric(df_plot[col],errors='coerce')
available_indicators = new_cols

df_plot['0 run'] = df['0 run']
#df_plot['3 restart_filename'] = df['3 restart_filename']

# --- dash stuff
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
#app = dash.Dash(__name__) 

server = app.server

#app.layout = dash_table.DataTable(
#    id='table',
#    columns=[{"name": i, "id": i} for i in df.columns],
#    data=df.to_dict('records'),
#)
app.layout = html.Div([

    # --- heading
    html.H1(children='RUBY-0 overview'),

    # --- intro text
    html.Div(dcc.Markdown(children='''
        Overview of RUBY-0 experiments. See Jungclaus et al. for more details ([https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2021MS002813]).
    ''')),

    # --- column input
    html.Div("Choose which columns should be displayed (e.g. 1,3,5) and press 'Submit'!"),
    html.Div([
              dcc.Input(id='id_col_select', value='', type='text', style={'width':'30%'}),
              html.Button(id='submit-button-state', n_clicks=0, children='Submit'),
              html.Div(id='output-state'),
    ]),
    html.Div(id='my-output'),
    html.Br(),

    # --- querry reader
    dcc.RadioItems(
        id='filter-query-read-write',
        options=[
            {'label': 'Read filter_query', 'value': 'read'},
            {'label': 'Write to filter_query', 'value': 'write'}
        ],
        value='read'
    ),

    html.Br(),

    dcc.Input(id='filter-query-input', placeholder='Enter filter query'),

    html.Div(id='filter-query-output'),

    html.Hr(),

    #html.Div(id='id_div_table'),
    dash_table.DataTable(
        id='id_datatable',
        columns=columns,
        fixed_columns={'headers': True, 'data': 1},
        data=data,
        editable=True,
        page_action='native',
        #page_size=100,
        filter_action="native",
        sort_action="native",
        #css=[{
        #    'selector': 'table',
        #    'rule': 'table-layout: fixed; width: 200%'  # note - this does not work with fixed_rows
        #}],
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(248, 248, 248)'
            }
        ],
        style_header={
          'backgroundColor': 'rgb(230, 230, 230)',
          'fontWeight': 'bold'
        },
        style_table={'overflowX': 'scroll', 'maxWidth': '100%'},
    ),

    html.Hr(),
    html.Div(id='datatable-query-structure', style={'whitespace': 'pre'}),

    # --- for plotting
    html.Div(['xaxis: ',
        dcc.Dropdown(
            id='xaxis-column',
            options=[{'label': i, 'value': i} for i in available_indicators],
            value=available_indicators[0],
        ),
        dcc.RadioItems(
            id='xaxis-type',
            options=[{'label': i, 'value': i} for i in ['Linear', 'Log']],
            value='Linear',
            labelStyle={'display': 'inline-block'}
        )
    ],
    style={'width': '30%', 'display': 'inline-block'}),

    #html.Br(),

    html.Div(['yaxis: ',
        dcc.Dropdown(
            id='yaxis-column',
            options=[{'label': i, 'value': i} for i in available_indicators],
            value=available_indicators[1],
        ),
        dcc.RadioItems(
            id='yaxis-type',
            options=[{'label': i, 'value': i} for i in ['Linear', 'Log']],
            value='Linear',
            labelStyle={'display': 'inline-block'}
        )
    ],style={'width': '30%', 'display': 'inline-block'}),

    html.Br(),

    html.Div(['color: ',
        dcc.Dropdown(
            id='color-column',
            options=[{'label': i, 'value': i} for i in available_indicators],
            value=available_indicators[0],
        ),
    ],
    style={'width': '30%', 'display': 'inline-block'}),

    #html.Br(),

    html.Div(['size: ',
        dcc.Dropdown(
            id='size-column',
            options=[{'label': i, 'value': i} for i in available_indicators],
            value=available_indicators[1],
        ),
    ],style={'width': '30%', 'display': 'inline-block'}),

    html.Br(),

    html.Div([
    dcc.Graph(id='indicator-graphic'),
    ])
])

@app.callback(
    [Output('filter-query-input', 'style'),
     Output('filter-query-output', 'style')],
    [Input('filter-query-read-write', 'value')]
)
def query_input_output(val):
    input_style = {'width': '100%'}
    output_style = {}
    if val == 'read':
        input_style.update(display='none')
        output_style.update(display='inline-block')
    else:
        input_style.update(display='inline-block')
        output_style.update(display='none')
    return input_style, output_style


@app.callback([Output('id_datatable', 'data'),
               Output('id_datatable', 'columns'),
               Output('my-output', 'children')],
              [Input('submit-button-state', 'n_clicks')],
              [State('id_col_select', 'value')])
def update_output(n_clicks, input1):
    try:
      icols = [int(x) for x in input1.split(',')]
      df_show = df.iloc[:,icols]
      #result = u'''The Button has been pressed {} times, Input 1 is "{}"'''.format(n_clicks, input1)
      result = u'''Input 1 is "{}"'''.format(input1)
    except:
      result = f'Nothing is done: There was a problem with your input: {input1}'
      df_show = df.copy()
    if input1.replace(' ','')=='':
      result = 'No columns selected.'

    types = dict()
    for i in df_show.columns:
      types[i] = table_type(df_show[i][0])
    #print(types)
    columns=[
        {'name': i, 'id': i, 'deletable': True, 'presentation': 'markdown', 'type': types[i]} for i in df_show.columns
        if i != 'id'
    ]
    data = df_show.to_dict('records')
    return data, columns, result


@app.callback(
    Output('id_datatable', 'filter_query'),
    [Input('filter-query-input', 'value')]
)
def write_query(query):
    if query is None:
        return ''
    return query


@app.callback(
    Output('filter-query-output', 'children'),
    [Input('id_datatable', 'filter_query')]
)
def read_query(query):
    if query is None:
        return "No filter query"
    return dcc.Markdown('`filter_query = "{}"`'.format(query))


@app.callback(
    Output('datatable-query-structure', 'children'),
    [Input('id_datatable', 'derived_filter_query_structure')]
)
def display_query(query):
    if query is None:
        return ''
    return html.Details([
        html.Summary('Derived filter query structure'),
        html.Div(dcc.Markdown('''```json
{}
```'''.format(json.dumps(query, indent=4))))
    ])

# --- for plotting
@app.callback(
    Output('indicator-graphic', 'figure'),
    [Input('xaxis-column', 'value'),
     Input('yaxis-column', 'value'),
     Input('xaxis-type', 'value'),
     Input('yaxis-type', 'value'),
     Input('color-column', 'value'),
     Input('size-column', 'value'),
    ])
def update_graph(xaxis_column_name, yaxis_column_name,
                 xaxis_type, yaxis_type, 
                 color_column_name, size_column_name,
                 width=50, height=50,
                ):

    #fig = px.scatter(x=df_plot[xaxis_column_name],
    #                 y=df_plot[yaxis_column_name],
    #                 hover_name=df_plot['0 run'])
    fig = px.scatter(df, x=xaxis_column_name, y=yaxis_column_name, 
                     color=color_column_name,
                     #size=size_column_name, 
                     hover_data=['0 run']
                    )

    fig.update_layout(margin={'l': 40, 'b': 40, 't': 10, 'r': 0}, hovermode='closest')

    fig.update_xaxes(title=xaxis_column_name, 
                     type='linear' if xaxis_type == 'Linear' else 'log') 

    fig.update_yaxes(title=yaxis_column_name, 
                     type='linear' if yaxis_type == 'Linear' else 'log') 

    return fig

if __name__ == '__main__':
    app.run_server(debug=True,
                   #port=iopts.port,
                   #port=8050,
                  )
