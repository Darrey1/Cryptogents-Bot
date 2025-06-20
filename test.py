from blofin import BloFinClient
from blofin.utils import get_server_time as original_get_time
import blofin.auth as _auth
from datetime import datetime
api_key='b8fb3fadd6fb45299b11cd75843e7a53'
api_secret='f2af6128cb1b40998361a221533b0fcc'
passphrase='CG1234'
def safe_get_server_time():
    import time
    try:
        server_time = original_get_time()
        return str(int(server_time)) if server_time else str(int(time.time() * 1000))
    except Exception:
        return str(int(time.time() * 1000))

_auth.get_server_time = safe_get_server_time


client = BloFinClient(
    api_key=api_key,
    api_secret=api_secret,
    passphrase=passphrase,
    use_server_time=True, 
)

referral = "CryptoGents"
uuid = 18539402303
uuid2 = 21306966544
# invitee_info = client.affiliate.get_invitees(uid=5802024463)
# print(invitee_info)


from datetime import datetime
from typing import List, Dict

def get_monthly_trade_report(affiliate_uid: str, year: int) -> List[Dict]:
    report = []

    for month in range(1, 13):
        start = datetime(year, month, 1)
        end = datetime(year, month % 12 + 1, 1) if month < 12 else datetime(year + 1, 1, 1)
        begin_ms = int(start.timestamp() * 1000)
        end_ms = int(end.timestamp() * 1000)

        # Call the API
        res = client.affiliate.get_invitees(uid=affiliate_uid, begin=str(begin_ms), end=str(end_ms))
        invitees = res.get("data", [])

        total_volume = 0.0
        total_commission = 0.0
        active_traders = 0

        for invitee in invitees:
            volume = float(invitee.get("totalTradingVolume", 0))
            commission = float(invitee.get("totalCommission", 0))
            deposit = float(invitee.get("totalDeposit", 0))

            if volume > 0 or deposit > 0:
                active_traders += 1
                total_volume += volume
                total_commission += commission

        report.append({
            "month": f"{year}-{month:02}",
            "traders": active_traders,
            "total_volume": round(total_volume, 4),
            "total_commission": round(total_commission, 4)
        })

    return report



# def count_invitee_trades(invitee_uid: str, year: int, month: int):
#     start = datetime(year, month, 1)
#     if month < 12:
#         end = datetime(year, month+1, 1)
#     else:
#         end = datetime(year+1, 1, 1)

#     start_ms = int(start.timestamp() * 1000)
#     end_ms = int(end.timestamp() * 1000)

#     orders = client.trading.get_trade_history(
#         uid=invitee_uid,
#         begin=str(start_ms),
#         end=str(end_ms)
#     )
#     return len(orders.get("data", []))

# # Example
# trades = count_invitee_trades(uuid, 2025, 6)
# print(f"Trades done in June 2025: {trades}")


report = get_monthly_trade_report(5802024463, 2025)

for r in report:
    print(f"Month: {r['month']} → Traders: {r['traders']} | Volume: {r['total_volume']} | Commission: {r['total_commission']}")








