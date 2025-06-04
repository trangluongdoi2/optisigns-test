import os
import logging
from datadog_api_client.v2 import ApiClient, ApiException, Configuration
from datadog_api_client.v2.api import logs_api
from datadog_api_client.v2.models import HTTPLog, HTTPLogItem
from config import DD_API_KEY, DD_APP_KEY

class DatadogHandler(logging.StreamHandler):
  def __init__(self, apiKey, appKey, serviceName, environment):
    logging.StreamHandler.__init__(self)
    self.configuration = Configuration()
    self.configuration.api_key['apiKeyAuth'] = apiKey
    self.configuration.api_key['appKeyAuth'] = appKey
    self.configuration.server_variables['site'] ='us3.datadoghq.com'
    self.serviceName = serviceName
    self.environment = environment

  def emit(self, record):
    try:
      msg = self.format(record)
      with ApiClient(self.configuration) as api_client:
        apiInstance = logs_api.LogsApi(api_client)
        body = HTTPLog(
          [
            HTTPLogItem(
              ddsource='python',
              ddtags=f"env:{self.environment}",
              message=msg,
              service=self.serviceName,
              status=record.levelname.lower(),
            ),
          ]
        )
        apiInstance.submit_log(body)
    except Exception as e:
      print(f"Error sending log to Datadog: {str(e)}")

class DatadogLogger:
  def __init__(self, serviceName='optisigns', environment='production'):
    self.apiKey = DD_API_KEY
    self.appKey = DD_APP_KEY

    self.serviceName = serviceName
    self.environment = environment

    if not self.apiKey or not self.appKey:
      raise ValueError("DD_API_KEY and DD_APP_KEY environment variables must be set")

    # Configure the logger
    self.logger = logging.getLogger(serviceName)
    self.logger.setLevel(logging.INFO)

    # Create formatters
    formatter = logging.Formatter(
      '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(formatter)
    self.logger.addHandler(consoleHandler)

    ddHandler = DatadogHandler(
      apiKey=self.apiKey,
      appKey=self.appKey,
      serviceName=self.serviceName,
      environment=self.environment
    )
    ddHandler.setFormatter(formatter)
    self.logger.addHandler(ddHandler)

  def info(self, message):
    self.logger.info(message)

  def error(self, message, exc_info=True):
    self.logger.error(message, exc_info=exc_info)

  def debug(self, message):
    self.logger.debug(message)

  def warning(self, message):
    self.logger.warning(message)

defaultLogger = None

def initLogger(serviceName='optisigns', environment='production'):
  global defaultLogger
  defaultLogger = DatadogLogger(serviceName, environment)
  return defaultLogger
 