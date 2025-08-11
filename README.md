# Social Media Monitoring Tool

A web scraping tool to monitor mentions of Marc Benioff, Agentforce, and Sierra.AI on LinkedIn and Glassdoor.

## Overview

This tool automatically scrapes and monitors social media platforms to track:
- What people are saying about Marc Benioff (especially regarding Agentforce launch)
- Discussions about Salesforce's Agentforce product
- Mentions of Sierra.AI and its founder Bret Taylor (former Salesforce co-CEO)

## Key Features

- **Automated Scraping**: Scheduled scraping of LinkedIn posts, ads, and Glassdoor reviews
- **Real-time Monitoring**: Track mentions of key terms across platforms
- **Web Dashboard**: Beautiful, modern UI to view and analyze collected data
- **Data Storage**: SQLite database for efficient data management
- **Smart Filtering**: Focus on relevant content using keyword matching
- **Export Capabilities**: Export data for further analysis

## Keywords Monitored

- Salesforce
- Agentforce
- AI
- Marc Benioff
- CRM agents
- Sierra.AI
- Bret Taylor

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Paleonas/rpotential.git
cd rpotential
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install Playwright browsers:
```bash
playwright install chromium
```

5. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your credentials
```

## Usage

1. Start the web dashboard:
```bash
python app.py
```

2. Run the scraper manually:
```bash
python scraper/run_scraper.py
```

3. Access the dashboard at http://localhost:5000

## Project Structure

```
rpotential/
├── app.py                 # Flask web application
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── scraper/
│   ├── __init__.py
│   ├── base_scraper.py   # Base scraper class
│   ├── linkedin_scraper.py
│   ├── glassdoor_scraper.py
│   └── run_scraper.py    # Main scraper runner
├── models/
│   ├── __init__.py
│   └── database.py       # Database models
├── static/
│   ├── css/
│   └── js/
├── templates/
│   └── index.html        # Dashboard template
└── data/
    └── monitoring.db     # SQLite database
```

## Configuration

Edit `.env` file to configure:
- Scraping intervals
- Proxy settings (if needed)
- API keys (if using any APIs)
- Database settings

## Important Notes

- This tool respects robots.txt and rate limits
- LinkedIn and Glassdoor may require authentication for full access
- Use responsibly and in accordance with platform terms of service
- Consider using proxies for production use

## License

MIT License
