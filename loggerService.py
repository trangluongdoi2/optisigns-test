import logging
from logging.handlers import RotatingFileHandler 
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

class LoggerService:
  _instance = None
  
  def __init__(self, name: str = 'optisigns', env: str = 'development'):
    self.logger = logging.getLogger(name)
    self.logger.setLevel(logging.INFO)
    self.logger.handlers = []
    self.loggerName = name
    self.env = env
    formatter = logging.Formatter(
      '%(asctime)s - %(name)s - %(levelname)s: %(message)s'
    )

    if 'gunicorn' in sys.modules:
      gunicornLogger = logging.getLogger('gunicorn.error')
      self.logger.handlers = gunicornLogger.handlers
      self.logger.setLevel(gunicornLogger.level)
      for handler in self.logger.handlers:
        handler.setFormatter(formatter)
    else:
      consoleHandler = logging.StreamHandler(sys.stdout)
      consoleHandler.setFormatter(formatter)
      consoleHandler.setLevel(logging.DEBUG)
      self.logger.addHandler(consoleHandler)

    self.logger.propagate = False
    # self.initFileLogger()

  def initFileLogger(self):
    file_formatter = logging.Formatter(
      '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    current_date = datetime.now().strftime('%Y-%m-%d')
    logDir = Path('logs') / current_date
    logDir.mkdir(parents=True, exist_ok=True)
    logFile = logDir / f'{self.loggerName}-{self.env}.log'
    
    # File handler with rotation
    fileHandler = RotatingFileHandler(
      filename=logFile,
      maxBytes=10 * 1024 * 1024,  # 10MB
      backupCount=5,
      encoding='utf-8'
    )
    fileHandler.setFormatter(file_formatter)
    fileHandler.setLevel(logging.INFO)
    self.logger.addHandler(fileHandler)

  @classmethod
  def getInstance(cls, name: str = 'optisigns', env: str = 'development') -> logging.Logger:
    if cls._instance is None:
      cls._instance = cls(name, env)
    return cls._instance.logger
  
  def getLogger(self) -> logging.Logger:
    return self.logger

def getLogger(name: str = 'optisigns', env: str = 'development') -> logging.Logger:
  return LoggerService.getInstance(name, env)