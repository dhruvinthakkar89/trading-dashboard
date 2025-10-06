import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import streamlit as st

class TradingDataManager:
    def __init__(self):
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        # File paths
        self.trades_file = self.data_dir / "trades.csv"
        self.clients_file = self.data_dir / "clients.csv"
        self.capital_movements_file = self.data_dir / "capital_movements.csv"
        self.monthly_capital_file = self.data_dir / "monthly_capital.csv"
        self.config_file = self.data_dir / "config.json"
        
        # Initialize data structures
        self._load_config()
        self._load_trades()
        self._load_clients()
        self._load_capital_movements()
        self._load_monthly_capital()
    
    def _load_config(self):
        """Load configuration settings"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                import json
                old_config = json.load(f)
                
            # Migrate old config format to new format
            if "global" not in old_config and "clients" not in old_config:
                # This is the old format, migrate it
                self.config = {
                    "global": {
                        "tax_rate": old_config.get("tax_rate", 0.25),
                        "trader_share": old_config.get("trader_share", 0.40),
                        "investor_share": old_config.get("investor_share", 0.60),
                        "auto_remove_day_trades": old_config.get("auto_remove_day_trades", True)
                    },
                    "clients": {}
                }
                self._save_config()  # Save in new format
            else:
                # Already in new format
                self.config = old_config
        else:
            # Default configuration structure
            self.config = {
                "global": {
                    "tax_rate": 0.25,
                    "trader_share": 0.40,
                    "investor_share": 0.60,
                    "auto_remove_day_trades": True,
                    "enable_sp500_comparison": True
                },
                "clients": {}
            }
            self._save_config()
    
    def _save_config(self):
        """Save configuration settings"""
        with open(self.config_file, 'w') as f:
            import json
            json.dump(self.config, f, indent=2)
    
    def _load_trades(self):
        """Load trades data"""
        if self.trades_file.exists():
            self.trades_df = pd.read_csv(self.trades_file)
            self.trades_df['buy_date'] = pd.to_datetime(self.trades_df['buy_date'])
            self.trades_df['sell_date'] = pd.to_datetime(self.trades_df['sell_date'])
        else:
            # Create sample trades structure
            self.trades_df = pd.DataFrame({
                'trade_id': [],
                'buy_date': [],
                'sell_date': [],
                'stock': [],
                'buy_price': [],
                'sell_price': [],
                'quantity': [],
                'profit_loss': [],
                'position_size': [],
                'return_pct': [],
                'win_loss': []
            })
            self._save_trades()
    
    def _load_clients(self):
        """Load clients data"""
        if self.clients_file.exists():
            self.clients_df = pd.read_csv(self.clients_file)
        else:
            # Create sample clients structure
            self.clients_df = pd.DataFrame({
                'client_id': [],
                'username': [],
                'name': [],
                'email': [],
                'starting_capital': [],
                'active': []
            })
            self._save_clients()
        # After loading, merge-in any clients from users.json so UI shows all
        self.sync_clients_from_users()
    
    def _load_capital_movements(self):
        """Load capital movements data"""
        if self.capital_movements_file.exists():
            self.capital_movements_df = pd.read_csv(self.capital_movements_file)
            self.capital_movements_df['date'] = pd.to_datetime(self.capital_movements_df['date'])
        else:
            # Create sample capital movements structure
            self.capital_movements_df = pd.DataFrame({
                'movement_id': [],
                'client_id': [],
                'date': [],
                'type': [],  # 'contribution' or 'withdrawal'
                'amount': [],
                'notes': []
            })
            self._save_capital_movements()
    
    def _save_trades(self):
        """Save trades data"""
        self.trades_df.to_csv(self.trades_file, index=False)
    
    def _save_clients(self):
        """Save clients data"""
        self.clients_df.to_csv(self.clients_file, index=False)
    
    def _save_capital_movements(self):
        """Save capital movements data"""
        self.capital_movements_df.to_csv(self.capital_movements_file, index=False)
    
    def upload_trades(self, file):
        """Upload and process trade log"""
        try:
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            elif file.name.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file)
            else:
                return False, "Unsupported file format"
            
            # Normalize headers to accept variants like "Buy Date", "Sell Price", etc.
            def _normalize(name):
                return ''.join(ch for ch in name.lower() if ch.isalnum())

            header_map = {}
            for c in df.columns:
                key = _normalize(c)
                if key in {
                    'buydate', 'selldate', 'stock', 'buyprice', 'sellprice', 'quantity'
                }:
                    if key == 'buydate':
                        header_map[c] = 'buy_date'
                    elif key == 'selldate':
                        header_map[c] = 'sell_date'
                    elif key == 'stock':
                        header_map[c] = 'stock'
                    elif key == 'buyprice':
                        header_map[c] = 'buy_price'
                    elif key == 'sellprice':
                        header_map[c] = 'sell_price'
                    elif key == 'quantity':
                        header_map[c] = 'quantity'

            if header_map:
                df = df.rename(columns=header_map)

            # Validate required columns (canonical names)
            required_columns = ['buy_date', 'sell_date', 'stock', 'buy_price', 'sell_price', 'quantity']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                return False, f"Missing required columns: {missing_columns}. Accepted headers include: Buy Date, Sell Date, Stock, Buy Price, Sell Price, Quantity"
            
            # Process trades
            df['buy_date'] = pd.to_datetime(df['buy_date'])
            df['sell_date'] = pd.to_datetime(df['sell_date'])
            
            # Calculate derived fields
            df['profit_loss'] = (df['sell_price'] - df['buy_price']) * df['quantity']
            df['position_size'] = df['buy_price'] * df['quantity']
            df['return_pct'] = (df['sell_price'] - df['buy_price']) / df['buy_price'] * 100
            df['win_loss'] = df['profit_loss'].apply(lambda x: 'Win' if x > 0 else 'Loss')
            
            # Add trade ID if not present
            if 'trade_id' not in df.columns:
                df['trade_id'] = [f"TRADE_{i+1:04d}" for i in range(len(df))]
            
            # Remove day trades if configured
            if self.get_config()['auto_remove_day_trades']:
                day_trades_count = len(df[df['buy_date'] == df['sell_date']])
                df = df[df['buy_date'] != df['sell_date']]
                if day_trades_count > 0:
                    st.info(f"Removed {day_trades_count} day trades")
            
            # Handle duplicates - remove duplicates based on key fields
            # Create a unique identifier for each trade
            df['trade_signature'] = (
                df['buy_date'].astype(str) + '_' + 
                df['sell_date'].astype(str) + '_' + 
                df['stock'].astype(str) + '_' + 
                df['buy_price'].astype(str) + '_' + 
                df['sell_price'].astype(str) + '_' + 
                df['quantity'].astype(str)
            )
            
            # If there are existing trades, remove duplicates
            if not self.trades_df.empty:
                # Create trade signature for existing trades
                existing_trades = self.trades_df.copy()
                existing_trades['trade_signature'] = (
                    existing_trades['buy_date'].astype(str) + '_' + 
                    existing_trades['sell_date'].astype(str) + '_' + 
                    existing_trades['stock'].astype(str) + '_' + 
                    existing_trades['buy_price'].astype(str) + '_' + 
                    existing_trades['sell_price'].astype(str) + '_' + 
                    existing_trades['quantity'].astype(str)
                )
                
                # Find duplicates in the new data
                duplicates_in_new = df['trade_signature'].isin(existing_trades['trade_signature'])
                duplicate_count = duplicates_in_new.sum()
                
                if duplicate_count > 0:
                    st.warning(f"Found {duplicate_count} duplicate trades. Removing duplicates...")
                    df = df[~duplicates_in_new]
                
                # Remove duplicates within the new data itself
                df = df.drop_duplicates(subset=['trade_signature'], keep='first')
                
                # Combine with existing trades
                self.trades_df = pd.concat([existing_trades.drop('trade_signature', axis=1), df.drop('trade_signature', axis=1)], ignore_index=True)
            else:
                # No existing trades, just remove internal duplicates
                df = df.drop_duplicates(subset=['trade_signature'], keep='first')
                self.trades_df = df.drop('trade_signature', axis=1)
            
            self._save_trades()
            
            return True, f"Successfully uploaded {len(df)} trades (duplicates removed)"
            
        except Exception as e:
            return False, f"Error processing file: {str(e)}"
    
    def get_monthly_strategy_returns(self, client_id=None):
        """Calculate monthly strategy returns based on client capital, not position size"""
        if self.trades_df.empty:
            return pd.DataFrame()
        
        # Filter trades by client investment start date if client_id is provided
        trades_df = self.trades_df.copy()
        
        if client_id:
            # Get client investment start date
            client_info = self.clients_df[self.clients_df['client_id'] == client_id]
            if not client_info.empty and 'investment_start_date' in client_info.columns:
                investment_start_date = client_info['investment_start_date'].iloc[0]
                if not pd.isna(investment_start_date):
                    # Convert to datetime if needed
                    if hasattr(investment_start_date, 'strftime'):
                        investment_start_date = investment_start_date.strftime('%Y-%m-%d')
                    
                    investment_start = pd.to_datetime(investment_start_date)
                    # Filter trades to only include those from investment start date onwards
                    trades_df = trades_df[trades_df['sell_date'] >= investment_start]
        
        if trades_df.empty:
            return pd.DataFrame()
        
        # Group by month
        trades_df['month'] = trades_df['sell_date'].dt.to_period('M')
        
        monthly_stats = trades_df.groupby('month').agg({
            'profit_loss': 'sum',
            'trade_id': 'count',
            'win_loss': lambda x: (x == 'Win').sum()
        }).reset_index()
        
        monthly_stats.columns = ['Month', 'Total_PL', 'Total_Trades', 'Winning_Trades']
        monthly_stats['Month'] = monthly_stats['Month'].astype(str)
        monthly_stats['Win_Rate'] = (monthly_stats['Winning_Trades'] / monthly_stats['Total_Trades'] * 100).round(2)
        
        # Calculate return percentage based on client capital for each month
        monthly_stats['Client_Capital'] = monthly_stats['Month'].apply(lambda x: self.get_monthly_capital(x))
        monthly_stats['Return_Pct'] = (monthly_stats['Total_PL'] / monthly_stats['Client_Capital'] * 100).round(2)
        # Replace any infinite or NaN values with 0
        monthly_stats['Return_Pct'] = monthly_stats['Return_Pct'].fillna(0).replace([float('inf'), float('-inf')], 0)
        
        # Calculate average win percentage for winning trades
        def get_avg_win_pct(month_period):
            month_trades = self.trades_df[self.trades_df['sell_date'].dt.to_period('M') == month_period]
            winning_trades = month_trades[month_trades['win_loss'] == 'Win']
            if not winning_trades.empty:
                win_pcts = ((winning_trades['sell_price'] - winning_trades['buy_price']) / winning_trades['buy_price'] * 100)
                return win_pcts.mean()
            return 0
        
        # Calculate average loss percentage for losing trades
        def get_avg_loss_pct(month_period):
            month_trades = self.trades_df[self.trades_df['sell_date'].dt.to_period('M') == month_period]
            losing_trades = month_trades[month_trades['win_loss'] == 'Loss']
            if not losing_trades.empty:
                loss_pcts = ((losing_trades['sell_price'] - losing_trades['buy_price']) / losing_trades['buy_price'] * 100)
                return loss_pcts.mean()
            return 0
        
        monthly_stats['Avg_Win_Pct'] = monthly_stats['Month'].apply(lambda x: round(get_avg_win_pct(pd.to_datetime(x).to_period('M')), 2))
        monthly_stats['Avg_Loss_Pct'] = monthly_stats['Month'].apply(lambda x: round(get_avg_loss_pct(pd.to_datetime(x).to_period('M')), 2))
        
        # Calculate cumulative return as actual percentage addition
        monthly_stats['Cumulative_Return'] = monthly_stats['Return_Pct'].cumsum()
        
        return monthly_stats
    
    def get_biweekly_strategy_returns(self, client_id=None):
        """Calculate biweekly strategy returns based on client capital, not position size"""
        if self.trades_df.empty:
            return pd.DataFrame()
        
        # Filter trades by client investment start date if client_id is provided
        trades_df = self.trades_df.copy()
        
        if client_id:
            # Get client investment start date
            client_info = self.clients_df[self.clients_df['client_id'] == client_id]
            if not client_info.empty and 'investment_start_date' in client_info.columns:
                investment_start_date = client_info['investment_start_date'].iloc[0]
                if not pd.isna(investment_start_date):
                    # Convert to datetime if needed
                    if hasattr(investment_start_date, 'strftime'):
                        investment_start_date = investment_start_date.strftime('%Y-%m-%d')
                    
                    investment_start = pd.to_datetime(investment_start_date)
                    # Filter trades to only include those from investment start date onwards
                    trades_df = trades_df[trades_df['sell_date'] >= investment_start]
        
        if trades_df.empty:
            return pd.DataFrame()
        
        # Group by biweekly periods (every 2 weeks)
        trades_df['biweek'] = trades_df['sell_date'].dt.to_period('2W')
        
        biweekly_stats = trades_df.groupby('biweek').agg({
            'profit_loss': 'sum',
            'trade_id': 'count',
            'win_loss': lambda x: (x == 'Win').sum()
        }).reset_index()
        
        biweekly_stats.columns = ['Period', 'Total_PL', 'Total_Trades', 'Winning_Trades']
        
        # Create better period labels (e.g., "Jun 1", "Jun 15" for biweekly periods)
        def format_period_label(period_str):
            try:
                # Extract start date from period string
                start_date_str = period_str.split('/')[0]
                start_date = pd.to_datetime(start_date_str)
                return start_date.strftime('%b %d')
            except:
                return period_str
        
        biweekly_stats['Period_Label'] = biweekly_stats['Period'].apply(format_period_label)
        biweekly_stats['Period'] = biweekly_stats['Period'].astype(str)
        biweekly_stats['Win_Rate'] = (biweekly_stats['Winning_Trades'] / biweekly_stats['Total_Trades'] * 100).round(2)
        
        # Calculate return percentage based on client capital for each biweekly period
        biweekly_stats['Client_Capital'] = biweekly_stats['Period'].apply(lambda x: self.get_biweekly_capital(x))
        biweekly_stats['Return_Pct'] = (biweekly_stats['Total_PL'] / biweekly_stats['Client_Capital'] * 100).round(2)
        # Replace any infinite or NaN values with 0
        biweekly_stats['Return_Pct'] = biweekly_stats['Return_Pct'].fillna(0).replace([float('inf'), float('-inf')], 0)
        
        # Calculate average win percentage for winning trades
        def get_avg_win_pct_biweekly(period_str):
            try:
                start_date_str = period_str.split('/')[0]
                period_dt = pd.to_datetime(start_date_str)
                period_period = period_dt.to_period('2W')
            except:
                return 0
            
            period_trades = self.trades_df[self.trades_df['sell_date'].dt.to_period('2W') == period_period]
            winning_trades = period_trades[period_trades['win_loss'] == 'Win']
            if not winning_trades.empty:
                win_pcts = ((winning_trades['sell_price'] - winning_trades['buy_price']) / winning_trades['buy_price'] * 100)
                return win_pcts.mean()
            return 0
        
        # Calculate average loss percentage for losing trades
        def get_avg_loss_pct_biweekly(period_str):
            try:
                start_date_str = period_str.split('/')[0]
                period_dt = pd.to_datetime(start_date_str)
                period_period = period_dt.to_period('2W')
            except:
                return 0
            
            period_trades = self.trades_df[self.trades_df['sell_date'].dt.to_period('2W') == period_period]
            losing_trades = period_trades[period_trades['win_loss'] == 'Loss']
            if not losing_trades.empty:
                loss_pcts = ((losing_trades['sell_price'] - losing_trades['buy_price']) / losing_trades['buy_price'] * 100)
                return loss_pcts.mean()
            return 0
        
        biweekly_stats['Avg_Win_Pct'] = biweekly_stats['Period'].apply(lambda x: round(get_avg_win_pct_biweekly(x), 2))
        biweekly_stats['Avg_Loss_Pct'] = biweekly_stats['Period'].apply(lambda x: round(get_avg_loss_pct_biweekly(x), 2))
        
        # Calculate cumulative return as actual percentage addition
        biweekly_stats['Cumulative_Return'] = biweekly_stats['Return_Pct'].cumsum()
        
        return biweekly_stats
    
    def get_daily_strategy_returns(self):
        """Calculate daily strategy returns based on client capital, not position size"""
        if self.trades_df.empty:
            return pd.DataFrame()
        
        # Group by daily periods
        self.trades_df['day'] = self.trades_df['sell_date'].dt.to_period('D')
        
        daily_stats = self.trades_df.groupby('day').agg({
            'profit_loss': 'sum',
            'position_size': 'sum',
            'trade_id': 'count',
            'win_loss': lambda x: (x == 'Win').sum()
        }).reset_index()
        
        daily_stats.columns = ['Period', 'Total_PL', 'Total_Position_Size', 'Total_Trades', 'Winning_Trades']
        
        # Create better period labels (e.g., "Jun 1", "Jun 2" for daily periods)
        def format_daily_label(period_str):
            try:
                # Extract start date from period string
                start_date_str = period_str.split('/')[0]
                start_date = pd.to_datetime(start_date_str)
                return start_date.strftime('%b %d')
            except:
                return period_str
        
        daily_stats['Period_Label'] = daily_stats['Period'].apply(format_daily_label)
        daily_stats['Period'] = daily_stats['Period'].astype(str)
        daily_stats['Win_Rate'] = (daily_stats['Winning_Trades'] / daily_stats['Total_Trades'] * 100).round(2)
        
        # Calculate return percentage based on total position size for each daily period
        # This is more reliable than trying to estimate client capital
        daily_stats['Return_Pct'] = (daily_stats['Total_PL'] / daily_stats['Total_Position_Size'] * 100).round(2)
        # Replace any infinite or NaN values with 0
        daily_stats['Return_Pct'] = daily_stats['Return_Pct'].fillna(0).replace([float('inf'), float('-inf')], 0)
        
        # Calculate cumulative return
        daily_stats['Cumulative_Return'] = (1 + daily_stats['Return_Pct'] / 100).cumprod()
        
        return daily_stats
    
    def get_weekly_cumulative_returns(self):
        """Calculate weekly cumulative returns from trades"""
        if self.trades_df.empty:
            return pd.DataFrame()
        
        # Convert dates to datetime
        trades_df = self.trades_df.copy()
        trades_df['buy_date'] = pd.to_datetime(trades_df['buy_date'])
        trades_df['sell_date'] = pd.to_datetime(trades_df['sell_date'])
        
        # Create weekly aggregation
        trades_df['week'] = trades_df['sell_date'].dt.to_period('W')
        
        # Group by week and calculate returns
        weekly_stats = trades_df.groupby('week').agg({
            'profit_loss': 'sum',
            'position_size': 'sum',
            'win_loss': lambda x: (x == 'Win').sum(),
            'trade_id': 'count'
        }).reset_index()
        
        weekly_stats.columns = ['Week', 'Total_PL', 'Total_Position_Size', 'Winning_Trades', 'Total_Trades']
        
        # Calculate weekly return percentage
        weekly_stats['Weekly_Return_Pct'] = (weekly_stats['Total_PL'] / weekly_stats['Total_Position_Size'] * 100).fillna(0)
        
        # Calculate cumulative return
        weekly_stats['Cumulative_Return'] = (1 + weekly_stats['Weekly_Return_Pct'] / 100).cumprod()
        weekly_stats['Cumulative_Return_Pct'] = (weekly_stats['Cumulative_Return'] - 1) * 100
        
        # Convert week to string for display
        weekly_stats['Week'] = weekly_stats['Week'].astype(str)
        
        return weekly_stats[['Week', 'Total_Trades', 'Winning_Trades', 'Weekly_Return_Pct', 'Cumulative_Return_Pct']]
    
    def get_strategy_summary(self, client_id=None):
        """Get overall strategy summary"""
        if self.trades_df.empty:
            return {}
        
        # Filter trades by client investment start date if client_id is provided
        trades_df = self.trades_df.copy()
        
        if client_id:
            # Get client investment start date
            client_info = self.clients_df[self.clients_df['client_id'] == client_id]
            if not client_info.empty and 'investment_start_date' in client_info.columns:
                investment_start_date = client_info['investment_start_date'].iloc[0]
                if not pd.isna(investment_start_date):
                    # Convert to datetime if needed
                    if hasattr(investment_start_date, 'strftime'):
                        investment_start_date = investment_start_date.strftime('%Y-%m-%d')
                    
                    investment_start = pd.to_datetime(investment_start_date)
                    # Filter trades to only include those from investment start date onwards
                    trades_df = trades_df[trades_df['sell_date'] >= investment_start]
        
        if trades_df.empty:
            return {}
        
        total_trades = len(trades_df)
        winning_trades = len(trades_df[trades_df['win_loss'] == 'Win'])
        losing_trades = total_trades - winning_trades
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Calculate total P&L
        total_pl = trades_df['profit_loss'].sum()
        
        # Calculate total position size
        total_position_size = trades_df['position_size'].sum()
        
        # Calculate average win/loss amounts
        winning_trades_df = trades_df[trades_df['profit_loss'] > 0]
        losing_trades_df = trades_df[trades_df['profit_loss'] < 0]
        
        if not winning_trades_df.empty:
            avg_winner = winning_trades_df['profit_loss'].mean()
            # Calculate average win percentage based on buy price
            avg_winner_pct = ((winning_trades_df['sell_price'] - winning_trades_df['buy_price']) / winning_trades_df['buy_price'] * 100).mean()
        else:
            avg_winner = 0
            avg_winner_pct = 0
            
        if not losing_trades_df.empty:
            avg_loser = losing_trades_df['profit_loss'].mean()
            # Calculate average loss percentage based on buy price
            avg_loser_pct = ((losing_trades_df['sell_price'] - losing_trades_df['buy_price']) / losing_trades_df['buy_price'] * 100).mean()
        else:
            avg_loser = 0
            avg_loser_pct = 0
        
        # Calculate overall return percentage
        if total_position_size > 0:
            overall_return = (total_pl / total_position_size * 100)
        else:
            overall_return = 0
        
        # Calculate cumulative return from monthly returns
        monthly_returns = self.get_monthly_strategy_returns()
        if not monthly_returns.empty:
            # Get the last cumulative return value (now already in percentage)
            cumulative_return_pct = monthly_returns['Cumulative_Return'].iloc[-1]
        else:
            cumulative_return_pct = 0
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': round(win_rate, 2),
            'total_pl': round(total_pl, 2),
            'total_position_size': round(total_position_size, 2),
            'avg_winner': round(avg_winner, 2),
            'avg_loser': round(avg_loser, 2),
            'avg_winner_pct': round(avg_winner_pct, 2),
            'avg_loser_pct': round(avg_loser_pct, 2),
            'overall_return': round(overall_return, 2),
            'cumulative_return': round(cumulative_return_pct, 2)
        }
    
    def add_capital_movement(self, client_id, movement_type, amount, date, notes=""):
        """Add capital contribution or withdrawal"""
        movement_id = f"MOV_{len(self.capital_movements_df) + 1:04d}"
        
        new_movement = pd.DataFrame({
            'movement_id': [movement_id],
            'client_id': [client_id],
            'date': [pd.to_datetime(date)],
            'type': [movement_type],
            'amount': [amount],
            'notes': [notes]
        })
        
        self.capital_movements_df = pd.concat([self.capital_movements_df, new_movement], ignore_index=True)
        self._save_capital_movements()
        return True
    
    def _load_monthly_capital(self):
        """Load monthly capital allocations"""
        if self.monthly_capital_file.exists():
            self.monthly_capital_df = pd.read_csv(self.monthly_capital_file)
            self.monthly_capital_df['month'] = pd.to_datetime(self.monthly_capital_df['month'])
        else:
            # Create sample monthly capital structure
            self.monthly_capital_df = pd.DataFrame({
                'month': [],
                'total_capital': [],
                'notes': []
            })
            self._save_monthly_capital()
    
    def _save_monthly_capital(self):
        """Save monthly capital allocations"""
        self.monthly_capital_df.to_csv(self.monthly_capital_file, index=False)
    
    def set_monthly_capital(self, month, total_capital, notes=""):
        """Set total capital for a specific month"""
        month_dt = pd.to_datetime(month)
        
        # Remove existing entry for this month
        self.monthly_capital_df = self.monthly_capital_df[self.monthly_capital_df['month'].dt.to_period('M') != month_dt.to_period('M')]
        
        # Add new entry
        new_entry = pd.DataFrame({
            'month': [month_dt],
            'total_capital': [total_capital],
            'notes': [notes]
        })
        
        self.monthly_capital_df = pd.concat([self.monthly_capital_df, new_entry], ignore_index=True)
        self.monthly_capital_df = self.monthly_capital_df.sort_values('month')
        self._save_monthly_capital()
        return True
    
    def get_monthly_capital(self, month):
        """Get total capital for a specific month, defaults to sum of all client capital if not set"""
        month_dt = pd.to_datetime(month)
        month_period = month_dt.to_period('M')
        
        # Check if we have a specific capital amount for this month
        month_capital = self.monthly_capital_df[self.monthly_capital_df['month'].dt.to_period('M') == month_period]
        
        if not month_capital.empty:
            return month_capital['total_capital'].iloc[0]
        else:
            # Default to sum of all client starting capital + contributions - withdrawals
            total_client_capital = self.clients_df['starting_capital'].sum()
            
            # Add contributions and subtract withdrawals up to this month
            if not self.capital_movements_df.empty:
                movements_up_to_month = self.capital_movements_df[
                    self.capital_movements_df['date'].dt.to_period('M') <= month_period
                ]
                contributions = movements_up_to_month[movements_up_to_month['type'] == 'contribution']['amount'].sum()
                withdrawals = movements_up_to_month[movements_up_to_month['type'] == 'withdrawal']['amount'].sum()
                total_client_capital += contributions - withdrawals
            
            return total_client_capital
    
    def get_biweekly_capital(self, period):
        """Get total capital for a specific biweekly period, defaults to sum of all client capital if not set"""
        # Parse the period string (format: "2025-06-23/2025-06-29")
        try:
            # Extract the start date from the period string
            start_date_str = period.split('/')[0]
            period_dt = pd.to_datetime(start_date_str)
            period_period = period_dt.to_period('2W')
        except:
            # If parsing fails, use the period as is
            period_period = pd.Period(period)
        
        # Check if we have a specific capital amount for this period
        period_capital = self.monthly_capital_df[self.monthly_capital_df['month'].dt.to_period('2W') == period_period]
        
        if not period_capital.empty:
            return period_capital['total_capital'].iloc[0]
        else:
            # Default to sum of all client starting capital + contributions - withdrawals
            total_client_capital = self.clients_df['starting_capital'].sum()
            
            # Add contributions and subtract withdrawals up to this period
            if not self.capital_movements_df.empty:
                movements_up_to_period = self.capital_movements_df[
                    self.capital_movements_df['date'].dt.to_period('2W') <= period_period
                ]
                contributions = movements_up_to_period[movements_up_to_period['type'] == 'contribution']['amount'].sum()
                withdrawals = movements_up_to_period[movements_up_to_period['type'] == 'withdrawal']['amount'].sum()
                total_client_capital += contributions - withdrawals
            
            return total_client_capital
    
    def get_client_capital_flow(self, client_id):
        """Get client's capital flow including contributions, withdrawals, and returns"""
        # Get client info
        client_info = self.clients_df[self.clients_df['client_id'] == client_id]
        if client_info.empty:
            return None
        
        starting_capital = client_info['starting_capital'].iloc[0]
        
        # Get investment start date, handling both Series and scalar values
        if 'investment_start_date' in client_info.columns:
            investment_start_date = client_info['investment_start_date'].iloc[0]
            # Convert to string if it's a pandas Timestamp or other pandas type
            if hasattr(investment_start_date, 'strftime'):
                investment_start_date = investment_start_date.strftime('%Y-%m-%d')
            elif pd.isna(investment_start_date):
                investment_start_date = None
        else:
            investment_start_date = None
        
        # Get capital movements
        movements = self.capital_movements_df[self.capital_movements_df['client_id'] == client_id].copy()
        
        # Calculate capital flow
        total_contributions = movements[movements['type'] == 'contribution']['amount'].sum()
        total_withdrawals = movements[movements['type'] == 'withdrawal']['amount'].sum()
        
        # Base capital = starting + contributions - withdrawals
        base_capital = starting_capital + total_contributions - total_withdrawals
        
        # Get biweekly strategy returns for chart (filtered by client investment start date)
        biweekly_returns = self.get_biweekly_strategy_returns(client_id)
        
        # Biweekly returns are now already filtered by investment start date in the method
        
        if biweekly_returns.empty:
            return {
                'starting_capital': starting_capital,
                'current_capital': base_capital,
                'total_contributions': total_contributions,
                'total_withdrawals': total_withdrawals,
                'total_returns': 0,
                'monthly_breakdown': [],
                'biweekly_breakdown': []
            }
        
        # Calculate biweekly capital progression for chart
        # Create a cleaner chart that shows capital growth over time
        biweekly_breakdown = []
        
        # Start with the total available capital
        total_available_capital = starting_capital + total_contributions - total_withdrawals
        current_capital = total_available_capital
        
        # Process capital movements by biweekly period
        movements['date'] = pd.to_datetime(movements['date'])
        movements['period'] = movements['date'].dt.to_period('2W')
        
        for _, period_data in biweekly_returns.iterrows():
            period_str = period_data['Period']
            period_period = pd.Period(period_str)
            
            # Get contributions/withdrawals for this period
            period_movements = movements[movements['period'] == period_period]
            period_contributions = period_movements[period_movements['type'] == 'contribution']['amount'].sum()
            period_withdrawals = period_movements[period_movements['type'] == 'withdrawal']['amount'].sum()
            net_contributions = period_contributions - period_withdrawals
            
            # Starting capital for this period
            period_starting_capital = current_capital
            
            # Add contributions/withdrawals
            current_capital += net_contributions
            
            # Apply trading returns to the capital after contributions
            period_return_pct = period_data['Return_Pct']
            period_return_amount = current_capital * (period_return_pct / 100)
            
            # Apply profit split calculations using client-specific config
            client_config = self.get_config(client_id)
            profit_after_tax = period_return_amount * (1 - client_config['tax_rate'])
            investor_share = profit_after_tax * client_config['investor_share']
            trader_share = profit_after_tax * client_config['trader_share']
            
            current_capital += investor_share
            
            # Create better period label
            try:
                start_date_str = period_str.split('/')[0]
                start_date = pd.to_datetime(start_date_str)
                period_label = start_date.strftime('%b %d')
            except:
                period_label = period_str
            
            biweekly_breakdown.append({
                'period': period_str,
                'period_label': period_label,
                'starting_capital': round(period_starting_capital, 2),
                'contributions': round(period_contributions, 2),
                'withdrawals': round(period_withdrawals, 2),
                'net_contributions': round(net_contributions, 2),
                'capital_after_contributions': round(period_starting_capital + net_contributions, 2),
                'period_return_pct': period_return_pct,
                'profit_after_tax': round(profit_after_tax, 2),
                'investor_share': round(investor_share, 2),
                'trader_share': round(trader_share, 2),
                'ending_capital': round(current_capital, 2)
            })
        
        # Calculate total returns (sum of all trading profits)
        # Sum up all the profit_after_tax from trading returns
        total_returns = sum([period['profit_after_tax'] for period in biweekly_breakdown])
        
        # Also calculate monthly breakdown for table display (filtered by client investment start date)
        monthly_returns = self.get_monthly_strategy_returns(client_id)
        monthly_breakdown = []
        monthly_current_capital = starting_capital
        
        if not monthly_returns.empty:
            # Process capital movements by month
            movements['month'] = movements['date'].dt.to_period('M')
            
            for _, month_data in monthly_returns.iterrows():
                month_str = month_data['Month']
                month_period = pd.Period(month_str)
                
                # Get contributions/withdrawals for this month
                month_movements = movements[movements['month'] == month_period]
                month_contributions = month_movements[month_movements['type'] == 'contribution']['amount'].sum()
                month_withdrawals = month_movements[month_movements['type'] == 'withdrawal']['amount'].sum()
                net_contributions = month_contributions - month_withdrawals
                
                # Starting capital for this month
                month_starting_capital = monthly_current_capital
                
                # Add contributions/withdrawals
                monthly_current_capital += net_contributions
                
                # Apply trading returns
                month_return_pct = month_data['Return_Pct']
                month_return_amount = monthly_current_capital * (month_return_pct / 100)
                
                # Apply profit split calculations using client-specific config
                client_config = self.get_config(client_id)
                profit_after_tax = month_return_amount * (1 - client_config['tax_rate'])
                investor_share = profit_after_tax * client_config['investor_share']
                trader_share = profit_after_tax * client_config['trader_share']
                
                monthly_current_capital += investor_share
                
                monthly_breakdown.append({
                    'month': month_str,
                    'starting_capital': round(month_starting_capital, 2),
                    'contributions': round(month_contributions, 2),
                    'withdrawals': round(month_withdrawals, 2),
                    'net_contributions': round(net_contributions, 2),
                    'capital_after_contributions': round(month_starting_capital + net_contributions, 2),
                    'monthly_return_pct': month_return_pct,
                    'profit_after_tax': round(profit_after_tax, 2),
                    'investor_share': round(investor_share, 2),
                    'trader_share': round(trader_share, 2),
                    'ending_capital': round(monthly_current_capital, 2)
                })
        
        # Get the ending capital from the last period (current capital)
        # Use monthly breakdown if available, otherwise use biweekly
        ending_capital = current_capital
        if monthly_breakdown:
            ending_capital = monthly_breakdown[-1]['ending_capital']
            # Also recalculate total returns from monthly breakdown for consistency
            total_returns = sum([period['profit_after_tax'] for period in monthly_breakdown])
        elif biweekly_breakdown:
            ending_capital = biweekly_breakdown[-1]['ending_capital']
        
        return {
            'starting_capital': starting_capital,
            'current_capital': ending_capital,
            'total_contributions': total_contributions,
            'total_withdrawals': total_withdrawals,
            'total_returns': total_returns,
            'monthly_breakdown': monthly_breakdown,
            'biweekly_breakdown': biweekly_breakdown
        }
    
    def update_config(self, tax_rate=None, trader_share=None, client_id=None):
        """Update configuration settings for a specific client or global settings"""
        if client_id is None:
            # Update global configuration
            if tax_rate is not None:
                self.config['global']['tax_rate'] = tax_rate
            if trader_share is not None:
                self.config['global']['trader_share'] = trader_share
                self.config['global']['investor_share'] = 1 - trader_share
        else:
            # Update client-specific configuration
            if client_id not in self.config['clients']:
                self.config['clients'][client_id] = {
                    "tax_rate": 0.25,  # Default 25%
                    "trader_share": 0.40,  # Default 40%
                    "investor_share": 0.60  # Default 60%
                }
            
            if tax_rate is not None:
                self.config['clients'][client_id]['tax_rate'] = tax_rate
            if trader_share is not None:
                self.config['clients'][client_id]['trader_share'] = trader_share
                self.config['clients'][client_id]['investor_share'] = 1 - trader_share
        
        self._save_config()
        return True
    
    def get_config(self, client_id=None):
        """Get configuration for a specific client or global configuration"""
        if client_id is None:
            # Return global configuration with defaults
            return {
                "tax_rate": self.config.get('global', {}).get('tax_rate', 0.25),
                "trader_share": self.config.get('global', {}).get('trader_share', 0.40),
                "investor_share": self.config.get('global', {}).get('investor_share', 0.60),
                "auto_remove_day_trades": self.config.get('global', {}).get('auto_remove_day_trades', True),
                "enable_sp500_comparison": self.config.get('global', {}).get('enable_sp500_comparison', True)
            }
        else:
            # Return client-specific configuration with fallback to global
            client_config = self.config.get('clients', {}).get(client_id, {})
            global_config = self.config.get('global', {})
            
            return {
                "tax_rate": client_config.get('tax_rate', global_config.get('tax_rate', 0.25)),
                "trader_share": client_config.get('trader_share', global_config.get('trader_share', 0.40)),
                "investor_share": client_config.get('investor_share', global_config.get('investor_share', 0.60)),
                "auto_remove_day_trades": global_config.get('auto_remove_day_trades', True)
            }
    
    def get_all_client_configs(self):
        """Get all client configurations"""
        return self.config.get('clients', {}).copy()
    
    def get_available_clients(self):
        """Get list of available clients for configuration"""
        if self.clients_df.empty:
            return []
        return self.clients_df['client_id'].tolist()

    def add_or_update_client(self, username, name, email, starting_capital, investment_start_date=None, active=True):
        """Add or update a client record in clients.csv

        This keeps the clients table in sync with users created via the admin UI.
        Uses the username as the stable client_id.
        """
        client_id = username
        if investment_start_date is None:
            investment_start_date = pd.Timestamp.now().date()
        
        new_row = {
            'client_id': client_id,
            'username': username,
            'name': name,
            'email': email,
            'starting_capital': starting_capital,
            'investment_start_date': investment_start_date,
            'active': active
        }

        if not self.clients_df.empty and 'client_id' in self.clients_df.columns:
            # Remove any existing row for this client_id
            self.clients_df = self.clients_df[self.clients_df['client_id'] != client_id]

        # Append the new/updated client
        self.clients_df = pd.concat([self.clients_df, pd.DataFrame([new_row])], ignore_index=True)
        self._save_clients()
        return True

    def sync_clients_from_users(self):
        """Ensure all client-role users from users.json exist in clients.csv.

        Idempotent: safe to call on every startup.
        """
        users_json = self.data_dir / "users.json"
        if not users_json.exists():
            return False
        try:
            import json
            with open(users_json, 'r') as f:
                users = json.load(f)
            rows = []
            for username, info in users.items():
                if info.get('role') == 'client':
                    investment_start_date = info.get('investment_start_date')
                    if investment_start_date:
                        try:
                            investment_start_date = pd.to_datetime(investment_start_date).date()
                        except:
                            investment_start_date = pd.Timestamp.now().date()
                    else:
                        investment_start_date = pd.Timestamp.now().date()
                    
                    rows.append({
                        'client_id': username,
                        'username': username,
                        'name': info.get('name', ''),
                        'email': info.get('email', ''),
                        'starting_capital': info.get('starting_capital', 0),
                        'investment_start_date': investment_start_date,
                        'active': info.get('active', True)
                    })
            if rows:
                # Remove any duplicates by client_id then append all
                df_new = pd.DataFrame(rows)
                if not self.clients_df.empty:
                    self.clients_df = self.clients_df[~self.clients_df['client_id'].isin(df_new['client_id'])]
                self.clients_df = pd.concat([self.clients_df, df_new], ignore_index=True)
                self._save_clients()
            return True
        except Exception:
            return False
    
    def delete_client(self, client_id):
        """Delete a client and all associated data"""
        try:
            # Remove from clients dataframe
            if not self.clients_df.empty and 'client_id' in self.clients_df.columns:
                self.clients_df = self.clients_df[self.clients_df['client_id'] != client_id]
                self._save_clients()
            
            # Remove from trades dataframe
            if not self.trades_df.empty and 'client_id' in self.trades_df.columns:
                self.trades_df = self.trades_df[self.trades_df['client_id'] != client_id]
                self._save_trades()
            
            # Remove from capital movements dataframe
            if not self.capital_movements_df.empty and 'client_id' in self.capital_movements_df.columns:
                self.capital_movements_df = self.capital_movements_df[self.capital_movements_df['client_id'] != client_id]
                self._save_capital_movements()
            
            # Remove from monthly capital dataframe
            if not self.monthly_capital_df.empty and 'client_id' in self.monthly_capital_df.columns:
                self.monthly_capital_df = self.monthly_capital_df[self.monthly_capital_df['client_id'] != client_id]
                self._save_monthly_capital()
            
            # Remove client-specific configuration
            if 'clients' in self.config and client_id in self.config['clients']:
                del self.config['clients'][client_id]
                self._save_config()
            
            return True
        except Exception as e:
            print(f"Error deleting client {client_id}: {str(e)}")
            return False
    
    def get_sp500_monthly_returns(self):
        """Get S&P 500 monthly returns for comparison"""
        try:
            import yfinance as yf
            
            # Get S&P 500 data for the last 5 years to ensure overlap
            sp500 = yf.Ticker("^GSPC")
            hist = sp500.history(period="5y")
            
            if hist.empty:
                return pd.DataFrame()
            
            # Calculate monthly returns
            monthly_data = hist.resample('ME').last()
            monthly_returns = monthly_data['Close'].pct_change() * 100
            
            # Create DataFrame with month and return
            sp500_returns = pd.DataFrame({
                'Month': monthly_returns.index.strftime('%Y-%m'),
                'SP500_Return_Pct': monthly_returns.values
            }).dropna()
            
            # Calculate cumulative return
            sp500_returns['SP500_Cumulative_Return'] = (1 + sp500_returns['SP500_Return_Pct'] / 100).cumprod() - 1
            sp500_returns['SP500_Cumulative_Return'] = sp500_returns['SP500_Cumulative_Return'] * 100
            
            return sp500_returns
            
        except ImportError:
            # If yfinance is not available, return empty DataFrame
            return pd.DataFrame()
        except Exception as e:
            print(f"Error fetching S&P 500 data: {str(e)}")
            return pd.DataFrame()
    
    def refresh_data(self):
        """Reload all data from files to ensure latest data is available"""
        try:
            self._load_config()
            self._load_trades()
            self._load_clients()
            self._load_capital_movements()
            self._load_monthly_capital()
            return True
        except Exception as e:
            print(f"Error refreshing data: {str(e)}")
            return False
    
    def reload_clients(self):
        """Reload clients data from file"""
        try:
            self._load_clients()
            return True
        except Exception as e:
            print(f"Error reloading clients: {str(e)}")
            return False
    
    def set_monthly_capital(self, month_year, capital_amount):
        """Set the total capital for a specific month"""
        try:
            # Convert month_year string to datetime
            month_dt = pd.to_datetime(month_year + '-01')
            
            # Check if this month already exists
            existing_month = self.monthly_capital_df[
                self.monthly_capital_df['month'].dt.to_period('M') == month_dt.to_period('M')
            ]
            
            if not existing_month.empty:
                # Update existing month
                self.monthly_capital_df.loc[
                    self.monthly_capital_df['month'].dt.to_period('M') == month_dt.to_period('M'),
                    'total_capital'
                ] = capital_amount
            else:
                # Add new month
                new_row = pd.DataFrame({
                    'month': [month_dt],
                    'total_capital': [capital_amount]
                })
                self.monthly_capital_df = pd.concat([self.monthly_capital_df, new_row], ignore_index=True)
            
            # Save to file
            self._save_monthly_capital()
            return True
            
        except Exception as e:
            print(f"Error setting monthly capital: {str(e)}")
            return False
    
    def delete_monthly_capital(self, month_year):
        """Delete the monthly capital entry for a specific month"""
        try:
            # Convert month_year string to datetime
            month_dt = pd.to_datetime(month_year + '-01')
            
            # Remove the month from the dataframe
            self.monthly_capital_df = self.monthly_capital_df[
                self.monthly_capital_df['month'].dt.to_period('M') != month_dt.to_period('M')
            ]
            
            # Save to file
            self._save_monthly_capital()
            return True
            
        except Exception as e:
            print(f"Error deleting monthly capital: {str(e)}")
            return False
    
    def remove_trades_by_return_percentage(self, stock_symbol, target_return_pct, tolerance=0.1):
        """Remove trades for a specific stock with a target return percentage"""
        try:
            if self.trades_df.empty:
                return False, "No trades found"
            
            # Calculate return percentage for all trades
            self.trades_df['return_pct'] = ((self.trades_df['sell_price'] - self.trades_df['buy_price']) / self.trades_df['buy_price'] * 100)
            
            # Find trades matching the criteria
            stock_trades = self.trades_df[self.trades_df['stock'] == stock_symbol]
            matching_trades = stock_trades[
                (stock_trades['return_pct'] >= target_return_pct - tolerance) & 
                (stock_trades['return_pct'] <= target_return_pct + tolerance)
            ]
            
            if matching_trades.empty:
                return False, f"No {stock_symbol} trades found with return percentage around {target_return_pct}%"
            
            # Remove the matching trades
            original_count = len(self.trades_df)
            self.trades_df = self.trades_df[~self.trades_df.index.isin(matching_trades.index)]
            removed_count = original_count - len(self.trades_df)
            
            # Save the updated data
            self._save_trades()
            
            return True, f"Removed {removed_count} {stock_symbol} trades with return percentage around {target_return_pct}%"
            
        except Exception as e:
            return False, f"Error removing trades: {str(e)}"
    
    def update_client(self, client_id, name, email, starting_capital, investment_start_date, active, new_password=None):
        """Update client information"""
        try:
            # Update clients dataframe
            client_mask = self.clients_df['client_id'] == client_id
            if client_mask.any():
                self.clients_df.loc[client_mask, 'name'] = name
                self.clients_df.loc[client_mask, 'email'] = email
                self.clients_df.loc[client_mask, 'starting_capital'] = starting_capital
                self.clients_df.loc[client_mask, 'investment_start_date'] = investment_start_date
                self.clients_df.loc[client_mask, 'active'] = active
                
                # Save clients data
                self._save_clients()
                
                # Update auth manager if password is provided
                if new_password:
                    auth_success = st.session_state.auth_manager.change_password(client_id, new_password)
                    if not auth_success:
                        return False
                
                return True
            else:
                return False
                
        except Exception as e:
            print(f"Error updating client: {str(e)}")
            return False

