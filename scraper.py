import os
import re
import hashlib
import json
from pathlib import Path
from typing import Dict, List
import frontmatter
from bs4 import BeautifulSoup, NavigableString
from slugify import slugify
from zenpy import Zenpy
import html2text
from loggerService import getLogger
from config import COUNT_ARTICLES, ZENDESK_EMAIL, ZENDESK_TOKEN, ZENDESK_SUBDOMAIN, OUTPUT_DIR

class ArticleScraper:
  def __init__(self):
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
    return htmlConverter
    
  def getArticleHash(self, content: str) -> str:
    """Generate hash for article content"""
    return hashlib.md5(content.encode()).hexdigest()

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
  
  def extractUrls(self, html: str) -> Dict[str, str]:
    """Extract URLs and their text from HTML content"""
    soup = BeautifulSoup(html, 'html.parser')
    urls = {}
    
    # Extract links
    for i, link in enumerate(soup.find_all('a', href=True)):
      urls[f"link{i+1}"] = {
        'url': link['href'],
        'text': link.get_text(strip=True),
        'title': link.get('title', '').strip().upper()
      }
    
    # Extract images
    # for i, img in enumerate(soup.find_all('img', src=True)):
    #   urls[f"img{i+1}"] = {
    #     'url': img['src'],
    #     'text': img.get('alt', 'Image'),
    #     'title': img.get('title', '').strip().upper()
    #   }
    return urls

  def convertToMarkdown(self, htmlContent: str, title: str = "", articleUrl: str = "") -> str:
    """Convert HTML to properly formatted markdown with URL references"""
    self.urlReferences = self.extractUrls(htmlContent)

    # Clean HTML
    cleanedHtml = self.cleanHtml(htmlContent)

    # Convert to markdown
    markdown = self.htmlConverter.handle(cleanedHtml)

    # Handle all types of markdown links
    def replaceAllLinks(match):
      url = match.group(2).replace('\n', '').replace(' ', '')

      for index, item in enumerate(self.urlReferences.values()):
        if (item['url'] == url):
          formatedUrl = [
            f"\n## {title} - {item['text']} ",
            f"Article URL {index}: {url} ",
          ]
          return '\n'.join(formatedUrl)

      return match.group(0)

    # Handle inline links [text](url)
    markdown = re.sub(r'\[([^\]]+)\]\(\s*([^)]+?)\s*\)', replaceAllLinks, markdown)

    # Handle reference links [text][ref]
    markdown = re.sub(r'\[([^\]]+)\]\[\s*([^\]]+?)\s*\]', replaceAllLinks, markdown)

    # Structure content with metadata
    sections = [
      f"## {title}",
      f"LINK: {articleUrl}",
      "## Content",
      markdown,
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
    files = self.getAllFiles(directoryPath)
    return [x for x in files if x.name.split('.')[0] == slug]

  def checkModifiedFile(self, newData: Dict, oldFile):
    if newData.get('updated_at') != oldFile.get('updatedAt'):
      return True
    return False

  def formatAndSaveArticle(self, filePath: str, articleData: Dict):
    frontmatter = {
      'title': articleData['title'],
      'id': articleData['id'],
      'url': articleData['html_url'],
      "article_url": articleData['html_url'],
      'createdAt': articleData['created_at'],
      'updatedAt': articleData['updated_at'],
      'hash': self.getArticleHash(articleData['body'])
    }
    
    formattedContent = self.convertToMarkdown(
      articleData['body'],
      articleData['title'],
      articleData['html_url']
    )
    
    content = f"""---
{json.dumps(frontmatter, indent=2)}
---

{formattedContent}
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