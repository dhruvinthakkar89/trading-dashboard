import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st
from datetime import datetime, timedelta
import yaml
from pathlib import Path

def load_data(file_path):
    """Load data from various file formats"""
    try:
        if file_path.endswith('.csv'):
            return pd.read_csv(file_path)
        elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
            return pd.read_excel(file_path)
        else:
            st.error("Unsupported file format. Please use CSV or Excel files.")
            return None
    except Exception as e:
        st.error(f"Error loading file: {str(e)}")
        return None

def validate_trading_data(df):
    """Validate trading data for required columns"""
    required_columns = ['date', 'symbol', 'quantity', 'price']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        st.warning(f"Missing required columns: {missing_columns}")
        return False
    
    # Check for data types
    if 'date' in df.columns:
        try:
            df['date'] = pd.to_datetime(df['date'])
        except:
            st.warning("Date column could not be converted to datetime")
            return False
    
    if 'quantity' in df.columns and 'price' in df.columns:
        if not (df['quantity'].dtype in ['int64', 'float64'] and 
                df['price'].dtype in ['int64', 'float64']):
            st.warning("Quantity and price columns should be numeric")
            return False
    
    return True

def calculate_pnl(df):
    """Calculate profit and loss from trading data"""
    if 'quantity' not in df.columns or 'price' not in df.columns:
        return df
    
    df['position_value'] = df['quantity'] * df['price']
    df['cumulative_position'] = df['quantity'].cumsum()
    df['cumulative_value'] = df['position_value'].cumsum()
    
    # Calculate P&L (simplified - assumes FIFO)
    df['pnl'] = 0.0
    for i in range(1, len(df)):
        if df.iloc[i]['quantity'] < 0:  # Selling
            # Calculate average cost from previous positions
            prev_positions = df.iloc[:i]
            if len(prev_positions) > 0:
                avg_cost = prev_positions['position_value'].sum() / prev_positions['quantity'].sum()
                df.iloc[i, df.columns.get_loc('pnl')] = (df.iloc[i]['price'] - avg_cost) * abs(df.iloc[i]['quantity'])
    
    return df

def create_trading_chart(df, symbol=None):
    """Create interactive trading chart"""
    if df.empty:
        return None
    
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        subplot_titles=('Price & Volume', 'Cumulative P&L'),
        row_width=[0.7, 0.3]
    )
    
    # Price chart
    if 'price' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df['date'] if 'date' in df.columns else df.index,
                y=df['price'],
                mode='lines+markers',
                name='Price',
                line=dict(color='blue')
            ),
            row=1, col=1
        )
    
    # Volume chart
    if 'quantity' in df.columns:
        colors = ['red' if q < 0 else 'green' for q in df['quantity']]
        fig.add_trace(
            go.Bar(
                x=df['date'] if 'date' in df.columns else df.index,
                y=df['quantity'].abs(),
                name='Volume',
                marker_color=colors
            ),
            row=1, col=1
        )
    
    # P&L chart
    if 'pnl' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df['date'] if 'date' in df.columns else df.index,
                y=df['pnl'].cumsum(),
                mode='lines',
                name='Cumulative P&L',
                line=dict(color='orange')
            ),
            row=2, col=1
        )
    
    fig.update_layout(
        title=f"Trading Analysis - {symbol if symbol else 'All Symbols'}",
        xaxis_title="Date",
        height=600,
        showlegend=True
    )
    
    return fig

def format_currency(value):
    """Format value as currency"""
    try:
        return f"${value:,.2f}"
    except:
        return str(value)

def format_percentage(value):
    """Format value as percentage"""
    try:
        return f"{value:.2f}%"
    except:
        return str(value)

def load_config():
    """Load application configuration"""
    config_path = Path(__file__).parent / "config" / "app.yaml"
    try:
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        return {}

def save_config(config):
    """Save application configuration"""
    config_path = Path(__file__).parent / "config" / "app.yaml"
    try:
        with open(config_path, 'w') as file:
            yaml.dump(config, file, default_flow_style=False)
        return True
    except Exception as e:
        st.error(f"Error saving configuration: {str(e)}")
        return False
