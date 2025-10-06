# 🚀 Quick Start Guide

Get your Multi-Client Trading Performance Dashboard up and running in minutes!

## ⚡ Quick Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Dashboard
```bash
streamlit run app.py
```

### 3. Login as Admin
- **Username**: `admin`
- **Password**: `admin123`

## 🎯 First Steps

### For Administrators

1. **Upload Trade Log**
   - Go to "📊 Upload Trade Log"
   - Use the provided template: `templates/trade_log_template.csv`
   - Ensure your file has these columns: `buy_date`, `sell_date`, `stock`, `buy_price`, `sell_price`, `quantity`

2. **Create Client Accounts**
   - Go to "👥 Manage Clients"
   - Create client accounts with starting capital
   - Set usernames and passwords for client login

3. **Configure System Settings**
   - Go to "⚙️ Configuration"
   - Set tax rate (default: 25%)
   - Set trader share (default: 40%)
   - Investor share auto-calculates as (100% - trader share)

4. **Add Capital Movements**
   - Go to "💰 Capital Movements"
   - Record client contributions and withdrawals
   - These affect monthly capital calculations

### For Clients

1. **Login with Your Credentials**
   - Use the username/password provided by admin

2. **View Capital Account**
   - See your starting capital, contributions, withdrawals
   - View monthly progression and returns
   - Monitor profit split calculations

3. **Check Strategy Summary**
   - View global trading performance
   - See monthly returns and win rates
   - No client-specific data shown (privacy maintained)

## 📊 Sample Data

### Trade Log Format
```csv
buy_date,sell_date,stock,buy_price,sell_price,quantity
2025-01-01,2025-01-15,AAPL,150.00,155.00,100
2025-01-02,2025-01-16,MSFT,300.00,295.00,50
```

### Client Creation
- **Username**: Unique login identifier
- **Name**: Full client name
- **Email**: Contact information
- **Starting Capital**: Initial investment amount

## 🔧 Key Features

### Profit Split Calculation
```
Monthly Return = (Total P&L / Total Position Size) × 100
Profit After Tax = Monthly Return × (1 - Tax Rate)
Investor Share = Profit After Tax × Investor Share %
Trader Share = Profit After Tax × Trader Share %
```

### Capital Progression
- **Starting**: Initial capital + contributions - withdrawals
- **Monthly**: Previous ending × (1 + monthly return)
- **Final**: Compounded monthly returns

## 🚨 Important Notes

### Data Privacy
- **Clients never see**: Raw position sizes, other client data
- **Clients can see**: Their own capital flow, global strategy performance
- **Admins can see**: All data, full system access

### File Requirements
- **Trade Logs**: Must have required columns, dates in YYYY-MM-DD format
- **File Size**: Keep under 100MB for optimal performance
- **Formats**: CSV, Excel (.xlsx, .xls) supported

### Security
- **Session Timeout**: 24 hours automatic logout
- **Password Security**: SHA-256 hashing
- **Role-Based Access**: Admin vs client permissions

## 🆘 Troubleshooting

### Common Issues

1. **"Module not found" errors**
   - Run: `pip install -r requirements.txt`

2. **"Authentication failed"**
   - Check username/password
   - Ensure account is active

3. **"File upload failed"**
   - Verify file format (CSV/Excel)
   - Check required columns
   - Ensure file size < 100MB

4. **"Calculation errors"**
   - Check configuration settings
   - Verify data format
   - Ensure no missing values

### Getting Help

- **Check logs**: Look for error messages in the dashboard
- **Verify data**: Ensure your files match the expected format
- **Review config**: Check system configuration settings
- **Contact admin**: For account or system issues

## 📈 Next Steps

### Advanced Usage
1. **Custom Calculations**: Modify profit split logic
2. **Data Export**: Download reports and data
3. **Performance Monitoring**: Track system performance
4. **User Management**: Manage multiple client accounts

### Customization
1. **Configuration**: Adjust tax rates and profit splits
2. **Data Processing**: Modify trade analysis logic
3. **UI Changes**: Customize dashboard appearance
4. **Integration**: Connect with external systems

## 🎉 You're Ready!

Your Multi-Client Trading Performance Dashboard is now running! 

- **Admins**: Start by uploading trades and creating clients
- **Clients**: Login to view your capital progression
- **Everyone**: Monitor performance and track returns

Need help? Check the full README.md for detailed documentation.





