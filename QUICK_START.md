# 🚀 13F Parser - Quick Start Guide

Get your 13F filing parser up and running in minutes!

## What This Does

Automatically monitors SEC EDGAR for new 13F filings from **Situational Awareness LP** (Leopold Aschenbrenner) and creates GitHub issues with parsed portfolio data.

## ⚡ Quick Setup (5 minutes)

### 1. Push to GitHub
```bash
git add .
git commit -m "Initial 13F Parser setup"
git push origin main
```

### 2. Enable GitHub Actions
- Go to your repo → Actions tab
- Click "13F Parser Daily Run" → "Enable workflow"

### 3. Done! 🎉

The parser will now run automatically every day at **9 AM EST** and check for new filings.

## 📊 What You'll Get

- **Daily automated checks** for new 13F filings
- **GitHub issues** created for each new filing
- **Parsed portfolio data** showing holdings, values, and changes
- **Historical tracking** of all filings over time

## 🔍 How It Works

1. **Daily Schedule**: Runs automatically every day at 9 AM EST
2. **SEC Search**: Searches SEC EDGAR for new filings from target funds
3. **Data Parsing**: Downloads and parses XML filings into structured data
4. **Notifications**: Creates GitHub issues with portfolio summaries
5. **Data Storage**: Saves all parsed data to your repository

## 🎯 Target Fund

- **Fund**: Situational Awareness LP
- **Manager**: Leopold Aschenbrenner
- **Filing Types**: 13F-HR (initial) and 13F-HR/A (amendments)

## 📁 Key Files

- `.github/workflows/13f-parser.yml` - GitHub Actions workflow
- `config/settings.yaml` - Configuration and target funds
- `src/main.py` - Main parser logic
- `test_parser.py` - Local testing script

## 🧪 Test Locally

```bash
pip install -r requirements.txt
python test_parser.py
```

## 📈 Monitor Progress

- **Actions Tab**: See workflow runs and logs
- **Issues Tab**: View new filing notifications
- **Data Directory**: Access parsed filing data
- **Commits**: Automatic updates when new filings are found

## 🚨 First Run

The first few runs may not find filings (this is normal):
- 13F filings are quarterly, not daily
- The parser searches the last 30 days
- New filings will be detected when they appear

## 🔧 Customization

Edit `config/settings.yaml` to:
- Add more funds to monitor
- Change notification settings
- Adjust parsing parameters
- Modify search frequency

## 📞 Need Help?

1. Check the Actions logs for errors
2. Run `python test_parser.py` locally
3. Review the full [Deployment Guide](DEPLOYMENT.md)
4. Check the [README](README.md) for detailed information

---

**Next**: The parser will run automatically tomorrow at 9 AM EST. Check the Actions tab to see it in action! 🎯
