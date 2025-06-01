# Quotex Partner Snapshot Generator Bot

A Telegram bot that generates customized snapshots of Quotex Partner Panel trading accounts with HTML formatting.

## Features

- Generate trading account snapshots with customizable parameters
- Set multiple parameters in a single message using the custom command
- Generate snapshots by sending an 8-digit trader ID
- Customize all trader statistics including balance, deposits, withdrawals, etc.
- Set country, date, and other parameters
- Reset all parameters to default or zero values

## Setup Instructions

### Prerequisites

- Python 3.7+
- python-telegram-bot library

### Installation

1. Clone or download this repository
2. Install required dependencies:
   ```
   pip install python-telegram-bot
   ```
3. Set your Telegram Bot Token as an environment variable:
   - Windows: `set TELEGRAM_BOT_TOKEN=your_token_here`
   - Linux/Mac: `export TELEGRAM_BOT_TOKEN=your_token_here`

### Getting a Telegram Bot Token

1. Open Telegram and search for @BotFather
2. Start a chat with BotFather and send the command `/newbot`
3. Follow the instructions to create a new bot
4. BotFather will provide you with a token - save this for use with the application

## Usage

1. Start the bot:
   ```
   python quotex_bot.py
   ```

2. Open Telegram and search for your bot by the username you created
3. Start a chat with the bot and use the following commands:

### Commands

- `/start` - Start the bot and see available commands
- `/help` - Show help information
- `/generate [count]` - Generate snapshots (default: 1)
- `/reset` - Reset all parameters to default values
- `/zeros` - Set all parameters to zero
- `/custom` - Set multiple parameters in one message
### Examples

- `/generate 5` - Generate 5 random snapshots
- `/setdate 01.05.2025` - Set registration date
- `/setbalance 5000` - Set balance to $5000
- `/setcon Pakistan` - Set country to Pakistan

### Custom Command Format

You can combine multiple parameters in one message:

```
/custom /setdate 01.05.2025 /setpercent 5 /setbalance 5000 /setdepositscount 1 /setdepositssum 30 /setturnoverclear 200 /setplall 4000 /setrevshare 10 /setlinkid 123456 /setcon Pakistan
```

After setting parameters, send an 8-digit trader ID to generate a snapshot:

```
74125896
```

## Running on a VPS (24/7)

### Linux VPS

1. Upload the code to your VPS using Git or SFTP
2. Install screen or tmux: `sudo apt-get install screen`
3. Create a new screen session: `screen -S quotex_bot`
4. Navigate to the bot directory: `cd /path/to/quotex_bot`
5. Run the bot: `python quotex_bot.py`
6. Detach from the screen session: Press `Ctrl+A` then `D`

To reconnect to the session later: `screen -r quotex_bot`

### Windows VPS

1. Upload the code to your Windows VPS
2. Create a batch file to run the bot (already included as `run_bot.bat`)
3. Set up a scheduled task to run the batch file on startup:
   - Open Task Scheduler
   - Create a new task
   - Set trigger to "At startup"
   - Set action to start the batch file
   - Configure to run with highest privileges

## Note

This bot is for demonstration purposes only. The generated data is not connected to any real trading accounts.
