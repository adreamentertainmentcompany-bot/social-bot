import time
import subprocess
import urllib.request
import json
import sqlite3
from datetime import datetime

WEB_APP_URL = 'https://script.google.com/macros/s/AKfycby1Felv6esvZ_FLe73n_xc_Y398aGBxhpCAftrm-VE3aeQJA8vKHIAN9qjx_FXP8Cws/exec'

def send_post_request(payload):
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(WEB_APP_URL, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as response:
            return response.read().decode()
    except Exception as e:
        print(f"Failed to post: {e}")
        return None

def get_trigger_status():
    try:
        with urllib.request.urlopen(WEB_APP_URL) as response:
            return response.read().decode('utf-8').strip()
    except Exception as e:
        return ""

def poll_and_run():
    print("Listening for Run commands via Webhook...")
    while True:
        try:
            trigger_status = get_trigger_status()
            
            if trigger_status == "RUN_REQUESTED":
                print("Trigger detected! Starting social-bot...")
                send_post_request({"action": "update_status", "status": "RUNNING"})
                subprocess.run(["python3", "run_daily.py"], check=True)
                sync_results_to_sheet()
                send_post_request({"action": "update_status", "status": "READY"})
                print("Run complete. Results synced.")
        except Exception as e:
            pass
        time.sleep(60)

def sync_results_to_sheet():
    try:
        conn = sqlite3.connect('bot/bot_database.db')
        cursor = conn.cursor()
        today = datetime.now().strftime('%Y-%m-%d')
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='reddit_posts'")
        if not cursor.fetchone():
            conn.close()
            return
            
        cursor.execute("SELECT url, date_posted FROM reddit_posts WHERE date_posted LIKE ?", (f"{today}%",))
        new_posts = cursor.fetchall()
        conn.close()
        
        if new_posts:
            rows_to_append = [[url, date_posted, 0, "Pending Re-probe", "Automated by Bot"] for url, date_posted in new_posts]
            send_post_request({"action": "append_rows", "rows": rows_to_append})
    except Exception as e:
        print(f"Error syncing: {e}")

if __name__ == "__main__":
    poll_and_run()
