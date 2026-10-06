import time
import subprocess
import gspread # pip install gspread

SHEET_ID = '1Wq2m_tA6nxz2zBYDrPFIGuEYEzldBaHjavM-MJ_jUEA'
SERVICE_ACCOUNT_FILE = 'google_credentials.json'

client = gspread.service_account(filename=SERVICE_ACCOUNT_FILE)

def poll_and_run():
    print("Listening for Run commands from Google Sheets...")
    while True:
        try:
            sheet = client.open_by_key(SHEET_ID).worksheet("Dashboard")
            trigger_status = sheet.acell('Z1').value
            
            if trigger_status == "RUN_REQUESTED":
                print("Trigger detected! Starting social-bot...")
                sheet.update_acell('Z1', 'RUNNING')
                subprocess.run(["python3", "run_daily.py"], check=True)
                sync_results_to_sheet(sheet)
                sheet.update_acell('Z1', 'READY')
                print("Run complete. Results synced.")
        except Exception as e:
            pass
        time.sleep(60)

def sync_results_to_sheet(sheet):
    import sqlite3
    from datetime import datetime
    conn = sqlite3.connect('bot/bot_database.db')
    cursor = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute("SELECT url, date_posted FROM reddit_posts WHERE date_posted LIKE ?", (f"{today}%",))
    new_posts = cursor.fetchall()
    for post in new_posts:
        url, date_posted = post
        sheet.append_row([url, date_posted, 0, "Pending Re-probe", "Automated by Bot"])
    conn.close()

if __name__ == "__main__":
    poll_and_run()
