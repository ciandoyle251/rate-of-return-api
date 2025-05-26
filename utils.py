import yfinance as yf
import pandas as pd
import numpy as np
from fredapi import Fred

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
    if not months:
        return None

    monthly_data = []
    nominal_value = investment_amount
    real_value = investment_amount

    # Cash flows for IRR calculation:
    # initial investment at time 0 (outflow)
    cash_flows = [-investment_amount]

    nominal_returns = []
    inflation_rates = []
    real_returns = []

    for i, month in enumerate(months):
        # Add monthly contribution at the *start* of the period except for the first month
        if i > 0:
            nominal_value += monthly_contribution
            real_value += monthly_contribution
            cash_flows.append(-monthly_contribution)

        nr = nominal_dict[month]
        ir = inflation_dict[month]
        real_ret = (1 + nr) / (1 + ir) - 1

        nominal_returns.append(nr)
        inflation_rates.append(ir)
        real_returns.append(real_ret)

        nominal_value *= (1 + nr)
        real_value *= (1 + real_ret)

        monthly_data.append({
            'month': month,
            'nominal_return_percent': round(nr * 100, 4),
            'inflation_rate_percent': round(ir * 100, 4),
            'real_return_percent': round(real_ret * 100, 4),
            'nominal_value': round(nominal_value, 2),
            'real_value': round(real_value, 2),
        })

    n_months = len(months)

    # Final cash inflow at end of investment period in real terms
    cash_flows.append(real_value)

    # Calculate IRR (monthly)
    try:
        irr_monthly = np.irr(cash_flows)
        annualized_real_return = (1 + irr_monthly) ** 12 - 1 if irr_monthly is not None else None
    except Exception:
        annualized_real_return = None

    # Annualized nominal and inflation returns (geometric average)
    total_nominal_return = np.prod([1 + r for r in nominal_returns]) - 1
    total_inflation = np.prod([1 + ir for ir in inflation_rates]) - 1

    annualized_nominal_return = (1 + total_nominal_return) ** (12 / n_months) - 1
    annualized_inflation = (1 + total_inflation) ** (12 / n_months) - 1

    # Final value expressed in start period dollars
    final_value_start_period_dollars = real_value / (1 + total_inflation)

    return {
        'monthly_data': monthly_data,
        'annualized_nominal_return_percent': round(annualized_nominal_return * 100, 2),
        'annualized_inflation_percent': round(annualized_inflation * 100, 2),
        'annualized_real_return_percent': round(annualized_real_return * 100, 2) if annualized_real_return is not None else None,
        'final_value_real_terms': round(real_value, 2),
        'final_value_start_period_dollars': round(final_value_start_period_dollars, 2),
        'investment_amount': investment_amount,
        'monthly_contribution': monthly_contribution,
        'months_count': n_months
    }
