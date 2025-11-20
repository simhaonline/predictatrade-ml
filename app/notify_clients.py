# notify_clients.py (example, not tied to any framework)

import requests
from datetime import datetime, timedelta

API_BASE = "https://api.predictatrade.com"

# Pretend this comes from your SaaS DB
CLIENTS = [
    {"id": 1, "name": "Alice", "timezone": "Etc/GMT-3", "min_strength": "BUY"},
    {"id": 2, "name": "Bob",   "timezone": "Europe/London", "min_strength": "STRONG"},
]

STRENGTH_ORDER = ["STRONG SELL", "SELL", "NEUTRAL", "BUY", "STRONG BUY"]


def stronger_or_equal(signal, threshold):
    if threshold == "STRONG":
        return signal in ("STRONG BUY", "STRONG SELL")
    idx_s = STRENGTH_ORDER.index(signal)
    idx_t = STRENGTH_ORDER.index("BUY") if threshold == "BUY" else 0
    return idx_s >= idx_t


def fetch_report_for_client(client, target_date):
    url = f"{API_BASE}/api/reports/{target_date}?client_tz={client['timezone']}"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.json()["sessions"]


def main():
    today = datetime.utcnow().date().isoformat()

    for client in CLIENTS:
        sessions = fetch_report_for_client(client, today)
        alerts = []

        for session_name, rows in sessions.items():
            for row in rows:
                reco = row["trade_recommendation"]
                if not stronger_or_equal(reco, client["min_strength"]):
                    continue

                alerts.append(
                    {
                        "client_time": row.get("client_time"),
                        "session": session_name,
                        "reco": reco,
                        "score": row["gold_signal_score"],
                        "action": row["action"],
                    }
                )

        # Here you’d push alerts via email/SMS/webhook/etc.
        # print for demo
        print(f"Client {client['name']} alerts:")
        for a in alerts:
            print(" ", a)


if __name__ == "__main__":
    main()
