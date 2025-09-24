from flask import Flask, render_template, abort, request, redirect, url_for
from pymongo import MongoClient
import requests
from datetime import datetime

app = Flask(__name__)

# MongoDB setup
mongo_uri = "mongodb+srv://redgta36:J6n7Hoz2ribHmMmx@moneyfarm.wwzcs.mongodb.net/?retryWrites=true&w=majority&appName=moneyfarm"
client = MongoClient(mongo_uri)
db = client['MoneyFarmV10']
maindb_collection = db["maindb"]

# IPQualityScore API key
ipqs_key = "Bfg1dzryVqbpSwtbxgWb1uVkXLrr1Nzr"

@app.route("/<paste_id>")
def redirect_paste(paste_id):
    # Serve checking page first
    return render_template("checking.html", paste_id=paste_id)

@app.route("/check/<paste_id>", methods=["POST"])
def check_ip(paste_id):
    # Get visitor IP from POST
    visitor_ip = request.json.get("ip")
    if not visitor_ip:
        return "IP not provided", 400

    # Find document
    doc = maindb_collection.find_one({"type": "website"})
    if not doc:
        return abort(404, "No links found in database.")

    # Check if paste_id exists
    links_dict = doc.get("links", {})
    pastebin_url = None
    for url, pid in links_dict.items():
        if pid == paste_id:
            pastebin_url = url
            break

    if not pastebin_url:
        return abort(404, "Link not found.")

    # Call IPQualityScore API
    ipqs_url = f'https://ipqualityscore.com/api/json/ip/{ipqs_key}/{visitor_ip}?strictness=3&allow_public_access_points=true&lighter_penalties=true&mobile=true'
    try:
        r = requests.get(ipqs_url, timeout=5)
        ip_data = r.json()
    except Exception as e:
        return f"Error checking IP: {e}"

    country = ip_data.get("country_code", "N/A")
    is_vpn = ip_data.get("vpn", False)
    is_proxy = ip_data.get("proxy", False)

    # Log IP to MongoDB
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ip_list = doc.get("ip_list", {})
    ip_list[visitor_ip] = timestamp
    maindb_collection.update_one({"_id": doc["_id"]}, {"$set": {"ip_list": ip_list}})

    # Redirect based on IP check
    if is_vpn:  # or is_proxy
        return {"redirect": url_for("blocked", paste_id=paste_id, ip=visitor_ip, country=country)}
    else:
        return {"redirect": url_for("show_link", pastebin_url=pastebin_url, ip=visitor_ip, country=country)}

@app.route("/blocked")
def blocked():
    ip = request.args.get("ip", "Unknown")
    country = request.args.get("country", "N/A")
    paste_id = request.args.get("paste_id")
    return render_template("blocked.html", ip=ip, country=country, paste_id=paste_id)

@app.route("/show_link")
def show_link():
    ip = request.args.get("ip", "Unknown")
    country = request.args.get("country", "N/A")
    pastebin_url = request.args.get("pastebin_url")
    return render_template("show_link.html", ip=ip, country=country, pastebin_url=pastebin_url)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)
