# Telegram Accounting Bot

A Telegram bot for tracking expenses and generating financial reports.

## Deployment to Vercel

### Prerequisites
- A Vercel account
- A Telegram Bot Token (from @BotFather)
- Google Sheets API credentials

### Steps to Deploy

1. **Fork or clone this repository**

2. **Install Vercel CLI (optional)**
   ```
   npm i -g vercel
   ```

3. **Set up environment variables**

   In Vercel, add the following environment variables:
   - `BOT_TOKEN`: Your Telegram bot token
   - `SPREADSHEET_ID`: Your Google Spreadsheet ID
   - `GOOGLE_SHEET_NAME`: Name of the sheet to use (default: "Expenses")
   - `GOOGLE_APPLICATION_CREDENTIALS`: Paste the entire contents of your google-credentials.json file

4. **Deploy to Vercel**
   
   Option 1: Using Vercel CLI
   ```
   vercel
   ```
   
   Option 2: Using Vercel Dashboard
   - Import your GitHub repository
   - Configure build settings as per the vercel.json file
   - Deploy

5. **Set webhook for your Telegram bot**
   
   After deployment, your bot will automatically set up the webhook.

6. **Test your bot**
   
   Send a message to your bot: "I spent $20 on coffee"

## Local Development

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Create a `.env` file with the required environment variables
4. Run the bot: `python main.py`
