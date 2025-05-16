import os
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import pandas as pd
from sqlalchemy import create_engine
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DB_USER = os.getenv('POSTGRES_USER', 'airflow')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'airflow')
DB_HOST = os.getenv('POSTGRES_HOST', 'postgres')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')
DB_NAME = os.getenv('POSTGRES_DB', 'stockdata')

# Create database connection
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)

# Initialize Dash app
app = dash.Dash(__name__)
app.title = "Stock Market Dashboard"

# Layout
app.layout = html.Div([
    html.H1("Real-Time Stock Market Dashboard"),
    
    # Stock selector
    html.Div([
        html.Label("Select Stock:"),
        dcc.Dropdown(
            id='stock-selector',
            options=[
                {'label': 'Apple (AAPL)', 'value': 'AAPL'},
                {'label': 'Google (GOOGL)', 'value': 'GOOGL'},
                {'label': 'Microsoft (MSFT)', 'value': 'MSFT'},
                {'label': 'Amazon (AMZN)', 'value': 'AMZN'},
                {'label': 'Meta (META)', 'value': 'META'},
                {'label': 'Tesla (TSLA)', 'value': 'TSLA'},
                {'label': 'NVIDIA (NVDA)', 'value': 'NVDA'},
                {'label': 'Netflix (NFLX)', 'value': 'NFLX'},
                {'label': 'AMD (AMD)', 'value': 'AMD'},
                {'label': 'Intel (INTC)', 'value': 'INTC'}
            ],
            value='AAPL'
        )
    ], style={'width': '30%', 'margin': '10px'}),
    
    # Time range selector
    html.Div([
        html.Label("Select Time Range:"),
        dcc.RadioItems(
            id='timeframe-selector',
            options=[
                {'label': '5 Minutes', 'value': '5min'},
                {'label': '15 Minutes', 'value': '15min'},
                {'label': '1 Hour', 'value': '1hour'},
                {'label': '1 Day', 'value': '1day'}
            ],
            value='15min'
        )
    ], style={'margin': '10px'}),
    
    # Price chart
    html.Div([
        html.H3("Price Chart"),
        dcc.Graph(id='price-chart')
    ]),
    
    # Volume chart
    html.Div([
        html.H3("Volume Chart"),
        dcc.Graph(id='volume-chart')
    ]),
    
    # Anomalies table
    html.Div([
        html.H3("Recent Anomalies"),
        html.Div(id='anomalies-table')
    ]),
    
    # Auto-refresh
    dcc.Interval(
        id='interval-component',
        interval=5*1000,  # in milliseconds
        n_intervals=0
    )
])

def get_timeframe_delta(timeframe):
    """Convert timeframe selection to timedelta"""
    if timeframe == '5min':
        return timedelta(minutes=5)
    elif timeframe == '15min':
        return timedelta(minutes=15)
    elif timeframe == '1hour':
        return timedelta(hours=1)
    else:  # 1day
        return timedelta(days=1)

@app.callback(
    [Output('price-chart', 'figure'),
     Output('volume-chart', 'figure'),
     Output('anomalies-table', 'children')],
    [Input('interval-component', 'n_intervals'),
     Input('stock-selector', 'value'),
     Input('timeframe-selector', 'value')]
)
def update_graphs(n, symbol, timeframe):
    """Update all graphs based on selected stock and timeframe"""
    try:
        # Calculate time range
        end_time = datetime.now()
        start_time = end_time - get_timeframe_delta(timeframe)
        
        # Fetch price data
        price_query = f"""
            SELECT timestamp, price, volume
            FROM stock_prices
            WHERE symbol = '{symbol}'
            AND timestamp BETWEEN '{start_time}' AND '{end_time}'
            ORDER BY timestamp
        """
        df = pd.read_sql(price_query, engine)
        
        # Create price chart
        price_chart = {
            'data': [{
                'x': df['timestamp'],
                'y': df['price'],
                'type': 'line',
                'name': f'{symbol} Price'
            }],
            'layout': {
                'title': f'{symbol} Price Over Time',
                'xaxis': {'title': 'Time'},
                'yaxis': {'title': 'Price ($)'}
            }
        }
        
        # Create volume chart
        volume_chart = {
            'data': [{
                'x': df['timestamp'],
                'y': df['volume'],
                'type': 'bar',
                'name': f'{symbol} Volume'
            }],
            'layout': {
                'title': f'{symbol} Trading Volume',
                'xaxis': {'title': 'Time'},
                'yaxis': {'title': 'Volume'}
            }
        }
        
        # Fetch anomalies
        anomalies_query = f"""
            SELECT timestamp, alert_type, value
            FROM anomalies
            WHERE symbol = '{symbol}'
            AND timestamp >= NOW() - INTERVAL '1 hour'
            ORDER BY timestamp DESC
            LIMIT 5
        """
        anomalies_df = pd.read_sql(anomalies_query, engine)
        
        # Create anomalies table
        anomalies_table = html.Table([
            html.Thead(html.Tr([
                html.Th("Time"),
                html.Th("Alert Type"),
                html.Th("Value")
            ])),
            html.Tbody([
                html.Tr([
                    html.Td(row['timestamp'].strftime('%H:%M:%S')),
                    html.Td(row['alert_type']),
                    html.Td(f"{row['value']:.2f}")
                ]) for _, row in anomalies_df.iterrows()
            ])
        ])
        
        return price_chart, volume_chart, anomalies_table
        
    except Exception as e:
        logger.error(f"Error updating dashboard: {str(e)}")
        return {}, {}, html.Div("Error loading data")

if __name__ == '__main__':
    app.run_server(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 8050)),
        debug=False
    ) 