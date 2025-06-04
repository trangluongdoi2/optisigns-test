import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Common configuration variables
PORT = int(os.getenv('PORT', 8080))
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
FLASK_ENV = os.getenv('FLASK_ENV', 'production')
DD_API_KEY = os.getenv('DD_API_KEY')
DD_APP_KEY = os.getenv('DD_APP_KEY')
ZENDESK_EMAIL = os.getenv('ZENDESK_EMAIL')
ZENDESK_TOKEN = os.getenv('ZENDESK_TOKEN')
ZENDESK_SUBDOMAIN = os.getenv('ZENDESK_SUBDOMAIN')
OUTPUT_DIR = os.getenv('outputDir', './articles')
COUNT_ARTICLES = int(os.getenv('COUNT_ARTICLES', 30))

class SCHEDULE_CONFIG:
  SCHEDULER_API_ENABLED = True
  SCHEDULER_TIMEZONE = 'UTC'