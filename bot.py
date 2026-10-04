import os
from flask import Flask

web = Flask(__name__)

@web.get("/")
def health():
    return "Footballbozibot is permanently disabled", 200

if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    web.run(host="0.0.0.0", port=port, use_reloader=False)
