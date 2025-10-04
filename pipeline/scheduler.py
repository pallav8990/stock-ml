from apscheduler.schedulers.blocking import BlockingScheduler
import subprocess, yaml, pytz

IST = pytz.timezone("Asia/Kolkata")
sch = BlockingScheduler(timezone=IST)

cfg = yaml.safe_load(open("conf/schedule.yaml"))

def run(py):
    print(">>", py); subprocess.run(["python", f"pipeline/{py}"], check=True)

@sch.scheduled_job("cron", hour=cfg["collect_hour"], minute=cfg["collect_minute"])
def job_collect():
    run("build_universe.py")
    run("collect_prices_nse.py")
    run("collect_news.py")
    run("build_features.py")

@sch.scheduled_job("cron", hour=cfg["train_hour"], minute=cfg["train_minute"])
def job_train():
    run("train_model.py")

@sch.scheduled_job("cron", hour=cfg["predict_hour"], minute=cfg["predict_minute"])
def job_predict():
    run("predict.py")

@sch.scheduled_job("cron", hour=cfg["evaluate_hour"], minute=cfg["evaluate_minute"])
def job_eval():
    run("evaluate_and_explain.py")

if __name__ == "__main__":
    sch.start()
