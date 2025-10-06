# Trading Performance Dashboard

A comprehensive Streamlit application for tracking trading performance across multiple clients.

## Features

- Multi-client support with role-based access
- Capital account tracking with investor share calculations
- Strategy analysis with S&P 500 comparison
- Trade upload and management
- Client management and configuration

## Deployment

This app is ready for deployment on Streamlit Cloud, Heroku, or any cloud platform.

## Setup

1. Install dependencies: `pip install -r requirements.txt`
2. Run the app: `streamlit run app.py`
3. Access at `http://localhost:8501`

## Default Admin Login

- Username: `admin`
- Password: `Smita@280135`

## Data Structure

The app expects the following data directory structure:
```
data/
├── users.json
├── sessions.json
├── config.json
├── trades.csv
├── clients.csv
├── capital_movements.csv
└── monthly_capital.json
```