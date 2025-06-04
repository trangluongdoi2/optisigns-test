# OptiSigns Support Bot

A Python-based application that automatically scrapes OptiSigns support articles and creates an AI-powered knowledge base using OpenAI embeddings.

## Features

- Automated article scraping from Zendesk Help Center
- Markdown conversion and formatting
- OpenAI vector store integration for semantic search
- Scheduled daily updates via cron job
- Datadog logging integration
- Flask web server with health checks

## Prerequisites

- Python 3.11 or higher
- pip (Python package installer)
- A Zendesk account with API access
- OpenAI API key
- Datadog account (for logging)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd otpsigns-projects
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

# Datadog Configuration
DD_API_KEY=your_datadog_api_key
DD_APP_KEY=your_datadog_app_key

# Output Directory
outputDir=./articles
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
- `GET /scheduler`: View scheduler status (if enabled)

### Directory Structure

```
.
├── articles/          # Scraped articles in Markdown format
├── config.py         # Global configuration and environment setup
├── main.py          # Main application entry point
├── myLogger.py      # Datadog logging configuration
├── scraper.py       # Article scraping functionality
├── uploaderOpenAI.py # OpenAI vector store integration
└── requirements.txt  # Python dependencies
```

## Monitoring and Logs

The application uses Datadog for logging and monitoring. You can view:
- Application logs in your Datadog dashboard
- Scraping job execution status
- Error reports and warnings

## Development

### Running Tests
```bash
# To be implemented
```

### Code Style
The project follows a 2-space indentation style. To format your code:
```bash
# Add your preferred formatter command here
```

## Troubleshooting

1. **Environment Variables**
   - Ensure all required variables are set in `.env`
   - Check for proper API key permissions

2. **Common Issues**
   - If scraping fails, verify Zendesk API access
   - For OpenAI errors, check API key and rate limits
   - For logging issues, verify Datadog credentials

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[Add your license information here] 