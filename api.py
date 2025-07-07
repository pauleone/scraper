# === api.py ===
from flask import Flask, jsonify, request
import subprocess
import datetime

app = Flask(__name__)

@app.route("/scrape", methods=["POST"])
def run_scraper():
    try:
        print(f"[+] Trigger received at {datetime.datetime.now()}")
        result = subprocess.run(["python3", "scraper.py"], capture_output=True, text=True)
        print("STDOUT:\n", result.stdout)
        print("STDERR:\n", result.stderr)
        if result.returncode == 0:
            return jsonify({"status": "success", "output": result.stdout})
        else:
            return jsonify({"status": "error", "stderr": result.stderr}), 500
    except Exception as e:
        return jsonify({"status": "exception", "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)

