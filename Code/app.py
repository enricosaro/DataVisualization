"""
Inside Airbnb – Ghent dashboard

Run:
    python app.py
Then open:
    http://127.0.0.1:8051/
"""

import dash
from layout import get_app_layout
from callbacks import register_callbacks


# Single Dash instance.
app = dash.Dash(
    __name__,
    title="Inside Airbnb Gent",
)

# Page layout and callbacks
app.layout = get_app_layout()
register_callbacks(app)


if __name__ == "__main__":
    app.run(debug=False, host="127.0.0.1", port=8051)