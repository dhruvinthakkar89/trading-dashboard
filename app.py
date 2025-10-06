import streamlit as st
import yaml
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import time

# Import authentication and data management
from auth import init_auth, login_page, logout_button, require_auth
from models import TradingDataManager

# Page configuration
st.set_page_config(
    page_title="Multi-Client Trading Performance Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize authentication and data manager
init_auth()

def main():
    # Check if user is authenticated
    if not st.session_state.session_id:
        login_page()
        return
    
    # User is authenticated, show dashboard
    user_info = st.session_state.user_info
    is_admin = user_info['role'] == 'admin'
    
    # Sidebar navigation
    st.sidebar.title("📈 Trading Performance Dashboard")
    st.sidebar.markdown(f"**Welcome, {user_info['name']}**")
    st.sidebar.markdown(f"*Role: {user_info['role'].title()}*")
    st.sidebar.markdown("---")
    
    # Navigation menu based on user role
    if is_admin:
        # Admin navigation
        pages = {
            "🏠 Dashboard Overview": "admin_dashboard",
            "📊 Upload Trade Log": "admin_upload_trades",
            "👥 Manage Clients": "admin_manage_clients",
            "💰 Capital Movements": "admin_capital_movements",
            "🏦 Capital Accounts": "admin_capital_accounts",
            "⚙️ Configuration": "admin_configuration",
            "📈 Strategy Analysis": "admin_strategy_analysis",
            "📋 Strategy Details": "admin_strategy_details"
        }
    else:
        # Client navigation
        pages = {
            "🏠 Capital Account": "client_capital_account",
            "📊 Strategy Summary": "client_strategy_summary",
            "📋 Strategy Details": "client_strategy_details"
        }
    
    selected_page = st.sidebar.selectbox(
        "Select Page",
        list(pages.keys())
    )
    
    # Load the selected page
    page_function = pages[selected_page]
    
    # Initialize data manager
    if 'data_manager' not in st.session_state:
        st.session_state.data_manager = TradingDataManager()
        st.session_state.last_data_refresh = 0
    
    # Always refresh data to ensure we have the latest from files
    # This ensures all sessions see the same data
    current_time = time.time()
    
    # Refresh data every 30 seconds or on first load
    if current_time - st.session_state.last_data_refresh > 30:
        try:
            st.session_state.data_manager.refresh_data()
            st.session_state.last_data_refresh = current_time
        except Exception as e:
            # If refresh fails, recreate the data manager
            st.session_state.data_manager = TradingDataManager()
            st.session_state.last_data_refresh = current_time
    
    # Display selected page
    if page_function == "admin_dashboard":
        admin_dashboard_page()
    elif page_function == "admin_upload_trades":
        admin_upload_trades_page()
    elif page_function == "admin_manage_clients":
        admin_manage_clients_page()
    elif page_function == "admin_capital_movements":
        admin_capital_movements_page()
    elif page_function == "admin_capital_accounts":
        admin_capital_accounts_page()
    elif page_function == "admin_configuration":
        admin_configuration_page()
    elif page_function == "admin_strategy_analysis":
        admin_strategy_analysis_page()
    elif page_function == "admin_strategy_details":
        admin_strategy_details_page()
    elif page_function == "client_capital_account":
        client_capital_account_page()
    elif page_function == "client_strategy_summary":
        client_strategy_summary_page()
    elif page_function == "client_strategy_details":
        client_strategy_details_page()
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Version:** 2.0.0")
    st.sidebar.markdown("**Last Updated:** 2025")
    
    # Logout button
    logout_button()

# Admin Pages
def admin_dashboard_page():
    """Admin dashboard overview"""
    require_auth("admin")
    
    st.title("🏠 Admin Dashboard Overview")
    st.markdown("Welcome to the admin dashboard. Manage trades, clients, and system configuration.")
    
    # Add refresh button and trade removal tools
    col1, col2, col3 = st.columns([2, 1, 1])
    with col2:
        if st.button("🔄 Refresh Data", help="Reload all data from files"):
            try:
                st.session_state.data_manager.refresh_data()
                st.session_state.last_data_refresh = time.time()
                st.success("Data refreshed successfully!")
                st.rerun()
            except Exception as e:
                # If refresh fails, recreate the data manager
                from models import TradingDataManager
                st.session_state.data_manager = TradingDataManager()
                st.session_state.last_data_refresh = time.time()
                st.success("Data refreshed successfully!")
                st.rerun()
    
    with col3:
        if st.button("🗑️ Remove Problem Trades", help="Remove MSTR and COIN trades with high return percentages"):
            # Remove MSTR trades with ~4737% return
            success1, message1 = st.session_state.data_manager.remove_trades_by_return_percentage("MSTR", 4737, tolerance=100)
            # Remove COIN trades with ~2721% return  
            success2, message2 = st.session_state.data_manager.remove_trades_by_return_percentage("COIN", 2721, tolerance=100)
            
            if success1 or success2:
                st.success("Problem trades removed successfully!")
                if success1:
                    st.info(message1)
                if success2:
                    st.info(message2)
                st.rerun()
            else:
                st.warning("No matching trades found to remove")
    
    # Get data summary
    data_manager = st.session_state.data_manager
    
    # Add trade removal diagnostic section
    if not data_manager.trades_df.empty:
        st.subheader("🔍 Trade Analysis & Removal Tools")
        
        # Calculate return percentages for analysis
        trades_df = data_manager.trades_df.copy()
        trades_df['return_pct'] = ((trades_df['sell_price'] - trades_df['buy_price']) / trades_df['buy_price'] * 100)
        
        # Show high return percentage trades
        high_returns = trades_df[trades_df['return_pct'] > 1000]
        if not high_returns.empty:
            st.write("**🚨 High Return Percentage Trades (>1000%):**")
            st.dataframe(high_returns[['stock', 'buy_price', 'sell_price', 'profit_loss', 'return_pct', 'sell_date']], use_container_width=True)
            
            # Manual removal options
            st.write("**Manual Trade Removal:**")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Remove All High Return Trades (>1000%)"):
                    original_count = len(data_manager.trades_df)
                    data_manager.trades_df = data_manager.trades_df[~data_manager.trades_df.index.isin(high_returns.index)]
                    removed_count = original_count - len(data_manager.trades_df)
                    data_manager._save_trades()
                    st.success(f"Removed {removed_count} high return trades!")
                    st.rerun()
            
            with col2:
                if st.button("Remove MSTR & COIN High Returns"):
                    # Remove MSTR trades with very high returns
                    mstr_high = trades_df[(trades_df['stock'] == 'MSTR') & (trades_df['return_pct'] > 1000)]
                    coin_high = trades_df[(trades_df['stock'] == 'COIN') & (trades_df['return_pct'] > 1000)]
                    
                    original_count = len(data_manager.trades_df)
                    data_manager.trades_df = data_manager.trades_df[~data_manager.trades_df.index.isin(mstr_high.index)]
                    data_manager.trades_df = data_manager.trades_df[~data_manager.trades_df.index.isin(coin_high.index)]
                    removed_count = original_count - len(data_manager.trades_df)
                    data_manager._save_trades()
                    st.success(f"Removed {removed_count} MSTR & COIN high return trades!")
                    st.rerun()
    
    # Add September calculation diagnostic
    if not data_manager.trades_df.empty:
        st.subheader("🔍 September Return Calculation Diagnostic")
        
        # Show all available data first
        st.write("**📊 Data Analysis:**")
        
        # Show date range of all trades
        if not data_manager.trades_df.empty:
            min_date = data_manager.trades_df['sell_date'].min()
            max_date = data_manager.trades_df['sell_date'].max()
            st.write(f"• Trade date range: {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}")
            
            # Show unique months in data
            unique_months = data_manager.trades_df['sell_date'].dt.to_period('M').unique()
            st.write(f"• Available months: {', '.join([str(m) for m in sorted(unique_months)])}")
            
            # Show total trades count
            st.write(f"• Total trades in system: {len(data_manager.trades_df)}")
        
        # Try different September date formats
        st.write("**🔍 September Trade Search:**")
        
        # Method 1: Exact period match for 2025-09
        september_trades_1 = data_manager.trades_df[
            data_manager.trades_df['sell_date'].dt.to_period('M') == '2025-09'
        ]
        st.write(f"• Method 1 (Period '2025-09'): {len(september_trades_1)} trades found")
        
        # Method 2: Date range for September 2025
        september_trades_2 = data_manager.trades_df[
            (data_manager.trades_df['sell_date'] >= '2025-09-01') & 
            (data_manager.trades_df['sell_date'] < '2025-10-01')
        ]
        st.write(f"• Method 2 (Date range Sep 1-30, 2025): {len(september_trades_2)} trades found")
        
        # Method 3: Any September (any year)
        september_trades_3 = data_manager.trades_df[
            data_manager.trades_df['sell_date'].dt.month == 9
        ]
        st.write(f"• Method 3 (Any September): {len(september_trades_3)} trades found")
        
        # Show sample of recent trades
        if not data_manager.trades_df.empty:
            st.write("**📋 Recent Trades Sample (last 5):**")
            recent_trades = data_manager.trades_df.tail(5)[['sell_date', 'stock', 'profit_loss']]
            st.dataframe(recent_trades, use_container_width=True)
        
        # Use the most successful method
        september_trades = september_trades_2 if not september_trades_2.empty else september_trades_1 if not september_trades_1.empty else september_trades_3
        
        if not september_trades.empty:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                total_pl = september_trades['profit_loss'].sum()
                st.metric("September Total P&L", f"${total_pl:,.2f}")
            
            with col2:
                client_capital = data_manager.get_monthly_capital('2025-09')
                st.metric("Client Capital Used", f"${client_capital:,.2f}")
            
            with col3:
                calculated_return = (total_pl / client_capital * 100) if client_capital > 0 else 0
                st.metric("Calculated Return %", f"{calculated_return:.2f}%")
            
            # Show the calculation breakdown
            st.write("**Calculation Breakdown:**")
            st.write(f"• Total September P&L: ${total_pl:,.2f}")
            st.write(f"• Client Capital Base: ${client_capital:,.2f}")
            st.write(f"• Return Formula: (${total_pl:,.2f} ÷ ${client_capital:,.2f}) × 100 = {calculated_return:.2f}%")
            
            # Show September trades details
            st.write("**📋 September Trades Details:**")
            st.dataframe(september_trades[['sell_date', 'stock', 'buy_price', 'sell_price', 'quantity', 'profit_loss']], use_container_width=True)
            
            # Show what you think it should be
            st.write("**What do you think the September return should be?**")
            expected_return = st.number_input("Expected September Return (%)", value=calculated_return, step=0.1)
            
            if expected_return != calculated_return:
                st.warning(f"**Discrepancy detected!**")
                st.write(f"• System calculates: {calculated_return:.2f}%")
                st.write(f"• You expect: {expected_return:.2f}%")
                st.write(f"• Difference: {abs(expected_return - calculated_return):.2f} percentage points")
                
                # Calculate what the capital base should be for your expected return
                if expected_return != 0:
                    expected_capital = (total_pl / expected_return * 100)
                    st.write(f"• For {expected_return:.2f}% return, capital base should be: ${expected_capital:,.2f}")
                    st.write(f"• Current capital base is: ${client_capital:,.2f}")
                    st.write(f"• Capital difference: ${abs(expected_capital - client_capital):,.2f}")
        else:
            st.warning("**No September trades found with any method.**")
            st.write("This could mean:")
            st.write("• September trades haven't been uploaded yet")
            st.write("• September trades are in a different year (not 2024)")
            st.write("• Date format issues in the uploaded file")
            st.write("• Trades are marked with different sell dates")
            
            # Show all unique years and months
            if not data_manager.trades_df.empty:
                st.write("**Available data by year and month:**")
                year_month = data_manager.trades_df['sell_date'].dt.to_period('M').value_counts().sort_index()
                st.dataframe(year_month, use_container_width=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_trades = len(data_manager.trades_df)
        st.metric("Total Trades", total_trades)
    
    with col2:
        total_clients = len(data_manager.clients_df)
        st.metric("Total Clients", total_clients)
    
    with col3:
        total_capital = data_manager.clients_df['starting_capital'].sum() if not data_manager.clients_df.empty else 0
        st.metric("Total Capital", f"${total_capital:,.2f}")
    
    with col4:
        config = data_manager.get_config()
        st.metric("Tax Rate", f"{config['tax_rate']*100:.1f}%")
    
    # Recent activity
    st.subheader("📊 Recent Activity")
    
    if not data_manager.trades_df.empty:
        recent_trades = data_manager.trades_df.tail(5)
        st.write("**Recent Trades:**")
        st.dataframe(recent_trades[['trade_id', 'stock', 'buy_date', 'sell_date', 'profit_loss', 'win_loss']], use_container_width=True)
    
    if not data_manager.capital_movements_df.empty:
        recent_movements = data_manager.capital_movements_df.tail(5)
        st.write("**Recent Capital Movements:**")
        st.dataframe(recent_movements, use_container_width=True)

def admin_upload_trades_page():
    """Admin page for uploading trade logs"""
    require_auth("admin")
    
    st.title("📊 Upload Trade Log")
    st.markdown("Upload your trade log to calculate strategy performance and client returns.")
    
    # Refresh button
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("🔄 Refresh Data", help="Reload all data from files"):
            try:
                st.session_state.data_manager.refresh_data()
                st.session_state.last_data_refresh = time.time()
                st.success("Data refreshed successfully!")
                st.rerun()
            except Exception as e:
                # If refresh fails, recreate the data manager
                from models import TradingDataManager
                st.session_state.data_manager = TradingDataManager()
                st.session_state.last_data_refresh = time.time()
                st.success("Data refreshed successfully!")
                st.rerun()
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose a trade log file",
        type=['csv', 'xlsx', 'xls'],
        help="File must contain: buy_date, sell_date, stock, buy_price, sell_price, quantity"
    )
    
    if uploaded_file is not None:
        if st.button("Process Trade Log"):
            with st.spinner("Processing trades..."):
                success, message = st.session_state.data_manager.upload_trades(uploaded_file)
                if success:
                    # Refresh data manager to ensure all data is up to date
                    if hasattr(st.session_state.data_manager, 'refresh_data'):
                        st.session_state.data_manager.refresh_data()
                    else:
                        # Fallback: recreate data manager to get latest methods
                        st.session_state.data_manager = TradingDataManager()
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
    
    # Show current trades
    if not st.session_state.data_manager.trades_df.empty:
        st.subheader("📈 Current Trades")
        st.dataframe(st.session_state.data_manager.trades_df, use_container_width=True)
        
        # Download current trades
        csv = st.session_state.data_manager.trades_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Current Trades",
            data=csv,
            file_name="current_trades.csv",
            mime="text/csv"
        )

def admin_manage_clients_page():
    """Admin page for managing client accounts"""
    require_auth("admin")
    
    st.title("👥 Manage Clients")
    st.markdown("Create, edit, and manage client accounts.")
    
    # Refresh button
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("🔄 Refresh Data", help="Reload all data from files"):
            try:
                st.session_state.data_manager.refresh_data()
                st.session_state.last_data_refresh = time.time()
                st.success("Data refreshed successfully!")
                st.rerun()
            except Exception as e:
                # If refresh fails, recreate the data manager
                from models import TradingDataManager
                st.session_state.data_manager = TradingDataManager()
                st.session_state.last_data_refresh = time.time()
                st.success("Data refreshed successfully!")
                st.rerun()
    
    # Create new client
    st.subheader("➕ Create New Client")
    
    with st.form("create_client"):
        col1, col2 = st.columns(2)
        
        with col1:
            username = st.text_input("Username")
            name = st.text_input("Full Name")
            email = st.text_input("Email")
        
        with col2:
            password = st.text_input("Password", type="password")
            starting_capital = st.number_input("Starting Capital ($)", min_value=0.0, value=10000.0)
        
        if st.form_submit_button("Create Client"):
            if username and password and name and starting_capital > 0:
                success = st.session_state.auth_manager.create_client(
                    username, password, name, email, starting_capital
                )
                if success:
                    # Refresh data manager to sync with auth manager
                    st.session_state.data_manager.refresh_data()
                    st.success(f"Client {username} created successfully!")
                    st.rerun()
                else:
                    st.error("Username already exists")
            else:
                st.error("Please fill all required fields")
    
    # Manage existing clients
    st.subheader("📋 Existing Clients")
    
    if not st.session_state.data_manager.clients_df.empty:
        # Display clients with delete functionality (exclude admin user)
        clients_df = st.session_state.data_manager.clients_df.copy()
        
        # Filter out admin user from the list
        clients_df = clients_df[clients_df['client_id'] != 'admin']
        
        # Add delete buttons for each client
        st.markdown("**Client List:**")
        for idx, row in clients_df.iterrows():
            col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 2, 1, 1, 1])
            
            with col1:
                st.write(f"**{row['name']}**")
                st.write(f"Username: {row['client_id']}")
            
            with col2:
                st.write(f"Email: {row['email']}")
                st.write(f"Starting Capital: ${row['starting_capital']:,.2f}")
            
            with col3:
                st.write(f"Investment Start: {row['investment_start_date']}")
                st.write(f"Active: {'Yes' if row['active'] else 'No'}")
            
            with col4:
                if st.button("Edit", key=f"edit_{row['client_id']}"):
                    st.session_state[f"editing_{row['client_id']}"] = True
            
            with col5:
                if st.button("🔑 Password", key=f"password_{row['client_id']}", type="secondary"):
                    st.session_state[f"changing_password_{row['client_id']}"] = True
            
            with col6:
                if st.button("🗑️ Delete", key=f"delete_{row['client_id']}", type="secondary"):
                    st.session_state[f"confirm_delete_{row['client_id']}"] = True
            
            # Confirmation dialog for deletion
            if st.session_state.get(f"confirm_delete_{row['client_id']}", False):
                st.warning(f"⚠️ Are you sure you want to delete client '{row['name']}' ({row['client_id']})?")
                st.warning("This will permanently delete ALL data associated with this client including trades, capital movements, and configurations.")
                
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("Yes, Delete Permanently", key=f"confirm_yes_{row['client_id']}", type="primary"):
                        # Delete from both auth manager and data manager
                        auth_success = st.session_state.auth_manager.delete_user(row['client_id'])
                        data_success = st.session_state.data_manager.delete_client(row['client_id'])
                        
                        if auth_success and data_success:
                            st.success(f"Client '{row['name']}' deleted successfully!")
                            # Clear the confirmation state
                            if f"confirm_delete_{row['client_id']}" in st.session_state:
                                del st.session_state[f"confirm_delete_{row['client_id']}"]
                            st.rerun()
                        else:
                            st.error("Failed to delete client. Please try again.")
                
                with col_no:
                    if st.button("Cancel", key=f"confirm_no_{row['client_id']}"):
                        # Clear the confirmation state
                        if f"confirm_delete_{row['client_id']}" in st.session_state:
                            del st.session_state[f"confirm_delete_{row['client_id']}"]
                        st.rerun()
            
            # Edit form for client
            if st.session_state.get(f"editing_{row['client_id']}", False):
                st.markdown("---")
                st.subheader(f"✏️ Edit Client: {row['name']}")
                
                with st.form(f"edit_client_{row['client_id']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        new_name = st.text_input("Full Name", value=row['name'], key=f"edit_name_{row['client_id']}")
                        new_email = st.text_input("Email", value=row['email'], key=f"edit_email_{row['client_id']}")
                        new_starting_capital = st.number_input(
                            "Starting Capital ($)", 
                            min_value=0.0, 
                            value=float(row['starting_capital']),
                            key=f"edit_capital_{row['client_id']}"
                        )
                    
                    with col2:
                        new_investment_start = st.date_input(
                            "Investment Start Date",
                            value=pd.to_datetime(row['investment_start_date']).date(),
                            key=f"edit_start_{row['client_id']}"
                        )
                        new_active = st.selectbox(
                            "Status",
                            options=["Active", "Inactive"],
                            index=0 if row['active'] else 1,
                            key=f"edit_active_{row['client_id']}"
                        )
                        new_password = st.text_input(
                            "New Password (leave blank to keep current)", 
                            type="password",
                            key=f"edit_password_{row['client_id']}"
                        )
                    
                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        if st.form_submit_button("💾 Save Changes", type="primary"):
                            # Update client data
                            success = st.session_state.data_manager.update_client(
                                row['client_id'],
                                new_name,
                                new_email,
                                new_starting_capital,
                                new_investment_start,
                                new_active == "Active",
                                new_password if new_password else None
                            )
                            
                            if success:
                                st.success(f"Client '{new_name}' updated successfully!")
                                # Clear editing state
                                if f"editing_{row['client_id']}" in st.session_state:
                                    del st.session_state[f"editing_{row['client_id']}"]
                                st.rerun()
                            else:
                                st.error("Failed to update client. Please try again.")
                    
                    with col_cancel:
                        if st.form_submit_button("❌ Cancel"):
                            # Clear editing state
                            if f"editing_{row['client_id']}" in st.session_state:
                                del st.session_state[f"editing_{row['client_id']}"]
                            st.rerun()
            
            # Password change form
            if st.session_state.get(f"changing_password_{row['client_id']}", False):
                st.markdown("---")
                st.subheader(f"🔑 Change Password: {row['name']}")
                
                with st.form(f"change_password_{row['client_id']}"):
                    new_password = st.text_input(
                        "New Password", 
                        type="password",
                        key=f"new_password_{row['client_id']}",
                        help="Enter a new password for this client"
                    )
                    confirm_password = st.text_input(
                        "Confirm New Password", 
                        type="password",
                        key=f"confirm_password_{row['client_id']}",
                        help="Re-enter the new password to confirm"
                    )
                    
                    col_save, col_cancel = st.columns(2)
                    with col_save:
                        if st.form_submit_button("🔑 Change Password", type="primary"):
                            if new_password and confirm_password:
                                if new_password == confirm_password:
                                    # Update password using auth manager
                                    success = st.session_state.auth_manager.change_password(row['client_id'], new_password)
                                    if success:
                                        st.success(f"Password for '{row['name']}' updated successfully!")
                                        # Clear password change state
                                        if f"changing_password_{row['client_id']}" in st.session_state:
                                            del st.session_state[f"changing_password_{row['client_id']}"]
                                        st.rerun()
                                    else:
                                        st.error("Failed to update password. Please try again.")
                                else:
                                    st.error("Passwords do not match. Please try again.")
                            else:
                                st.error("Please enter and confirm the new password.")
                    
                    with col_cancel:
                        if st.form_submit_button("❌ Cancel"):
                            # Clear password change state
                            if f"changing_password_{row['client_id']}" in st.session_state:
                                del st.session_state[f"changing_password_{row['client_id']}"]
                            st.rerun()
            
            st.divider()
        
        # Also show the dataframe for reference
        st.markdown("**Data Table View:**")
        st.dataframe(clients_df, use_container_width=True)
    else:
        st.info("No clients created yet.")

def admin_capital_movements_page():
    """Admin page for managing capital movements"""
    require_auth("admin")
    
    st.title("💰 Capital Movements")
    st.markdown("Manage client contributions and withdrawals.")
    
    # Refresh button
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("🔄 Refresh Data", help="Reload all data from files"):
            try:
                st.session_state.data_manager.refresh_data()
                st.session_state.last_data_refresh = time.time()
                st.success("Data refreshed successfully!")
                st.rerun()
            except Exception as e:
                # If refresh fails, recreate the data manager
                from models import TradingDataManager
                st.session_state.data_manager = TradingDataManager()
                st.session_state.last_data_refresh = time.time()
                st.success("Data refreshed successfully!")
                st.rerun()
    
    # Add capital movement
    st.subheader("➕ Add Capital Movement")
    
    with st.form("add_movement"):
        col1, col2 = st.columns(2)
        
        with col1:
            client_id = st.selectbox(
                "Client ID",
                options=st.session_state.data_manager.clients_df['client_id'].tolist() if not st.session_state.data_manager.clients_df.empty else []
            )
            movement_type = st.selectbox("Type", ["contribution", "withdrawal"])
            amount = st.number_input("Amount ($)", min_value=0.0, value=1000.0)
        
        with col2:
            date = st.date_input("Date")
            notes = st.text_input("Notes")
        
        if st.form_submit_button("Add Movement"):
            if client_id and amount > 0:
                success = st.session_state.data_manager.add_capital_movement(
                    client_id, movement_type, amount, date, notes
                )
                if success:
                    st.success(f"{movement_type.title()} of ${amount:,.2f} added for {client_id}")
                    st.rerun()
                else:
                    st.error("Failed to add movement")
            else:
                st.error("Please fill all required fields")
    
    # Show capital movements
    if not st.session_state.data_manager.capital_movements_df.empty:
        st.subheader("📊 Capital Movements History")
        st.dataframe(st.session_state.data_manager.capital_movements_df, use_container_width=True)

def admin_capital_accounts_page():
    """Admin page for viewing client capital accounts"""
    require_auth("admin")
    
    st.title("🏦 Capital Accounts")
    st.markdown("View capital progression, contributions, withdrawals, and returns for all clients.")
    
    # Refresh button
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("🔄 Refresh Data", help="Reload all data from files"):
            try:
                st.session_state.data_manager.refresh_data()
                st.session_state.last_data_refresh = time.time()
                st.success("Data refreshed successfully!")
                st.rerun()
            except Exception as e:
                # If refresh fails, recreate the data manager
                from models import TradingDataManager
                st.session_state.data_manager = TradingDataManager()
                st.session_state.last_data_refresh = time.time()
                st.success("Data refreshed successfully!")
                st.rerun()
    
    data_manager = st.session_state.data_manager
    
    # Client selection
    if not data_manager.clients_df.empty:
        client_options = data_manager.clients_df['client_id'].tolist()
        selected_client = st.selectbox(
            "Select Client to View",
            options=client_options,
            key="admin_client_selection"
        )
        
        if selected_client:
            # Get client capital flow
            client_capital = data_manager.get_client_capital_flow(selected_client)
            
            if client_capital:
                # Get client info for display
                client_info = data_manager.clients_df[data_manager.clients_df['client_id'] == selected_client].iloc[0]
                
                st.subheader(f"📊 Capital Account for {client_info['name']} ({selected_client})")
                
                # Capital overview
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Starting Capital", f"${client_capital['starting_capital']:,.2f}")
                    st.metric("Current Capital", f"${client_capital['current_capital']:,.2f}")
                
                with col2:
                    st.metric("Total Contributions", f"${client_capital['total_contributions']:,.2f}")
                    st.metric("Total Withdrawals", f"${client_capital['total_withdrawals']:,.2f}")
                
                with col3:
                    # Calculate investor's share of returns
                    config = data_manager.get_config(selected_client)
                    investor_returns = client_capital['total_returns'] * config['investor_share']
                    st.metric("Investor Returns", f"${investor_returns:,.2f}")
                    investor_return_pct = (investor_returns / client_capital['starting_capital'] * 100) if client_capital['starting_capital'] > 0 else 0
                    st.metric("Investor Return %", f"{investor_return_pct:.2f}%")
                
                with col4:
                    config = data_manager.get_config(selected_client)
                    st.metric("Tax Rate", f"{config['tax_rate']*100:.1f}%")
                    st.metric("Investor Share", f"{config['investor_share']*100:.1f}%")
                
                # Monthly table and biweekly chart
                if client_capital['monthly_breakdown'] or client_capital['biweekly_breakdown']:
                    # Monthly table
                    if client_capital['monthly_breakdown']:
                        st.subheader("📊 Monthly Capital Progression (Table)")
                        
                        monthly_df = pd.DataFrame(client_capital['monthly_breakdown'])
                        # Remove contribution/withdrawal columns for cleaner display
                        display_columns = ['month', 'starting_capital', 'capital_after_contributions', 'monthly_return_pct', 'profit_after_tax', 'investor_share', 'trader_share', 'ending_capital']
                        monthly_display_df = monthly_df[display_columns]
                        st.dataframe(monthly_display_df, use_container_width=True)
                    
                    # Capital Growth Visualization
                    st.subheader("📈 Capital Growth Analysis")
                    
                    if client_capital['monthly_breakdown']:
                        monthly_df = pd.DataFrame(client_capital['monthly_breakdown'])
                        
                        # Create two separate simple charts if biweekly data is available
                    if client_capital['biweekly_breakdown']:
                            st.write("**Biweekly Performance Analysis**")
                            
                            biweekly_df = pd.DataFrame(client_capital['biweekly_breakdown'])
                            
                            # Calculate cumulative profits (only from trading, not contributions)
                            # Profit for each period = ending_capital - capital_after_contributions
                            biweekly_df['period_profit'] = biweekly_df['ending_capital'] - biweekly_df['capital_after_contributions']
                            biweekly_df['cumulative_profit'] = biweekly_df['period_profit'].cumsum()
                            
                            # Calculate total capital starting from initial investment + cumulative profit + contributions
                            initial_capital = biweekly_df['starting_capital'].iloc[0]  # First period starting capital
                            # Use net_contributions (contributions - withdrawals) instead of total_contributions
                            biweekly_df['total_capital'] = initial_capital + biweekly_df['cumulative_profit'] + biweekly_df['net_contributions'].cumsum()
                            
                            # Chart 1: Cumulative Profit (biweekly)
                            fig1 = go.Figure()
                            fig1.add_trace(go.Scatter(
                                x=biweekly_df['period_label'],
                                y=biweekly_df['cumulative_profit'],
                                mode='lines+markers',
                                name='Cumulative Profit',
                                line=dict(color='green', width=3),
                                marker=dict(size=6)
                            ))
                            
                            fig1.update_layout(
                                title=f"Cumulative Profit (Biweekly) - {client_info['name']}",
                                xaxis_title="Biweekly Period",
                                yaxis_title="Cumulative Profit ($)",
                                hovermode='x unified'
                            )
                            
                            st.plotly_chart(fig1, use_container_width=True)
                    else:
                        # Fallback to monthly view if no biweekly data
                        st.write("**Monthly Capital Growth (Normalized to Starting Capital)**")
                        
                        # Calculate normalized capital (starting from 100%)
                        monthly_df['normalized_capital'] = (monthly_df['ending_capital'] / monthly_df['starting_capital'].iloc[0] * 100).round(2)
                        monthly_df['capital_growth_pct'] = monthly_df['normalized_capital'] - 100
                        
                        # Create dual-axis chart showing both absolute capital and normalized growth
                        fig = go.Figure()
                        
                        # Add normalized capital line
                        fig.add_trace(go.Scatter(
                            x=monthly_df['month'],
                            y=monthly_df['normalized_capital'],
                            mode='lines+markers',
                            name='Capital Growth (%)',
                            line=dict(color='blue', width=3),
                            marker=dict(size=8),
                            yaxis='y'
                        ))
                        
                        # Add monthly returns as bars
                        fig.add_trace(go.Bar(
                            x=monthly_df['month'],
                            y=monthly_df['monthly_return_pct'],
                            name='Monthly Returns (%)',
                            marker_color=['green' if x >= 0 else 'red' for x in monthly_df['monthly_return_pct']],
                            opacity=0.6,
                            yaxis='y2'
                        ))
                        
                        fig.update_layout(
                            title=f"Capital Growth vs Monthly Returns - {client_info['name']}",
                            xaxis_title="Month",
                            yaxis=dict(title="Capital Growth (%)", side="left"),
                            yaxis2=dict(title="Monthly Returns (%)", side="right", overlaying="y"),
                            hovermode='x unified',
                            legend=dict(x=0.02, y=0.98)
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                else:
                    st.info("No capital progression data available yet.")
            else:
                st.error("Unable to load capital account information for selected client.")
    else:
        st.info("No clients created yet. Please create clients first.")

def admin_configuration_page():
    """Admin page for system configuration"""
    require_auth("admin")
    
    st.title("⚙️ Configuration Management")
    st.markdown("Configure tax rates, profit splits, and system settings per client.")
    
    data_manager = st.session_state.data_manager
    
    # Configuration type selection
    config_type = st.radio(
        "Configuration Type",
        ["Global Settings", "Per-Client Settings"],
        horizontal=True
    )
    
    if config_type == "Global Settings":
        st.subheader("🌐 Global Configuration")
        st.markdown("These settings apply to all clients by default and can be overridden per client.")
        
        config = data_manager.get_config()
        
        with st.form("update_global_config"):
            col1, col2 = st.columns(2)
            
            with col1:
                tax_rate = st.slider(
                    "Default Tax Rate (%)",
                    min_value=0.0,
                    max_value=50.0,
                    value=config['tax_rate'] * 100,
                    step=1.0,
                    key="global_tax_rate"
                )
            
            with col2:
                trader_share = st.slider(
                    "Default Trader Share (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=config['trader_share'] * 100,
                    step=5.0,
                    key="global_trader_share"
                )
            
            if st.form_submit_button("Update Global Configuration"):
                success = data_manager.update_config(
                    tax_rate / 100, trader_share / 100
                )
                if success:
                    st.success("Global configuration updated successfully!")
                    st.rerun()
                else:
                    st.error("Failed to update global configuration")
        
        # Display current global configuration
        st.subheader("📋 Current Global Configuration")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Default Tax Rate", f"{config['tax_rate']*100:.1f}%")
        
        with col2:
            st.metric("Default Trader Share", f"{config['trader_share']*100:.1f}%")
        
        with col3:
            st.metric("Default Investor Share", f"{config['investor_share']*100:.1f}%")
        
        # Monthly Capital Management
        st.subheader("💰 Monthly Capital Management")
        st.markdown("Set total capital for specific months. If not set, system will calculate based on client capital.")
        
        with st.form("monthly_capital_config"):
            col1, col2 = st.columns(2)
            
            with col1:
                # Generate all months from 2024 to 2027
                month_options = []
                for year in range(2024, 2028):
                    for month in range(1, 13):
                        month_str = f"{year}-{month:02d}"
                        month_options.append(month_str)
                
                month_year = st.selectbox(
                    "Select Month/Year",
                    options=month_options,
                    key="month_year_selection"
                )
            
            with col2:
                # Get current capital for selected month if it exists
                current_capital = 0.0
                if not data_manager.monthly_capital_df.empty:
                    selected_month_dt = pd.to_datetime(month_year + '-01')
                    existing_month = data_manager.monthly_capital_df[
                        data_manager.monthly_capital_df['month'].dt.to_period('M') == selected_month_dt.to_period('M')
                    ]
                    if not existing_month.empty:
                        current_capital = existing_month['total_capital'].iloc[0]
                
                capital_amount = st.number_input(
                    "Total Capital for Month ($)",
                    min_value=0.0,
                    value=current_capital,
                    step=1000.0,
                    key="monthly_capital_amount"
                )
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.form_submit_button("Set Monthly Capital"):
                    if capital_amount > 0:
                        # Add or update monthly capital
                        success = data_manager.set_monthly_capital(month_year, capital_amount)
                        if success:
                            st.success(f"Monthly capital set to ${capital_amount:,.2f} for {month_year}")
                            st.rerun()
                        else:
                            st.error("Failed to set monthly capital")
                    else:
                        st.error("Please enter a valid capital amount")
            
            with col2:
                if st.form_submit_button("Delete Monthly Capital"):
                    if current_capital > 0:
                        # Delete monthly capital entry
                        success = data_manager.delete_monthly_capital(month_year)
                        if success:
                            st.success(f"Monthly capital deleted for {month_year}")
                            st.rerun()
                        else:
                            st.error("Failed to delete monthly capital")
                    else:
                        st.error("No capital set for this month")
            
            with col3:
                if st.form_submit_button("Reset to Default"):
                    if current_capital > 0:
                        # Delete monthly capital entry to use default calculation
                        success = data_manager.delete_monthly_capital(month_year)
                        if success:
                            st.success(f"Monthly capital reset to default calculation for {month_year}")
                            st.rerun()
                        else:
                            st.error("Failed to reset monthly capital")
                    else:
                        st.info("Already using default calculation")
        
        # Show current monthly capital settings
        if not data_manager.monthly_capital_df.empty:
            st.write("**📊 Current Monthly Capital Settings:**")
            monthly_capital_display = data_manager.monthly_capital_df.copy()
            monthly_capital_display['month'] = monthly_capital_display['month'].dt.strftime('%Y-%m')
            monthly_capital_display['total_capital'] = monthly_capital_display['total_capital'].apply(lambda x: f"${x:,.2f}")
            st.dataframe(monthly_capital_display[['month', 'total_capital']], use_container_width=True)
        else:
            st.info("No monthly capital settings configured. System will use default calculation based on client capital.")
    
    else:  # Per-Client Settings
        st.subheader("👥 Per-Client Configuration")
        st.markdown("Configure individual client settings. Clients inherit global settings if not specified.")
        
        # Client selection
        available_clients = data_manager.get_available_clients()
        
        if not available_clients:
            st.warning("No clients available. Please add clients first.")
        else:
            selected_client = st.selectbox(
                "Select Client",
                available_clients,
                key="client_selection"
            )
            
            if selected_client:
                # Get client info
                client_info = data_manager.get_client_info(selected_client)
                if client_info:
                    st.subheader(f"⚙️ Configuration for {client_info['name']}")
                    
                    # Get current client configuration
                    client_config = data_manager.get_client_config(selected_client)
                    
                    with st.form("update_client_config"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            tax_rate = st.slider(
                                "Tax Rate (%)",
                                min_value=0.0,
                                max_value=50.0,
                                value=client_config['tax_rate'] * 100,
                                step=1.0,
                                key="client_tax_rate"
                            )
                        
                        with col2:
                            trader_share = st.slider(
                                "Trader Share (%)",
                                min_value=0.0,
                                max_value=100.0,
                                value=client_config['trader_share'] * 100,
                                step=5.0,
                                key="client_trader_share"
                            )
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("Update Client Configuration"):
                                success = data_manager.update_config(
                                    tax_rate / 100, trader_share / 100, selected_client
                                )
                                if success:
                                    st.success(f"Configuration updated successfully for {client_info['name']}!")
                                    st.rerun()
                                else:
                                    st.error("Failed to update client configuration")
                        
                        with col2:
                            if st.form_submit_button("Reset to Global Settings"):
                                # Remove client-specific config to use global defaults
                                if selected_client in data_manager.config.get('clients', {}):
                                    del data_manager.config['clients'][selected_client]
                                    data_manager._save_config()
                                    st.success(f"Reset to global settings for {client_info['name']}!")
                                    st.rerun()
                    
                    # Display current client configuration
                    st.subheader(f"📋 Current Configuration for {client_info['name']}")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Tax Rate", f"{client_config['tax_rate']*100:.1f}%")
                    
                    with col2:
                        st.metric("Trader Share", f"{client_config['trader_share']*100:.1f}%")
                    
                    with col3:
                        st.metric("Investor Share", f"{client_config['investor_share']*100:.1f}%")
                    
                    # Show if using global or custom settings
                    client_configs = data_manager.get_all_client_configs()
                    if selected_client in client_configs:
                        st.info("🔧 Using custom configuration for this client")
                    else:
                        st.info("🌐 Using global default configuration")
    
    # Summary of all client configurations
    st.subheader("📊 Configuration Summary")
    client_configs = data_manager.get_all_client_configs()
    
    if client_configs:
        summary_data = []
        for client_id, config in client_configs.items():
            client_info = data_manager.get_client_info(client_id)
            if client_info:
                summary_data.append({
                    'Client': client_info['name'],
                    'Tax Rate': f"{config['tax_rate']*100:.1f}%",
                    'Trader Share': f"{config['trader_share']*100:.1f}%",
                    'Investor Share': f"{config['investor_share']*100:.1f}%"
                })
        
        if summary_data:
            summary_df = pd.DataFrame(summary_data)
            st.dataframe(summary_df, use_container_width=True)
        else:
            st.info("No custom client configurations found. All clients are using global defaults.")
    else:
        st.info("No custom client configurations found. All clients are using global defaults.")

def admin_strategy_analysis_page():
    """Strategy analysis page for both admin and clients"""
    require_auth(["admin", "client"])
    
    st.title("📈 Strategy Analysis")
    st.markdown("Detailed analysis of trading strategy performance.")
    
    # Refresh button
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("🔄 Refresh Data", help="Reload all data from files"):
            try:
                st.session_state.data_manager.refresh_data()
                st.session_state.last_data_refresh = time.time()
                st.success("Data refreshed successfully!")
                st.rerun()
            except Exception as e:
                # If refresh fails, recreate the data manager
                from models import TradingDataManager
                st.session_state.data_manager = TradingDataManager()
                st.session_state.last_data_refresh = time.time()
                st.success("Data refreshed successfully!")
                st.rerun()
    
    data_manager = st.session_state.data_manager
    
    if not data_manager.trades_df.empty:
        # Strategy summary
        summary = data_manager.get_strategy_summary()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Calculate return after tax using global tax rate
            config = data_manager.get_config()
            return_after_tax = summary['cumulative_return'] * (1 - config['tax_rate'])
            st.metric("Return After Tax", f"{return_after_tax:.2f}%")
            st.metric("Total Trades", summary['total_trades'])
        
        with col2:
            st.metric("Cumulative Return (Before Tax)", f"{summary['cumulative_return']:.2f}%")
            st.metric("Win Rate", f"{summary['win_rate']:.1f}%")
        
        with col3:
            st.metric("Avg Win %", f"{summary['avg_winner_pct']:.2f}%")
            st.metric("Avg Loss %", f"{summary['avg_loser_pct']:.2f}%")
        
        with col4:
            # Column 4 is now empty - metrics removed as requested
            pass
        
        # S&P 500 comparison toggle
        st.markdown("---")
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("**S&P 500 Comparison:**")
        with col2:
            enable_sp500 = st.checkbox(
                "Enable S&P 500 comparison", 
                value=config.get('enable_sp500_comparison', True),
                key="sp500_toggle"
            )
            if enable_sp500 != config.get('enable_sp500_comparison', True):
                # Update configuration
                data_manager.config['global']['enable_sp500_comparison'] = enable_sp500
                data_manager._save_config()
                st.rerun()
        
        # Monthly returns
        monthly_returns = data_manager.get_monthly_strategy_returns()
        
        if not monthly_returns.empty:
            st.subheader("📊 Monthly Strategy Returns vs S&P 500")
            
            # Get S&P 500 data for comparison (if enabled)
            config = data_manager.get_config()
            sp500_returns = pd.DataFrame()  # Default to empty
            
            if config.get('enable_sp500_comparison', True):
                try:
                    sp500_returns = data_manager.get_sp500_monthly_returns()
                    if sp500_returns.empty:
                        st.warning("S&P 500 data is empty. Check internet connection or try again later.")
                except Exception as e:
                    st.warning(f"Could not fetch S&P 500 data: {str(e)}")
                    sp500_returns = pd.DataFrame()
            
            # Status information
            if not sp500_returns.empty:
                st.success("✅ S&P 500 comparison enabled - showing benchmark data")
            else:
                st.warning("⚠️ S&P 500 comparison disabled or data unavailable. Showing strategy data only.")
            
            # Merge strategy returns with S&P 500 returns
            if not sp500_returns.empty:
                # Merge on Month column
                monthly_returns_with_sp500 = monthly_returns.merge(
                    sp500_returns[['Month', 'SP500_Return_Pct', 'SP500_Cumulative_Return']], 
                    on='Month', 
                    how='left'
                )
                
                # Fill NaN values with 0 for months where S&P 500 data is not available
                monthly_returns_with_sp500['SP500_Return_Pct'] = monthly_returns_with_sp500['SP500_Return_Pct'].fillna(0)
                monthly_returns_with_sp500['SP500_Cumulative_Return'] = monthly_returns_with_sp500['SP500_Cumulative_Return'].fillna(0)
                
                # Display columns including S&P 500 comparison (removed S&P500_Cumulative_Return)
                display_columns = ['Month', 'Total_Trades', 'Win_Rate', 'Avg_Win_Pct', 'Avg_Loss_Pct', 'Return_Pct', 'SP500_Return_Pct', 'Cumulative_Return']
                monthly_display_df = monthly_returns_with_sp500[display_columns]
                
                # Rename columns for better display
                monthly_display_df = monthly_display_df.rename(columns={
                    'Return_Pct': 'Strategy_Return_Pct',
                    'SP500_Return_Pct': 'S&P500_Return_Pct',
                    'Cumulative_Return': 'Strategy_Cumulative_Return'
                })
            else:
                # If S&P 500 data is not available, show original columns
                display_columns = ['Month', 'Total_Trades', 'Win_Rate', 'Avg_Win_Pct', 'Avg_Loss_Pct', 'Return_Pct', 'Cumulative_Return']
                monthly_display_df = monthly_returns[display_columns]
                monthly_display_df = monthly_display_df.rename(columns={
                    'Return_Pct': 'Strategy_Return_Pct',
                    'Cumulative_Return': 'Strategy_Cumulative_Return'
                })
            
            st.dataframe(monthly_display_df, use_container_width=True)
            
            # Combined Chart - Strategy vs S&P 500 Monthly Returns
            if not sp500_returns.empty:
                # Create combined chart with both strategy and S&P 500 returns
                fig = go.Figure()
                
                # Add strategy returns line
                fig.add_trace(go.Scatter(
                    x=monthly_returns['Month'],
                    y=monthly_returns['Return_Pct'],
                    mode='lines+markers',
                    name='Strategy Returns',
                    line=dict(color='blue', shape='spline'),
                    marker=dict(size=6)
                ))
                
                # Add S&P 500 returns line
                fig.add_trace(go.Scatter(
                    x=monthly_returns_with_sp500['Month'],
                    y=monthly_returns_with_sp500['SP500_Return_Pct'],
                    mode='lines+markers',
                    name='S&P 500 Returns',
                    line=dict(color='red', shape='spline'),
                    marker=dict(size=6)
                ))
                
                fig.update_layout(
                    title="Monthly Returns Comparison: Strategy vs S&P 500 (%)",
                    xaxis_title="Month",
                    yaxis_title="Return Percentage (%)",
                    hovermode='x unified',
                    legend=dict(
                        yanchor="top",
                        y=0.99,
                        xanchor="left",
                        x=0.01
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                # Fallback to strategy-only chart if S&P 500 data is not available
                fig = px.line(
                    monthly_returns,
                    x='Month',
                    y='Return_Pct',
                    title="Monthly Strategy Returns (%)",
                    markers=True,
                    line_shape='spline'
                )
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No trades uploaded yet. Please upload a trade log first.")

# Client Pages
def client_capital_account_page():
    """Client page for viewing capital account"""
    require_auth("client")
    
    st.title("🏠 Capital Account")
    st.markdown("View your capital progression, contributions, withdrawals, and returns.")
    
    # Add refresh button
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Refresh Data", help="Reload all data from files"):
            try:
                st.session_state.data_manager.refresh_data()
                st.session_state.last_data_refresh = time.time()
                st.success("Data refreshed successfully!")
                st.rerun()
            except Exception as e:
                # If refresh fails, recreate the data manager
                from models import TradingDataManager
                st.session_state.data_manager = TradingDataManager()
                st.session_state.last_data_refresh = time.time()
                st.success("Data refreshed successfully!")
                st.rerun()
    
    user_info = st.session_state.user_info
    data_manager = st.session_state.data_manager
    
    # Get client capital flow
    client_capital = data_manager.get_client_capital_flow(user_info['username'])
    
    # Debug section to show what data is being used
    if st.checkbox("🔍 Show Debug Info", help="Display technical details about the data"):
        st.write("**Debug Information:**")
        st.write(f"- Client ID: {user_info['username']}")
        st.write(f"- Investment start date: {data_manager.clients_df[data_manager.clients_df['client_id'] == user_info['username']].iloc[0]['investment_start_date']}")
        st.write(f"- Monthly breakdown length: {len(client_capital.get('monthly_breakdown', []))}")
        st.write(f"- Biweekly breakdown length: {len(client_capital.get('biweekly_breakdown', []))}")
        if client_capital.get('monthly_breakdown'):
            st.write("**Monthly breakdown months:**")
            for month in client_capital['monthly_breakdown']:
                st.write(f"  - {month['month']}")
    
    if client_capital:
        # Capital overview
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Starting Capital", f"${client_capital['starting_capital']:,.2f}")
            st.metric("Current Capital", f"${client_capital['current_capital']:,.2f}")
        
        with col2:
            st.metric("Total Contributions", f"${client_capital['total_contributions']:,.2f}")
            st.metric("Total Withdrawals", f"${client_capital['total_withdrawals']:,.2f}")
        
        with col3:
            # Calculate investor's share of returns
            config = data_manager.get_config(user_info['username'])
            investor_returns = client_capital['total_returns'] * config['investor_share']
            st.metric("Investor Returns", f"${investor_returns:,.2f}")
            investor_return_pct = (investor_returns / client_capital['starting_capital'] * 100) if client_capital['starting_capital'] > 0 else 0
            st.metric("Investor Return %", f"{investor_return_pct:.2f}%")
        
        with col4:
            config = data_manager.get_config(user_info['username'])
            st.metric("Tax Rate", f"{config['tax_rate']*100:.1f}%")
            st.metric("Investor Share", f"{config['investor_share']*100:.1f}%")
        
        # Monthly table and biweekly chart
        if client_capital['monthly_breakdown'] or client_capital['biweekly_breakdown']:
            # Monthly table
            if client_capital['monthly_breakdown']:
                st.subheader("📊 Monthly Capital Progression (Table)")
                
                monthly_df = pd.DataFrame(client_capital['monthly_breakdown'])
                # Remove contribution/withdrawal columns for cleaner display
                display_columns = ['month', 'starting_capital', 'capital_after_contributions', 'monthly_return_pct', 'profit_after_tax', 'investor_share', 'trader_share', 'ending_capital']
                monthly_display_df = monthly_df[display_columns]
                st.dataframe(monthly_display_df, use_container_width=True)
            
            # Capital Growth Visualization
            st.subheader("📈 Capital Growth Analysis")
            
            if client_capital['monthly_breakdown']:
                monthly_df = pd.DataFrame(client_capital['monthly_breakdown'])
                
                # Create two separate simple charts if biweekly data is available
                if client_capital['biweekly_breakdown']:
                    st.write("**Biweekly Performance Analysis**")
                    
                    biweekly_df = pd.DataFrame(client_capital['biweekly_breakdown'])
                    
                    # Calculate cumulative profits (only from trading, not contributions)
                    # Profit for each period = ending_capital - capital_after_contributions
                    biweekly_df['period_profit'] = biweekly_df['ending_capital'] - biweekly_df['capital_after_contributions']
                    biweekly_df['cumulative_profit'] = biweekly_df['period_profit'].cumsum()
                    
                    # Calculate total capital starting from initial investment + cumulative profit + contributions
                    initial_capital = biweekly_df['starting_capital'].iloc[0]  # First period starting capital
                    # Use net_contributions (contributions - withdrawals) instead of total_contributions
                    biweekly_df['total_capital'] = initial_capital + biweekly_df['cumulative_profit'] + biweekly_df['net_contributions'].cumsum()
                    
                    # Chart 1: Cumulative Profit (biweekly)
                    fig1 = go.Figure()
                    fig1.add_trace(go.Scatter(
                        x=biweekly_df['period_label'],
                        y=biweekly_df['cumulative_profit'],
                        mode='lines+markers',
                        name='Cumulative Profit',
                        line=dict(color='green', width=3),
                        marker=dict(size=6)
                    ))
                    
                    fig1.update_layout(
                        title="Cumulative Profit (Biweekly)",
                        xaxis_title="Biweekly Period",
                        yaxis_title="Cumulative Profit ($)",
                        hovermode='x unified'
                    )
                    
                    st.plotly_chart(fig1, use_container_width=True)
                else:
                    # Fallback to monthly view if no biweekly data
                    st.write("**Monthly Capital Growth (Normalized to Starting Capital)**")
                    
                    # Calculate normalized capital (starting from 100%)
                    monthly_df['normalized_capital'] = (monthly_df['ending_capital'] / monthly_df['starting_capital'].iloc[0] * 100).round(2)
                    monthly_df['capital_growth_pct'] = monthly_df['normalized_capital'] - 100
                    
                    # Create dual-axis chart showing both absolute capital and normalized growth
                    fig = go.Figure()
                    
                    # Add normalized capital line
                    fig.add_trace(go.Scatter(
                        x=monthly_df['month'],
                        y=monthly_df['normalized_capital'],
                        mode='lines+markers',
                        name='Capital Growth (%)',
                        line=dict(color='blue', width=3),
                        marker=dict(size=8),
                        yaxis='y'
                    ))
                    
                    # Add monthly returns as bars
                    fig.add_trace(go.Bar(
                        x=monthly_df['month'],
                        y=monthly_df['monthly_return_pct'],
                        name='Monthly Returns (%)',
                        marker_color=['green' if x >= 0 else 'red' for x in monthly_df['monthly_return_pct']],
                        opacity=0.6,
                        yaxis='y2'
                    ))
                    
                    fig.update_layout(
                        title="Capital Growth vs Monthly Returns",
                        xaxis_title="Month",
                        yaxis=dict(title="Capital Growth (%)", side="left"),
                        yaxis2=dict(title="Monthly Returns (%)", side="right", overlaying="y"),
                        hovermode='x unified',
                        legend=dict(x=0.02, y=0.98)
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("Unable to load capital account information.")

def client_strategy_summary_page():
    """Client page for viewing strategy analysis - redirects to admin strategy analysis"""
    require_auth("client")
    # Redirect to the same strategy analysis page that admins use
    admin_strategy_analysis_page()

def admin_strategy_details_page():
    """Admin page for detailed strategy information"""
    require_auth("admin")
    
    st.title("📋 Strategy Details")
    st.markdown("Detailed view of stock trading performance and individual trades.")
    
    data_manager = st.session_state.data_manager
    
    if not data_manager.trades_df.empty:
        # Filter trades with quantity >= 2
        filtered_trades = data_manager.trades_df[data_manager.trades_df['quantity'] >= 2].copy()
        
        if not filtered_trades.empty:
            # Top Winners and Losers by Month
            st.subheader("🏆 Top Winners and Losers by Month")
            
            # Group by month and stock to calculate returns
            filtered_trades['month'] = filtered_trades['sell_date'].dt.to_period('M')
            monthly_stock_returns = filtered_trades.groupby(['month', 'stock']).agg({
                'buy_price': 'first',
                'sell_price': 'last',
                'quantity': 'sum',
                'profit_loss': 'sum'
            }).reset_index()
            
            # Calculate return percentage
            monthly_stock_returns['return_pct'] = ((monthly_stock_returns['sell_price'] - monthly_stock_returns['buy_price']) / monthly_stock_returns['buy_price'] * 100).round(2)
            
            # Get unique months
            months = sorted(monthly_stock_returns['month'].unique())
            
            for month in months:
                month_data = monthly_stock_returns[monthly_stock_returns['month'] == month]
                month_str = str(month)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**{month_str} - Top Winners**")
                    top_winners = month_data.nlargest(5, 'return_pct')[['stock', 'return_pct']]
                    if not top_winners.empty:
                        st.dataframe(top_winners, use_container_width=True)
                    else:
                        st.info("No winning trades this month")
                
                with col2:
                    st.write(f"**{month_str} - Top Losers**")
                    top_losers = month_data.nsmallest(5, 'return_pct')[['stock', 'return_pct']]
                    if not top_losers.empty:
                        st.dataframe(top_losers, use_container_width=True)
                    else:
                        st.info("No losing trades this month")
            
            # Detailed Trade Log
            st.subheader("📊 Detailed Trade Log")
            st.markdown("All trades with entry/exit prices and dates (quantity >= 2)")
            
            # Prepare trade log data (hide position sizes)
            trade_log = filtered_trades[['stock', 'buy_date', 'sell_date', 'buy_price', 'sell_price', 'return_pct', 'win_loss']].copy()
            trade_log['buy_date'] = trade_log['buy_date'].dt.strftime('%Y-%m-%d')
            trade_log['sell_date'] = trade_log['sell_date'].dt.strftime('%Y-%m-%d')
            trade_log['return_pct'] = trade_log['return_pct'].round(2)
            
            # Rename columns for better display
            trade_log.columns = ['Symbol', 'Entry Date', 'Exit Date', 'Entry Price', 'Exit Price', 'Return %', 'Result']
            
            st.dataframe(trade_log, use_container_width=True)
        else:
            st.info("No trades with quantity >= 2 found.")
    else:
        st.info("No trading data available yet. Please upload trade logs first.")

def client_strategy_details_page():
    """Client page for detailed strategy information"""
    require_auth("client")
    
    st.title("📋 Strategy Details")
    st.markdown("Detailed view of stock trading performance and individual trades.")
    
    data_manager = st.session_state.data_manager
    
    if not data_manager.trades_df.empty:
        # Filter trades with quantity >= 2
        filtered_trades = data_manager.trades_df[data_manager.trades_df['quantity'] >= 2].copy()
        
        if not filtered_trades.empty:
            # Top Winners and Losers by Month
            st.subheader("🏆 Top Winners and Losers by Month")
            
            # Group by month and stock to calculate returns
            filtered_trades['month'] = filtered_trades['sell_date'].dt.to_period('M')
            monthly_stock_returns = filtered_trades.groupby(['month', 'stock']).agg({
                'buy_price': 'first',
                'sell_price': 'last',
                'quantity': 'sum',
                'profit_loss': 'sum'
            }).reset_index()
            
            # Calculate return percentage
            monthly_stock_returns['return_pct'] = ((monthly_stock_returns['sell_price'] - monthly_stock_returns['buy_price']) / monthly_stock_returns['buy_price'] * 100).round(2)
            
            # Get unique months
            months = sorted(monthly_stock_returns['month'].unique())
            
            for month in months:
                month_data = monthly_stock_returns[monthly_stock_returns['month'] == month]
                month_str = str(month)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**{month_str} - Top Winners**")
                    top_winners = month_data.nlargest(5, 'return_pct')[['stock', 'return_pct']]
                    if not top_winners.empty:
                        st.dataframe(top_winners, use_container_width=True)
                    else:
                        st.info("No winning trades this month")
                
                with col2:
                    st.write(f"**{month_str} - Top Losers**")
                    top_losers = month_data.nsmallest(5, 'return_pct')[['stock', 'return_pct']]
                    if not top_losers.empty:
                        st.dataframe(top_losers, use_container_width=True)
                    else:
                        st.info("No losing trades this month")
            
            # Detailed Trade Log
            st.subheader("📊 Detailed Trade Log")
            st.markdown("All trades with entry/exit prices and dates (quantity >= 2)")
            
            # Prepare trade log data (hide position sizes)
            trade_log = filtered_trades[['stock', 'buy_date', 'sell_date', 'buy_price', 'sell_price', 'return_pct', 'win_loss']].copy()
            trade_log['buy_date'] = trade_log['buy_date'].dt.strftime('%Y-%m-%d')
            trade_log['sell_date'] = trade_log['sell_date'].dt.strftime('%Y-%m-%d')
            trade_log['return_pct'] = trade_log['return_pct'].round(2)
            
            # Rename columns for better display
            trade_log.columns = ['Symbol', 'Entry Date', 'Exit Date', 'Entry Price', 'Exit Price', 'Return %', 'Result']
            
            st.dataframe(trade_log, use_container_width=True)
        else:
            st.info("No trades with quantity >= 2 found.")
    else:
        st.info("No trading data available yet. Please ask the administrator to upload trade logs.")

if __name__ == "__main__":
    main()
