# OptiSigns Support Bot

A Python-based application that automatically scrapes OptiSigns support articles and creates an AI-powered knowledge base using OpenAI embeddings.

## Features

- Automated article scraping from Zendesk Help Center.
- Markdown conversion and formatting.
- OpenAI vector store integration for semantic search.
- Scheduled daily updates via cron job.
- Opensearch Dasboard to visualize the logs from system [link here](https://db-opensearch-nyc3-78105-do-user-23016037-0.i.db.ondigitalocean.com/).
- Flask web server with health checks.

## Prerequisites

- Python 3.11 or higher, current verions is 3.11
- pip (Python package installer)
- A Zendesk account with API access
- OpenAI API key

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd optisigns-projects
```

2. Create and activate a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root with your configuration:
```env
# Flask Configuration
PORT=8080
FLASK_ENV=development

# Zendesk Configuration
ZENDESK_EMAIL=your_email
ZENDESK_TOKEN=your_token
ZENDESK_SUBDOMAIN=your_subdomain

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

# Output Directory
outputDir=./articles

# Count of Articles be scraped (default = 30)
COUNT_ARTICLES
```

## Running the Application

### Development Mode

Run the Flask application with the scheduler:
```bash
python main.py
```

The application will:
- Start a web server on http://localhost:8080
- Initialize the article scraping scheduler
- Run the scraping job at configured intervals

### Available Endpoints

- `GET /`: Home page showing application status
- `GET /health`: Health check endpoint

### Directory Structure

```
.
├── articles/          # Scraped articles in Markdown format
├── config.py         # Global configuration and environment setup
├── main.py          # Main application entry point
├── loggerService.py      # System logging configuration
├── scraper.py       # Article scraping functionality
├── uploaderOpenAI.py # OpenAI vector store integration
└── requirements.txt  # Python dependencies
```

## Running the Application with Docker

To run the application using Docker, follow these steps:

1. **Build the Docker Image**:
   ```bash
   docker build -t optisigns-support-bot .
   ```

2. **Run the Docker Container**:
   ```bash
   docker run -d -p 8080:8080 --env-file .env optisigns-support-bot
   ```

   This command will start the application in a Docker container, mapping port 8080 of the container to port 8080 on your host machine. The `--env-file` option is used to pass environment variables from the `.env` file.

## Database and Logging

The application uses OpenSearch Dashboard to visualize logs forwarded from DigitalOcean. This setup allows for comprehensive monitoring and analysis of system logs.

### OpenSearch Dashboard

- Access the OpenSearch Dashboard to view logs: [OpenSearch Dashboard](https://db-opensearch-nyc3-78105-do-user-23016037-0.i.db.ondigitalocean.com/).

## Chosen Chunk Strategy For Vector Stores: 'Auto'

The 'auto' chunk strategy offers several advantages when used in OpenAI vector stores:

1. **Dynamic Adjustment**: Automatically adjusts chunk sizes based on content and context, optimizing for performance and accuracy.
2. **Context Preservation**: Maintains semantic context within each chunk, improving the relevance and coherence of semantic search results.
3. **Flexibility**: Adapts to different types of data, making it suitable for varied datasets where the optimal chunk size might not be known in advance.
4. **Efficiency**: By optimizing chunk sizes dynamically, it can lead to more efficient processing and resource utilization.

## Troubleshooting

1. **Environment Variables**
   - Ensure all required variables are set in `.env`
   - Check for proper API key permissions

2. **Common Issues**
   - If scraping fails, verify Zendesk API access
   - For OpenAI errors, check API key and rate limits
