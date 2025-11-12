# web.py
import os
import subprocess
from flask import Flask, jsonify

app = Flask(__name__)
BOT_CMD = os.environ.get("BOT_CMD", "python3 bot.py")
# If you want the bot to run with python (venv)/python3, adjust BOT_CMD accordingly.

bot_proc = None

@app.before_first_request
def start_bot_process():
    global bot_proc
    if bot_proc is None:
        # Start the bot as a subprocess in the background
        # Use shell=False for safety by passing a list if you want; here split for convenience
        try:
            parts = BOT_CMD.split()
            bot_proc = subprocess.Popen(parts)
            app.logger.info(f"Started bot subprocess pid={bot_proc.pid}")
        except Exception as e:
            app.logger.error(f"Failed to start bot subprocess: {e}")

@app.route("/")
def index():
    return "OK", 200

@app.route("/health")
def health():
    alive = bot_proc is not None and bot_proc.poll() is None
    return jsonify({"bot_running": alive, "bot_pid": bot_proc.pid if bot_proc else None})

@app.route("/stop-bot", methods=["POST"])
def stop_bot():
    global bot_proc
    if bot_proc and bot_proc.poll() is None:
        bot_proc.terminate()
        return jsonify({"stopped": True}), 200
    return jsonify({"stopped": False}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
