# 13F Filing Parser



## What is a 13F Filing?

A 13F filing is a quarterly report that institutional investment managers with assets under management of $100 million or more must file with the SEC. It discloses their equity holdings, providing transparency into what major investors are buying and selling.

## Target Fund: Situational Awareness LP

**Manager**: Leopold Aschenbrenner  
**Focus**: This parser specifically tracks filings from this fund to monitor their investment decisions and portfolio changes.

## How It Works

### GitHub Actions Automation
- **Schedule**: Runs automatically every day at 9:00 AM EST
- **Process**: 
  1. Checks SEC EDGAR for new 13F filings
  2. Identifies filings from target funds/managers
  3. Downloads and parses the XML filings
  4. Extracts portfolio holdings and changes
  5. Saves structured data to the repository
  6. Sends notifications for new filings

### Data Output
- **Portfolio Holdings**: Current positions with quantities and values
- **Changes**: New positions, increased positions, decreased positions, and exits
- **Timeline**: Historical tracking of position changes
- **Analysis**: Summary statistics and insights

## Files Structure

```
├── .github/workflows/          # GitHub Actions workflows
├── src/                        # Python source code
├── data/                       # Parsed filing data
├── config/                     # Configuration files
├── requirements.txt            # Python dependencies
└── README.md                  # This file
```

## Setup

1. **Clone this repository**
2. **Install dependencies**: `pip install -r requirements.txt`
3. **Configure settings**: Edit `config/settings.yaml`
4. **Enable GitHub Actions**: Push to trigger automatic runs

## Usage

### Manual Run
```bash
python src/main.py
```

### Automatic Run
The GitHub Action runs automatically every day. Check the Actions tab in your repository to see execution history.

## Data Sources

- **SEC EDGAR**: Official source of 13F filings
- **Filing Types**: 13F-HR (initial holdings), 13F-HR/A (amendments)
- **Update Frequency**: Quarterly (45 days after quarter end)

## Output Format

Parsed data is saved in JSON format with the following structure:
```json
{
  "filing_date": "2024-01-15",
  "fund_name": "Situational Awareness LP",
  "manager": "Leopold Aschenbrenner",
  "total_value": 1234567890,
  "holdings": [
    {
      "security_name": "APPLE INC",
      "cusip": "037833100",
      "shares": 1000000,
      "value": 123456789,
      "change": "NEW"
    }
  ]
}
```

## Contributing

Feel free to submit issues and enhancement requests!

## License

MIT License - see LICENSE file for details.
