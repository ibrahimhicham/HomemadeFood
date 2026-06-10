import requests
from apscheduler.schedulers.background import BackgroundScheduler


def refresh_job():
    try:
        response = requests.get("https://homemadefood.onrender.com/api/dishes/refresh/")
        response2 = requests.get("https://homemadefood.onrender.com/api/orders/cancel-expired/")
        print("Refresh status:", response.status_code)
        print("Cancel expired orders status:", response2.status_code)
    except Exception as e:
        print("Error calling refresh:", e)
    

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(refresh_job, 'interval', minutes=1)
    scheduler.start()