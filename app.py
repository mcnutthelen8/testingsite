from flask import Flask, render_template, abort, request
from pymongo import MongoClient
import requests
from datetime import datetime, timezone, timedelta

app = Flask(__name__)

# MongoDB setup
mongo_uri = "mongodb+srv://redgta36:J6n7Hoz2ribHmMmx@moneyfarm.wwzcs.mongodb.net/?retryWrites=true&w=majority&appName=moneyfarm"
client = MongoClient(mongo_uri)
db = client['MoneyFarmV10']
maindb_collection = db["maindb"]

# IPQualityScore API key
ipqs_key = "BEPgiVi4XCx0URXqigTXonNwsLbkRdez"

def get_visitor_ip():
    if "X-Forwarded-For" in request.headers:
        ip = request.headers["X-Forwarded-For"].split(",")[0].strip()
    elif "CF-Connecting-IP" in request.headers:
        ip = request.headers["CF-Connecting-IP"]
    else:
        ip = request.remote_addr
    return ip

@app.route("/<paste_id>")
def redirect_paste(paste_id):
    doc = maindb_collection.find_one({"type": "website"})
    if not doc:
        return abort(404, "No links found in database.")

    links_dict = doc.get("links", {})
    pastebin_url = None
    for url, pid in links_dict.items():
        if pid == paste_id:
            pastebin_url = url
            break

    if not pastebin_url:
        return abort(404, "Link not found.")

    user_ip = get_visitor_ip()
    if not user_ip:
        user_ip = "Unknown"

    ipqs_url = f'https://ipqualityscore.com/api/json/ip/{ipqs_key}/{user_ip}?strictness=3&allow_public_access_points=true&lighter_penalties=true&mobile=true'
    try:
        r = requests.get(ipqs_url, timeout=5)
        ip_data = r.json()
    except Exception as e:
        return f"Error checking IP: {e}"

    country = ip_data.get("country_code", "N/A")
    is_vpn = ip_data.get("vpn", False)
    is_proxy = ip_data.get("proxy", False)

    # Sri Lanka timezone offset +05:30
    sl_timezone = timezone(timedelta(hours=5, minutes=30))
    timestamp = datetime.now(sl_timezone).strftime("%Y-%m-%d %H:%M:%S")

    ip_list = doc.get("ip_list", {})
    ip_list[user_ip] = timestamp
    maindb_collection.update_one({"_id": doc["_id"]}, {"$set": {"ip_list": ip_list}})

    if is_vpn:  # or is_proxy:
        return render_template("blocked.html", ip=user_ip, country=country, paste_id=paste_id)
    else:
        return render_template("show_link.html", ip=user_ip, country=country, pastebin_url=pastebin_url)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)

