from flask import Flask, request, render_template, abort, jsonify
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
def index(paste_id):
    # Show initial loading page
    return render_template("index.html", paste_id=paste_id)

@app.route("/check_ip", methods=["POST"])
def check_ip():
    data = request.json
    paste_id = data.get("paste_id")
    visitor_ip = data.get("ip")

    if not paste_id or not visitor_ip:
        return jsonify({"error": "Missing paste_id or IP"}), 400

    # Find document
    doc = maindb_collection.find_one({"type": "website"})
    if not doc:
        return jsonify({"error": "No links found in database."}), 404

    # Check if paste_id exists
    links_dict = doc.get("links", {})
    pastebin_url = None
    for url, pid in links_dict.items():
        if pid == paste_id:
            pastebin_url = url
            break

    if not pastebin_url:
        return jsonify({"error": "Link not found."}), 404

    # Call IPQualityScore API
    ipqs_url = f'https://ipqualityscore.com/api/json/ip/{ipqs_key}/{visitor_ip}?strictness=3&allow_public_access_points=true&lighter_penalties=true&mobile=true'
    try:
        r = requests.get(ipqs_url, timeout=5)
        ip_data = r.json()
    except Exception as e:
        return jsonify({"error": f"Error checking IP: {e}"}), 500

    country = ip_data.get("country_code", "N/A")
    is_vpn = ip_data.get("vpn", False)
    is_proxy = ip_data.get("proxy", False)

    # Get server local timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Log IP to MongoDB
    ip_list = doc.get("ip_list", {})
    ip_list[visitor_ip] = timestamp
    maindb_collection.update_one({"_id": doc["_id"]}, {"$set": {"ip_list": ip_list}})

    # Return result to frontend
    if is_vpn:  # or is_proxy if you want
        return jsonify({"status": "blocked", "ip": visitor_ip, "country": country})
    else:
        return jsonify({"status": "allowed", "ip": visitor_ip, "country": country, "pastebin_url": pastebin_url})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)
