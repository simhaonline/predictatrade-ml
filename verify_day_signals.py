# verify_day_signals.py

from datetime import datetime, date
from collections import Counter

from app.config import settings
from app.reports.multi_session_report import generate_multi_session_report


def main(s: str | None = None):
    if s:
        d = datetime.strptime(s, "%Y-%m-%d").date()
    else:
        d = datetime.utcnow().date()

    report = generate_multi_session_report(d)

    print(f"Signal distribution for {d.isoformat()}")
    for session_name, rows in report.items():
        counts = Counter(row["trade_recommendation"] for row in rows)
        print(f"\nSession: {session_name}")
        for k in ["STRONG BUY", "BUY", "NEUTRAL", "SELL", "STRONG SELL"]:
            print(f"  {k:12}: {counts.get(k, 0)}")


if __name__ == "__main__":
    import sys

    arg = sys.argv[1] if len(sys.argv) > 1 else None
    main(arg)
