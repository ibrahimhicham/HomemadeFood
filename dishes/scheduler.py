import requests
from apscheduler.schedulers.background import BackgroundScheduler


def refresh_job():
    try:
        response = requests.get("http://127.0.0.1:8000/api/dishes/refresh/")
        print("Refresh status:", response.status_code)
    except Exception as e:
        print("Error calling refresh:", e)


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(refresh_job, 'interval', minutes=1)
    scheduler.start()