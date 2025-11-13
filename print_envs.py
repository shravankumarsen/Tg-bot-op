# print_envs.py - debug helper to log the important env vars (do NOT commit secrets)
import os, sys, json
keys = ["TELEGRAM_API","TELEGRAM_HASH","BOT_TOKEN","FSUB_ID","DUMP_CHAT_ID","USER_SESSION_STRING"]
out = {k: (("SET" if os.environ.get(k) else "MISSING")) for k in keys}
print("ENV CHECK:", json.dumps(out, indent=2))
# also print config.env preview if exists
if os.path.exists("config.env"):
    print("--- config.env preview ---")
    with open("config.env","r") as f:
        print("\\n".join([l.rstrip() for l in f.readlines()[:20]]))
sys.stdout.flush()
# keep the container alive for a bit so logs appear
import time
time.sleep(5)
