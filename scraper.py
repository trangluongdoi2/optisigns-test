import os
import re
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import frontmatter
from openai import OpenAI
from openai.types import VectorStore
from bs4 import BeautifulSoup, NavigableString
from slugify import slugify
from tqdm import tqdm
from zenpy import Zenpy
import html2text
from loggerDatadog import initLogger
from loggerService import getLogger
from config import COUNT_ARTICLES, ZENDESK_EMAIL, ZENDESK_TOKEN, ZENDESK_SUBDOMAIN, OUTPUT_DIR

class ArticleScraper:
  def __init__(self):
    self.zendeskClient = Zenpy(
      email=ZENDESK_EMAIL,
      token=ZENDESK_TOKEN,
      subdomain=ZENDESK_SUBDOMAIN
    )
    self.skippedFiles = []
    self.modifededFiles = []
    self.addedFiles = []
    self.outputDir = Path(OUTPUT_DIR)
    self.outputDir.mkdir(exist_ok=True)
    self.htmlConverter = html2text.HTML2Text()
    self.htmlConverter.bodyWidth = 0
    self.setupHtmlConverter()
    # self.logger = initLogger('optisigns', 'development')
    self.logger = getLogger('optisigns', 'development')
    self.logger.info("Init articles...")
    self.urlReferences = {}

  def setupHtmlConverter(self):
    """Configure HTML to Markdown converter settings"""
    self.htmlConverter.unicode_snob = True
    self.htmlConverter.ignore_links = False
    self.htmlConverter.ignore_images = False
    self.htmlConverter.ignore_emphasis = False
    self.htmlConverter.ignore_tables = False
    self.htmlConverter.wrap_links = False  # Keep URLs inline
    self.htmlConverter.inline_links = False  # Use reference-style links
    
  def getArticleHash(self, content: str) -> str:
    """Generate hash for article content"""
    return hashlib.md5(content.encode()).hexdigest()

  def structureContent(self, markdown: str, title: str) -> str:
    """Structure the content in a standard format for AI readability"""
    sections = [f"# {title}\n"]
    
    # Add overview section
    sections.append("## Overview\n")
    
    # Extract and organize content sections
    content_parts = re.split(r'^#{2,3}\s+(.+)$', markdown, flags=re.MULTILINE)
    if len(content_parts) > 1:
      for i in range(1, len(content_parts), 2):
        header = content_parts[i]
        content = content_parts[i+1].strip() if i+1 < len(content_parts) else ""
        sections.append(f"## {header}\n\n{content}\n")
    
    return "\n".join(sections)

  def cleanHtml(self, html: str) -> str:
    """Clean and normalize HTML before conversion"""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Remove unwanted elements
    for element in soup.find_all(['script', 'style', 'iframe', 'noscript']):
      element.decompose()
    
    # Clean up whitespace
    for element in soup.find_all(text=True):
      if isinstance(element, NavigableString):
        element.replace_with(element.strip())
    
    return str(soup)
  
  def formatMarkdown(self, markdown: str) -> str:
    """Format and clean markdown content"""
    # Remove multiple consecutive blank lines
    markdown = re.sub(r'\n\s*\n\s*\n+', '\n\n', markdown)
    
    # Ensure proper spacing around headers
    markdown = re.sub(r'(#{1,6}.*?)\n*([^#\n])', r'\1\n\n\2', markdown)
    
    # Fix list formatting
    markdown = re.sub(r'(\n[*-].*?)\n*([^*\n-])', r'\1\n\n\2', markdown)
    
    return markdown.strip()
  
  def extractUrls(self, html: str) -> Dict[str, str]:
    """Extract URLs and their text from HTML content"""
    soup = BeautifulSoup(html, 'html.parser')
    urls = {}
    
    # Extract links
    for i, link in enumerate(soup.find_all('a', href=True)):
      ref_id = f"link{i+1}"
      urls[ref_id] = {
        'url': link['href'],
        'text': link.get_text(strip=True),
        'title': link.get('title', '')
      }
    
    # Extract images
    for i, img in enumerate(soup.find_all('img', src=True)):
      ref_id = f"img{i+1}"
      urls[ref_id] = {
        'url': img['src'],
        'text': img.get('alt', 'Image'),
        'title': img.get('title', '')
      }
    
    return urls

  def formatUrlReferences(self, urls: Dict[str, Dict]) -> str:
    """Format URL references section"""
    if not urls:
      return ""
    
    references = ["## URL References\n"]
    references.append("| Reference ID | Type | Description | URL |")
    references.append("|-------------|------|-------------|-----|")
    
    for ref_id, info in urls.items():
      url_type = "Image" if ref_id.startswith("img") else "Link"
      description = info['text']
      if info['title']:
        description += f" ({info['title']})"
      references.append(f"| {ref_id} | {url_type} | {description} | {info['url']} |")
    
    return "\n".join(references)

  def convertToMarkdown(self, htmlContent: str, title: str = "", article_url: str = "") -> str:
    """Convert HTML to properly formatted markdown with URL references"""
    # Extract URLs before cleaning HTML
    self.urlReferences = self.extractUrls(htmlContent)
    
    # Clean HTML
    cleanedHtml = self.cleanHtml(htmlContent)
    
    # Convert to markdown
    markdown = self.htmlConverter.handle(cleanedHtml)
    
    # Format markdown
    formattedMarkdown = self.formatMarkdown(markdown)
    
    # Structure content with metadata
    sections = [
      f"# {title}\n",
      "## Article Metadata",
      # f"- Original Article: {article_url}",
      f"- Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
      "\n## Content\n",
      formattedMarkdown,
      "\n" + self.formatUrlReferences(self.urlReferences)
    ]
    
    return "\n".join(sections)

  def getAllFiles(self, directoryPath: str):
    directory = Path(directoryPath)
    if not directory.exists():
      print(f"Directory {directoryPath} does not exist")
      return []
    
    return [f for f in directory.glob('**/*') if f.is_file()]

  def pathToDict(self, file_path: Path) -> Dict:
    try:
      post = frontmatter.load(file_path)
      metadata = post.metadata
      content = post.content
      return {
        'title': metadata.get('title', ''),
        'id': metadata.get('id', ''),
        'url': metadata.get('url', ''),
        'createdAt': metadata.get('createdAt', ''),
        'updatedAt': metadata.get('updatedAt', ''),
        'hash': metadata.get('hash') or self.getArticleHash(content),
        'body': content
      }
    except Exception as e:
      print(f"Error reading file {file_path}: {e}")
      return {}

  def getFileBySlug(self, directoryPath = '', slug = ''):
    directory = Path(directoryPath)
    files = self.getAllFiles(directoryPath)
    return [x for x in files if x.name.split('.')[0] == slug]

  def checkModifiedFile(self, newData: Dict, oldFile):
    # Need refactor
    if newData.get('updated_at') != oldFile.get('updatedAt'):
      return True
    return False

  def formatAndSaveArticle(self, filePath: str, articleData: Dict):
    frontmatter = {
      'title': articleData['title'],
      'id': articleData['id'],
      # 'url': articleData['url'],
      'createdAt': articleData['created_at'],
      'updatedAt': articleData['updated_at'],
      'hash': self.getArticleHash(articleData['body'])
    }
    
    formatted_content = self.convertToMarkdown(
      articleData['body'],
      articleData['title'],
      articleData['url']
    )
    
    content = f"""---
{json.dumps(frontmatter, indent=2)}
---

{formatted_content}
"""
    filePath.write_text(content)

  def saveArticles(self, articleData: list[Dict]):
    filePaths = []
    for article in articleData:
      filePaths.append(self.saveArticle(article.to_dict()))
    return filePaths

  def saveArticle(self, articleData: Dict) -> Path:
    slug = slugify(articleData['title'])
    filePath = self.outputDir / f"{slug}.md"
    checkedFile = self.getFileBySlug('./articles', slug)
    if len(checkedFile) > 0:
      existedFile = self.pathToDict(checkedFile[0])
      if self.checkModifiedFile(articleData, existedFile):
        self.modifededFiles.append(filePath)
        self.formatAndSaveArticle(filePath, articleData)
        return filePath
      else:
        self.skippedFiles.append(filePath)
        return filePath
    else:
      self.formatAndSaveArticle(filePath, articleData)
      self.addedFiles.append(filePath)
    return filePath

  def scrapeArticles(self) -> List[Path]:
    articles = self.zendeskClient.help_center.articles()[0: COUNT_ARTICLES]
    self.saveArticles(articles)

    self.logger.info(f"added: {len(self.addedFiles)}")
    self.logger.info(f"updated: {len(self.modifededFiles)}")
    self.logger.info(f"skipped: {len(self.skippedFiles)}")

    self.logger.debug(f"added: {len(self.addedFiles)}")
    self.logger.debug(f"updated: {len(self.modifededFiles)}")
    self.logger.debug(f"skipped: {len(self.skippedFiles)}")

    return self.addedFiles + self.modifededFiles