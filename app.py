from flask import Flask, request

app = Flask(__name__)

def get_visitor_ip():
    # Check for common headers used by proxies to pass real IP
    if "X-Forwarded-For" in request.headers:
        # It may contain multiple IPs if multiple proxies, take the first one
        ip = request.headers["X-Forwarded-For"].split(",")[0].strip()
    elif "CF-Connecting-IP" in request.headers:
        ip = request.headers["CF-Connecting-IP"]
    else:
        ip = request.remote_addr
    return ip

@app.route("/")
def home():
    visitor_ip = get_visitor_ip()
    return f"<h1>Your IP is: {visitor_ip}</h1>"

if __name__ == "__main__":
    # Always use 0.0.0.0 for hosting on Pella
    app.run(host="0.0.0.0", port=5000, debug=True)
