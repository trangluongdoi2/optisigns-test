import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

class LoggerService:
  _instance = None
  
  def __init__(self, name: str = 'optisigns', env: str = 'development'):
    self.logger = logging.getLogger(name)
    self.logger.setLevel(logging.DEBUG)

    consoleFormatter = logging.Formatter(
      '%(asctime)s - %(name)s - %(levelname)s: %(message)s'
    )
    
    consoleHandler = logging.StreamHandler(sys.stdout)
    consoleHandler.setFormatter(consoleFormatter)
    consoleHandler.setLevel(logging.INFO)
    
    # Add handlers
    self.logger.addHandler(consoleHandler)
    
  @classmethod
  def getInstance(cls, name: str = 'optisigns', env: str = 'development') -> logging.Logger:
    if cls._instance is None:
      cls._instance = cls(name, env)
    return cls._instance.logger
  
  def getLogger(self) -> logging.Logger:
    return self.logger

  # Convenience function to get logger
def getLogger(name: str = 'optisigns', env: str = 'development') -> logging.Logger:
  return LoggerService.getInstance(name, env)