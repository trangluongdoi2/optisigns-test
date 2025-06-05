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
    # self.logger = initLogger('optisigns', 'development')
    self.logger = getLogger('optisigns', 'development')

    self.zendeskClient = self.initZendeskClient()

    self.files = {
      'skipped': [],
      'modified': [],
      'added': []
    }
        
    self.outputDir = self.setupOutputDirectory()

    self.htmlConverter = self.setupHtmlConverter()

    self.urlReferences = {}

  def initZendeskClient(self) -> Zenpy:
    return Zenpy(
      email=ZENDESK_EMAIL,
      token=ZENDESK_TOKEN,
      subdomain=ZENDESK_SUBDOMAIN
    )
  
  def setupOutputDirectory(self) -> Path:
    outputDir = Path(OUTPUT_DIR)
    outputDir.mkdir(exist_ok=True)
    return outputDir

  def setupHtmlConverter(self) -> html2text.HTML2Text:
    htmlConverter = html2text.HTML2Text()
    htmlConverter.bodyWidth = 0
    htmlConverter.unicode_snob = True
    htmlConverter.ignore_links = False
    htmlConverter.ignore_images = False
    htmlConverter.ignore_emphasis = False
    htmlConverter.ignore_tables = False
    htmlConverter.wrap_links = False  # Keep URLs inline
    htmlConverter.inline_links = False  # Use reference-style links
    return htmlConverter
    
  def getArticleHash(self, content: str) -> str:
    """Generate hash for article content"""
    return hashlib.md5(content.encode()).hexdigest()

  def structureContent(self, markdown: str, title: str) -> str:
    """Structure the content in a standard format for AI readability"""
    sections = [f"# {title}\n"]
    
    # Add overview section
    sections.append("## Overview\n")

    # Extract and organize content sections
    contentParts = re.split(r'^#{2,3}\s+(.+)$', markdown, flags=re.MULTILINE)
    if len(contentParts) > 1:
      for i in range(1, len(contentParts), 2):
        header = contentParts[i]
        content = contentParts[i+1].strip() if i+1 < len(contentParts) else ""
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
      urls[f"link{i+1}"] = {
        'url': link['href'],
        'text': link.get_text(strip=True),
        'title': link.get('title', '')
      }
    
    # Extract images
    for i, img in enumerate(soup.find_all('img', src=True)):
      urls[f"img{i+1}"] = {
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
    
    for refId, info in urls.items():
      urlType = "Image" if refId.startswith("img") else "Link"
      description = info['text']
      if info['title']:
        description += f" ({info['title']})"
      references.append(f"| {refId} | {urlType} | {description} | {info['url']} |")
    
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

  def pathToDict(self, filePath: Path) -> Dict:
    try:
      post = frontmatter.load(filePath)
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
      print(f"Error reading file {filePath}: {e}")
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
    # Need refactor
    checkedFile = self.getFileBySlug('./articles', slug)

    if len(checkedFile) > 0:
      existedFile = self.pathToDict(checkedFile[0])
      if self.checkModifiedFile(articleData, existedFile):
        self.files['modified'].append(filePath)
        self.formatAndSaveArticle(filePath, articleData)
        return filePath
      else:
        self.files['skipped'].append(filePath)
        return filePath
    else:
      self.formatAndSaveArticle(filePath, articleData)
      self.files['added'].append(filePath)
    return filePath

  def scrapeArticles(self) -> List[Path]:
    articles = self.zendeskClient.help_center.articles()[0: COUNT_ARTICLES]
    self.saveArticles(articles)

    for status, files in self.files.items():
      self.logger.info(f"{status}: {len(files)}")

    return self.files['added'] + self.files['modified']