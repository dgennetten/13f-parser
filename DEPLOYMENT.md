# 13F Parser Deployment Guide

This guide will walk you through setting up and deploying the 13F Parser to automatically monitor SEC filings.

## Prerequisites

- A GitHub account
- Python 3.11+ installed locally (for testing)
- Basic knowledge of Git and GitHub

## Step 1: Repository Setup

### 1.1 Create a new GitHub repository
1. Go to [GitHub](https://github.com) and click "New repository"
2. Name it `13F-parser` (or your preferred name)
3. Make it public or private (your choice)
4. Don't initialize with README (we already have one)

### 1.2 Clone the repository locally
```bash
git clone https://github.com/YOUR_USERNAME/13F-parser.git
cd 13F-parser
```

### 1.3 Copy all the files from this project
Make sure you have all the files in your local repository:
- `src/` directory with all Python modules
- `.github/workflows/13f-parser.yml`
- `config/settings.yaml`
- `requirements.txt`
- `README.md`
- `test_parser.py`

## Step 2: Local Testing

### 2.1 Install dependencies
```bash
pip install -r requirements.txt
```

### 2.2 Test the parser locally
```bash
python test_parser.py
```

This should run without errors and show that the parser is working correctly.

### 2.3 Test the main parser
```bash
python src/main.py
```

This will attempt to search for filings (may not find any initially, which is normal).

## Step 3: GitHub Configuration

### 3.1 Push to GitHub
```bash
git add .
git commit -m "Initial commit: 13F Parser setup"
git push origin main
```

### 3.2 Enable GitHub Actions
1. Go to your repository on GitHub
2. Click on the "Actions" tab
3. You should see the "13F Parser Daily Run" workflow
4. Click on it and click "Enable workflow"

### 3.3 Configure repository secrets (optional)
If you want to customize notifications, you can set these secrets:

1. Go to Settings → Secrets and variables → Actions
2. Add the following secrets if needed:
   - `SLACK_WEBHOOK_URL`: Your Slack webhook URL for notifications
   - `EMAIL_SMTP_PASSWORD`: SMTP password for email notifications

## Step 4: Customization

### 4.1 Update target funds
Edit `config/settings.yaml` to add or modify the funds you want to monitor:

```yaml
target_funds:
  - name: "Situational Awareness LP"
    manager: "Leopold Aschenbrenner"
    aliases:
      - "Situational Awareness"
      - "Leopold Aschenbrenner"
  
  # Add more funds here
  - name: "Another Fund Name"
    manager: "Manager Name"
    aliases:
      - "Alternative Name"
```

### 4.2 Modify notification settings
In the same file, customize your notification preferences:

```yaml
notifications:
  email_enabled: false  # Set to true if you want email notifications
  email_recipients: ["your-email@example.com"]
  github_issue_enabled: true  # Creates GitHub issues for new filings
  slack_webhook: ""  # Add your Slack webhook URL here
```

### 4.3 Adjust parsing settings
```yaml
parsing:
  min_position_value: 10000  # Minimum position value to track
  include_zero_positions: false
  track_position_changes: true
```

## Step 5: Monitoring and Maintenance

### 5.1 Check GitHub Actions
- Go to the Actions tab in your repository
- You'll see the workflow running daily at 9 AM EST
- Click on any run to see detailed logs

### 5.2 View parsed data
- Check the `data/` directory in your repository
- New filings will be automatically committed
- Each filing creates a JSON file with parsed data

### 5.3 Monitor notifications
- GitHub issues will be created for new filings
- Check your email/Slack if configured
- Review daily summary issues

## Step 6: Troubleshooting

### Common Issues

#### 1. Workflow not running
- Check if GitHub Actions are enabled
- Verify the cron schedule in the workflow file
- Check repository permissions

#### 2. Parser errors
- Review the Actions logs for error details
- Check if all dependencies are installed
- Verify SEC EDGAR is accessible

#### 3. No filings found
- This is normal initially
- 13F filings are quarterly, not daily
- Check if the fund names are correct

#### 4. Rate limiting
- SEC EDGAR has rate limits
- The parser includes delays between requests
- If issues persist, increase the delay in config

### Debug Mode
To run the parser in debug mode locally:

```bash
export PYTHONPATH=src
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from main import ThirteenFParser
parser = ThirteenFParser()
parser.run()
"
```

## Step 7: Advanced Features

### 7.1 Add more funds
Simply add them to the `target_funds` section in `config/settings.yaml`.

### 7.2 Custom notification channels
The notification system is extensible. You can add:
- Discord webhooks
- Microsoft Teams notifications
- Custom API endpoints

### 7.3 Data export
The parser can export data in various formats:
```python
from src.data_manager import DataManager
dm = DataManager(config['data'])
dm.export_data('json', 'my_export.json')
```

### 7.4 Historical analysis
Use the data manager to analyze historical holdings:
```python
history = dm.get_fund_holdings_history("Fund Name")
for filing in history:
    print(f"Date: {filing['filing_date']}, Holdings: {len(filing['holdings'])}")
```

## Step 8: Security Considerations

### 8.1 Repository permissions
- The workflow runs with `GITHUB_TOKEN` permissions
- Only push to main branch if you trust the code
- Review Actions logs regularly

### 8.2 SEC EDGAR compliance
- Respect rate limits (already built-in)
- Use appropriate User-Agent headers
- Don't overwhelm their servers

### 8.3 Data privacy
- Parsed data is stored in your repository
- Consider if this meets your privacy requirements
- You can make the repository private

## Next Steps

1. **Monitor the first few runs** to ensure everything works
2. **Customize the configuration** for your specific needs
3. **Add more funds** if you want to track multiple managers
4. **Set up additional notifications** (Slack, email, etc.)
5. **Analyze the data** to gain insights into fund movements

## Support

If you encounter issues:
1. Check the GitHub Actions logs first
2. Review the error messages in the logs
3. Test locally with `python test_parser.py`
4. Check the SEC EDGAR website manually
5. Open an issue in your repository

The parser is designed to be robust and self-healing, but monitoring the first few runs will help ensure everything is working correctly.
