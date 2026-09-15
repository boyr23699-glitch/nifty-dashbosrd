from flask import Flask, jsonify
from flask_cors import CORS
import requests
import time

app = Flask(name)
CORS(app)

session = requests.Session()

session.headers.update({
"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140.0.0.0 Safari/537.36",
"Accept": "application/json, text/plain, /",
"Accept-Language": "en-US,en;q=0.9",
"Referer": "https://www.nseindia.com/",
"Connection": "keep-alive"
})

def empty_options():
return {
"callOI": None,
"putOI": None,
"callCOI": None,
"putCOI": None,
"pcr": None
}

def get_yahoo(symbol):

url = (
    "https://query1.finance.yahoo.com/v8/finance/chart/"
    + symbol
    + "?interval=1m&range=1d"
)

try:
    r = session.get(url, timeout=10)

    print("YAHOO STATUS:", r.status_code)

    if r.status_code != 200:
        print("YAHOO ERROR:", r.text[:500])
        return {"price": None, "change": None}

    data = r.json()

    result = data["chart"]["result"][0]
    meta = result["meta"]

    price = meta.get("regularMarketPrice")
    previous = meta.get("previousClose")

    change = None

    if price is not None and previous is not None:
        change = round(price - previous, 2)

    return {
        "price": price,
        "change": change
    }

except Exception as e:
    print("YAHOO EXCEPTION:", repr(e))
    return {"price": None, "change": None}

def get_nse_data():

try:

    # Step 1: Open NSE homepage to obtain cookies
    home_url = "https://www.nseindia.com/"

    home = session.get(
        home_url,
        timeout=15
    )

    print("NSE HOME STATUS:", home.status_code)
    print("NSE COOKIES:", session.cookies.get_dict())

    time.sleep(2)

    # Step 2: Request NIFTY option chain
    api_url = (
        "https://www.nseindia.com/api/"
        "option-chain-indices?symbol=NIFTY"
    )

    response = session.get(
        api_url,
        timeout=20,
        headers={
            "User-Agent": session.headers["User-Agent"],
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://www.nseindia.com/option-chain",
            "Accept-Language": "en-US,en;q=0.9"
        }
    )

    print("NSE API STATUS:", response.status_code)
    print("NSE CONTENT TYPE:", response.headers.get("content-type"))
    print("NSE RESPONSE:", response.text[:1000])

    if response.status_code != 200:
        return empty_options()

    if "json" not in response.headers.get(
        "content-type", ""
    ).lower():

        print("NSE DID NOT RETURN JSON")
        return empty_options()

    data = response.json()

    records = data.get("records", {})
    rows = records.get("data", [])

    print("NSE OPTION ROWS:", len(rows))

    if not rows:
        print("NSE OPTION DATA IS EMPTY")
        return empty_options()

    total_call_oi = 0
    total_put_oi = 0

    total_call_change = 0
    total_put_change = 0

    for row in rows:

        ce = row.get("CE")
        pe = row.get("PE")

        if ce:

            total_call_oi += ce.get(
                "openInterest", 0
            ) or 0

            total_call_change += ce.get(
                "changeinOpenInterest", 0
            ) or 0

        if pe:

            total_put_oi += pe.get(
                "openInterest", 0
            ) or 0

            total_put_change += pe.get(
                "changeinOpenInterest", 0
            ) or 0

    pcr = None

    if total_call_oi > 0:
        pcr = round(
            total_put_oi / total_call_oi,
            2
        )

    print("TOTAL CALL OI:", total_call_oi)
    print("TOTAL PUT OI:", total_put_oi)
    print("TOTAL CALL COI:", total_call_change)
    print("TOTAL PUT COI:", total_put_change)
    print("PCR:", pcr)

    return {
        "callOI": total_call_oi,
        "putOI": total_put_oi,
        "callCOI": total_call_change,
        "putCOI": total_put_change,
        "pcr": pcr
    }

except Exception as e:

    print("NSE EXCEPTION:", repr(e))

    return empty_options()

@app.route("/")
def home():

return jsonify({
    "status": "NIFTY API running",
    "message": "Market data service is online"
})

@app.route("/api/market")
def market():

print("========== MARKET REQUEST ==========")

nifty = get_yahoo("^NSEI")

vix = get_yahoo("^INDIAVIX")

options = get_nse_data()

return jsonify({

    "price": nifty["price"],
    "change": nifty["change"],

    "volume": None,

    "callOI": options["callOI"],
    "putOI": options["putOI"],

    "callCOI": options["callCOI"],
    "putCOI": options["putCOI"],

    "pcr": options["pcr"],

    "fii": None,
    "dii": None,
    "gift": None,

    "vix": vix["price"],

    "support": None,
    "resistance": None,

    "updated": int(time.time())

})

if name == "main":

app.run(
    host="0.0.0.0",
    port=10000
)
