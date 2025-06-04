import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv
from openai import OpenAI
from openai.types import VectorStore
from config import OPENAI_API_KEY

class OpenAIUploader:
  def __init__(self):
    self.client = OpenAI(api_key=OPENAI_API_KEY)
    self.MAX_FILES_PER_VERTOR_STORE = 100
    self.vectorStores: List[VectorStore] = []

  def createVectorStore(self, name="") -> VectorStore:
    newName = f"Support FAQ {name}"
    return self.client.vector_stores.create(name=newName)

  def attachToVectorFiles(self, fileIds: List[str]= []):
    if not fileIds:
      return

    chunkingStrategy = {
      "type": "auto",
    }

    fileBatches = [fileIds[i:i + self.MAX_FILES_PER_VERTOR_STORE] for i in range(0, len(fileIds), self.MAX_FILES_PER_VERTOR_STORE)]
    
    for i, batch in enumerate(fileBatches):
      vectorStore = self.createVectorStore(i+1)

      self.client.vector_stores.file_batches.create(
        vector_store_id=vectorStore.id,
        file_ids=batch,
        chunking_strategy=chunkingStrategy
      )

  def removeVectorStores(self):
    print("removeVectorStores")

  def removeFiles(self):
    files = self.client.files.list()
    for file in files:
      self.client.files.delete(file_id=file.id)

  def handleFiles(self, filePaths: list[Path]) -> list[Optional[str]]:
    response = []
    for filePath in filePaths:
      response.append(self.uploadFile(filePath))
    self.attachToVectorFiles(response)
    return response

  def uploadFile(self, filePath: Path) -> Optional[str]:
    """Upload file to OpenAI and return file ID"""
    try:
      with open(filePath, 'rb') as file:
        # Need check exist file for change modifed?
        response = self.client.files.create(
          file=file,
          purpose='assistants'
        )
        return response.id
    except Exception as e:
      print(f"Error uploading {filePath}: {e}")
      return None