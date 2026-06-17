import concurrent.futures
import os

import requests
from apscheduler.schedulers.background import BackgroundScheduler


PORT = os.environ.get('PORT', '8000')

URLS = [
    f"https://homemade-food-msvc.vercel.app/api/dishes/refresh/",
    f"https://homemade-food-msvc.vercel.app/api/orders/cancel-expired/",
]


TIMEOUT = 10


def refresh_job():
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as exe:
            futures = [exe.submit(requests.get, url, timeout=TIMEOUT) for url in URLS]
            for f in concurrent.futures.as_completed(futures):
                resp = f.result()
                print(f"Status {resp.url}: {resp.status_code}")
    except Exception as e:
        print("Error calling refresh:", e)


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(refresh_job, 'interval', seconds=5, max_instances=1)
    scheduler.start()