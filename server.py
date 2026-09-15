from flask import Flask, jsonify
from flask_cors import CORS
import requests
import time

app = Flask(__name__)
CORS(app)

session = requests.Session()

session.headers.update({
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "en-US,en;q=0.9"
})


def get_yahoo(symbol):

    url = (
        "https://query1.finance.yahoo.com/v8/finance/chart/"
        + symbol
        + "?interval=1m&range=1d"
    )

    try:

        r = session.get(url, timeout=10)

        print("Yahoo status:", r.status_code)
        print("Yahoo content-type:", r.headers.get("content-type"))

        if r.status_code != 200:
            print("Yahoo response:", r.text[:300])
            return {
                "price": None,
                "change": None
            }

        if "json" not in r.headers.get("content-type", "").lower():
            print("Yahoo returned non-JSON:", r.text[:300])
            return {
                "price": None,
                "change": None
            }

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

        print("Yahoo error:", repr(e))

        return {
            "price": None,
            "change": None
        }


def get_nse_data():

    try:

        r = session.get(
            "https://www.nseindia.com",
            timeout=10
        )

        print("NSE homepage status:", r.status_code)

        time.sleep(1)

        url = (
            "https://www.nseindia.com/api/"
            "option-chain-indices?symbol=NIFTY"
        )

        r = session.get(
            url,
            timeout=15
        )

        print("NSE API status:", r.status_code)
        print("NSE content-type:", r.headers.get("content-type"))

        if r.status_code != 200:
            print("NSE response:", r.text[:300])

            return {
                "callOI": None,
                "putOI": None,
                "callCOI": None,
                "putCOI": None,
                "pcr": None
            }

        if "json" not in r.headers.get("content-type", "").lower():
            print("NSE returned non-JSON:", r.text[:300])

            return {
                "callOI": None,
                "putOI": None,
                "callCOI": None,
                "putCOI": None,
                "pcr": None
            }

        data = r.json()

        rows = data.get("records", {}).get("data", [])

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
                )

                total_call_change += ce.get(
                    "changeinOpenInterest", 0
                )

            if pe:

                total_put_oi += pe.get(
                    "openInterest", 0
                )

                total_put_change += pe.get(
                    "changeinOpenInterest", 0
                )

        pcr = None

        if total_call_oi > 0:

            pcr = round(
                total_put_oi / total_call_oi,
                2
            )

        return {

            "callOI": total_call_oi,
            "putOI": total_put_oi,
            "callCOI": total_call_change,
            "putCOI": total_put_change,
            "pcr": pcr

        }

    except Exception as e:

        print("NSE error:", repr(e))

        return {

            "callOI": None,
            "putOI": None,
            "callCOI": None,
            "putCOI": None,
            "pcr": None

        }


@app.route("/")
def home():

    return jsonify({

        "status": "NIFTY API running",
        "message": "Market data service is online"

    })


@app.route("/api/market")
def market():

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


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=10000
    )
