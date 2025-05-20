import yfinance as yf
import pandas as pd
from fredapi import Fred

# Replace with your actual FRED API key
FRED_API_KEY = '50a101cdefe61ba1974b3c1dec658733'
fred = Fred(api_key=FRED_API_KEY)

# Map countries to their CPI FRED series IDs
cpi_series = {
    'US': 'CPIAUCSL',
    'JP': 'JPNCPIALLMINMEI',
    # Add other countries as needed here
}

def get_monthly_rate_of_return(ticker, start_date, end_date):
    data = yf.download(ticker, start=start_date, end=end_date, interval='1mo', auto_adjust=True)
    if data.empty:
        return None
    data['Monthly_Return'] = data['Close'].pct_change()
    data = data.dropna()
    return [{'month': d.strftime('%Y-%m'), 'monthly_return': r} for d, r in zip(data.index, data['Monthly_Return'])]

def get_monthly_inflation_rate(start_date, end_date, country='US'):
    if country not in cpi_series:
        return None
    series_id = cpi_series[country]
    cpi_data = fred.get_series(series_id, observation_start=start_date, observation_end=end_date)
    df = pd.DataFrame(cpi_data, columns=['CPI'])
    df.index = pd.to_datetime(df.index)
    df['Inflation_Rate'] = df['CPI'].pct_change()
    df = df.dropna()
    return [{'month': d.strftime('%Y-%m'), 'inflation_rate': r} for d, r in zip(df.index, df['Inflation_Rate'])]

def calculate_investment_performance(ticker, country, start_date, end_date, investment_amount, monthly_contribution=0):
    nominal = get_monthly_rate_of_return(ticker, start_date, end_date)
    inflation = get_monthly_inflation_rate(start_date, end_date, country)
    if nominal is None or inflation is None:
        return None
    
    nominal_dict = {item['month']: item['monthly_return'] for item in nominal}
    inflation_dict = {item['month']: item['inflation_rate'] for item in inflation}

    months = sorted(set(nominal_dict.keys()) & set(inflation_dict.keys()))

    monthly_data = []
    value = investment_amount

    nominal_returns = []
    inflation_rates = []
    real_returns = []

    for month in months:
        # Add monthly contribution at the start of the month (except first month since initial amount already counted)
        if month != months[0]:
            value += monthly_contribution

        nr = nominal_dict[month]
        ir = inflation_dict[month]
        real_ret = (1 + nr) / (1 + ir) - 1

        nominal_returns.append(nr)
        inflation_rates.append(ir)
        real_returns.append(real_ret)

        value = value * (1 + real_ret)

        monthly_data.append({
            'month': month,
            'nominal_return_percent': round(nr * 100, 4),
            'inflation_rate_percent': round(ir * 100, 4),
            'real_return_percent': round(real_ret * 100, 4),
            'investment_value': round(value, 2)
        })

    n_months = len(months)
    if n_months == 0:
        return None

    # Calculate total nominal return compounded
    total_nominal_return = 1
    for r in nominal_returns:
        total_nominal_return *= (1 + r)
    total_nominal_return -= 1

    total_real_return = value / investment_amount - 1

    annualized_nominal_return = (1 + total_nominal_return) ** (12 / n_months) - 1

    total_inflation = 1
    for ir in inflation_rates:
        total_inflation *= (1 + ir)
    total_inflation -= 1
    annualized_inflation = (1 + total_inflation) ** (12 / n_months) - 1

    annualized_real_return = (1 + total_real_return) ** (12 / n_months) - 1

    final_value_start_period = value / (1 + total_inflation)

    return {
        'monthly_data': monthly_data,
        'annualized_nominal_return_percent': round(annualized_nominal_return * 100, 2),
        'annualized_inflation_percent': round(annualized_inflation * 100, 2),
        'annualized_real_return_percent': round(annualized_real_return * 100, 2),
        'total_real_return_percent': round(total_real_return * 100, 2),
        'final_value_real_terms': round(value, 2),
        'final_value_start_period_dollars': round(final_value_start_period, 2),
        'investment_amount': investment_amount,
        'monthly_contribution': monthly_contribution,
        'months_count': n_months
    }
