import os
from flask import Flask, request, jsonify
from utils import calculate_investment_performance

app = Flask(__name__)

@app.route('/investment_performance', methods=['GET'])
def investment_performance():
    ticker = request.args.get('ticker')
    country = request.args.get('country', 'US')
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    investment_amount = request.args.get('investment_amount')
    monthly_contribution = request.args.get('monthly_contribution', 0)

    if not all([ticker, start_date, end_date, investment_amount]):
        return jsonify({'error': 'Missing required query parameters'}), 400

    try:
        investment_amount = float(investment_amount)
        monthly_contribution = float(monthly_contribution)
    except ValueError:
        return jsonify({'error': 'Invalid investment_amount or monthly_contribution value'}), 400

    result = calculate_investment_performance(ticker, country, start_date, end_date, investment_amount, monthly_contribution)

    if result is None:
        return jsonify({'error': 'Could not calculate investment performance'}), 404

    return jsonify(result)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Railway sets the port env var
    app.run(host='0.0.0.0', port=port, debug=True)
