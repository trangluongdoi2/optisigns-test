import os
import sys
import argparse
import hashlib
import json
from dotenv import load_dotenv
from scraper import ArticleScraper
from uploaderOpenAI import OpenAIUploader
from flask import Flask
from flask_apscheduler import APScheduler
from config import PORT, SCHEDULE_CONFIG

app = Flask(__name__)
app.config.from_object(SCHEDULE_CONFIG())
scheduler = APScheduler()

def handle():
  try:
    scraper = ArticleScraper()
    uploader = OpenAIUploader()

    # Run scraping
    savedFiles = scraper.scrapeArticles()
    uploader.handleFiles(savedFiles)
    
    return True
  except Exception as e:
    print(f"Error in scraping job: {str(e)}")
    return False

@scheduler.task('cron', id='my_daily_job', minute='*/10')
def dailyJob():
  handle()

@app.route("/")
def home():
  return 'OptiSigns Support Bot is running!'

@app.route("/health")
def healthCheck():
  return 'OK'

if __name__ == "__main__":
  scheduler.init_app(app)
  scheduler.start()

  parser = argparse.ArgumentParser()
  parser.add_argument('--cron', action='store_true', help='Run in cron mode')
  args = parser.parse_args()

  if args.cron:
    success = handle()
    sys.exit(0 if success else 1)
  else:
    port = PORT
    app.run(host='0.0.0.0', port=PORT, debug=False)