"""Simple Flask web app for Monte Carlo option pricing.

The server exposes both an HTML form and a JSON API to submit parameters
for Monte Carlo simulation using :mod:`monte_carlo`. It evaluates user-provided
payoff expressions per simulated path and returns the discounted average.
"""
from __future__ import annotations

from typing import Any, Dict, Tuple

from flask import Flask, jsonify, render_template_string, request

from monte_carlo import MonteCarloParameters, expression_payoff, monte_carlo_price

app = Flask(__name__)


FORM_TEMPLATE = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Monte Carlo Option Pricer</title>
    <style>
      body { font-family: Arial, sans-serif; margin: 2rem; max-width: 840px; }
      h1 { margin-bottom: 0.25rem; }
      form { margin-top: 1rem; display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 0.75rem 1rem; }
      label { display: flex; flex-direction: column; font-weight: bold; }
      input, textarea { padding: 0.5rem; font-size: 1rem; }
      .full-width { grid-column: 1 / -1; }
      .result { margin-top: 1.5rem; padding: 1rem; border-radius: 8px; background: #f1f5f9; }
      .error { background: #ffe6e6; color: #7f1d1d; }
      button { padding: 0.75rem 1.25rem; font-size: 1rem; background: #2563eb; color: white; border: none; border-radius: 6px; cursor: pointer; }
      button:hover { background: #1d4ed8; }
      code { background: #e2e8f0; padding: 0.15rem 0.3rem; border-radius: 4px; }
    </style>
  </head>
  <body>
    <h1>Monte Carlo Option Pricer</h1>
    <p>Simulate geometric Brownian motion paths in the browser and evaluate any payoff expression that references <code>path</code> and <code>np</code>.</p>
    <form method="post">
      <label>Spot price
        <input type="number" step="any" name="spot" value="{{ form_data.spot }}" required />
      </label>
      <label>Risk-free rate (continuous)
        <input type="number" step="any" name="rate" value="{{ form_data.rate }}" required />
      </label>
      <label>Time to maturity (years)
        <input type="number" step="any" name="time" value="{{ form_data.time }}" required />
      </label>
      <label>Volatility (annualized)
        <input type="number" step="any" name="volatility" value="{{ form_data.volatility }}" required />
      </label>
      <label>Dividend yield
        <input type="number" step="any" name="dividend_yield" value="{{ form_data.dividend_yield }}" />
      </label>
      <label>Number of paths
        <input type="number" step="1" min="1" name="paths" value="{{ form_data.paths }}" required />
      </label>
      <label>Steps per path
        <input type="number" step="1" min="1" name="steps" value="{{ form_data.steps }}" required />
      </label>
      <label>Random seed (optional)
        <input type="number" step="1" name="seed" value="{{ form_data.seed }}" />
      </label>
      <label class="full-width">Payoff expression (use <code>path</code> and <code>np</code>)
        <textarea name="payoff_expr" rows="3">{{ form_data.payoff_expr }}</textarea>
      </label>
      <div class="full-width"><button type="submit">Estimate price</button></div>
    </form>

    {% if price is not none %}
      <div class="result">Estimated option price: <strong>{{ price }}</strong></div>
    {% endif %}

    {% if error %}
      <div class="result error">Error: {{ error }}</div>
    {% endif %}

    <div class="result">
      <h2>Example payoffs</h2>
      <ul>
        <li>European call: <code>np.maximum(path[-1] - 100, 0)</code></li>
        <li>European put: <code>np.maximum(100 - path[-1], 0)</code></li>
        <li>Asian call (average): <code>np.maximum(np.mean(path) - 100, 0)</code></li>
        <li>Lookback call (max): <code>np.maximum(np.max(path) - 100, 0)</code></li>
      </ul>
    </div>
  </body>
</html>
"""


def _coerce_payload(data: Dict[str, Any]) -> Tuple[MonteCarloParameters, str]:
    """Convert user input into validated parameters and payoff expression."""

    def _get(key: str, default: Any = None) -> Any:
        return data.get(key, default)

    payoff_expr = (_get("payoff_expr") or "np.maximum(path[-1] - 100, 0)").strip()

    params = MonteCarloParameters(
        spot=float(_get("spot")),
        rate=float(_get("rate")),
        time=float(_get("time")),
        volatility=float(_get("volatility")),
        dividend_yield=float(_get("dividend_yield", 0.0) or 0.0),
        paths=int(_get("paths")),
        steps=int(_get("steps")),
        seed=int(_get("seed")) if _get("seed") not in (None, "") else None,
    )

    return params, payoff_expr


@app.route("/", methods=["GET", "POST"])
def index():
    """Render HTML form for interactive pricing."""

    default_form = {
        "spot": 100,
        "rate": 0.05,
        "time": 1.0,
        "volatility": 0.2,
        "dividend_yield": 0.0,
        "paths": 50000,
        "steps": 252,
        "seed": 42,
        "payoff_expr": "np.maximum(path[-1] - 100, 0)",
    }

    price = None
    error = None
    form_data: Dict[str, Any] = dict(default_form)

    if request.method == "POST":
        form_data.update(request.form)
        try:
            params, payoff_expr = _coerce_payload(form_data)
            payoff_fn = expression_payoff(payoff_expr)
            price = round(monte_carlo_price(params, payoff_fn), 6)
        except Exception as exc:  # noqa: BLE001 - surface error to user
            error = str(exc)

    return render_template_string(
        FORM_TEMPLATE,
        price=price,
        error=error,
        form_data=form_data,
    )


@app.post("/api/price")
def api_price():
    """JSON API endpoint to estimate an option price."""

    data = request.get_json(force=True, silent=True) or {}
    try:
        params, payoff_expr = _coerce_payload(data)
        payoff_fn = expression_payoff(payoff_expr)
        price = monte_carlo_price(params, payoff_fn)
    except Exception as exc:  # noqa: BLE001 - return client error
        return jsonify({"error": str(exc)}), 400

    return jsonify({"price": price, "payoff_expr": payoff_expr})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
