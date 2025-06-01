import os
import random
from datetime import datetime, timedelta
import logging
import re
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Load environment variables from .env file
load_dotenv()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Default values for snapshot parameters
default_values = {
    "trader_id": lambda: random.randint(50000000, 59999999),
    "trader_id_prefix": None,  # New parameter for trader ID prefix
    "country": "India",
    "reg_date": lambda: (datetime.today() - timedelta(days=random.randint(1, 365))).strftime('%d.%m.%Y'),
    "affiliate_percent": "5.0",
    "link_id": lambda: random.randint(100000, 999999),
    "balance": lambda: round(random.uniform(50, 1000), 2),
    "deposits_count": lambda: random.randint(1, 3),
    "deposits_sum": lambda: round(random.uniform(50, 500), 2),
    "bonuses_count": lambda: random.randint(0, 1),
    "bonuses_sum": lambda: round(random.uniform(0, 50), 2),
    "withdrawals_count": lambda: random.randint(0, 1),
    "withdrawals_sum": lambda: round(random.uniform(0, 100), 2),
    "pending_withdrawals_count": lambda: random.randint(0, 1),
    "pending_withdrawals_sum": lambda: round(random.uniform(0, 100), 2),
    "turnover_all": lambda: round(random.uniform(0, 200), 2),
    "turnover_clear": lambda: round(random.uniform(100, 1000), 2),
    "pl_all": lambda: round(random.uniform(50, 1000), 2),
    "pl_clear": "-",
    "vol_share": lambda: round(random.uniform(10, 50), 2),
    "rev_share": "-"
}

# User settings dictionary to store custom values per user
user_settings = {}

# Generate snapshot with user-specific parameters
def generate_snapshot(user_id):
    # Get user settings or create default
    if user_id not in user_settings:
        user_settings[user_id] = {}
    
    # Generate values for each field (use custom if set, otherwise default)
    values = {}
    for key, default in default_values.items():
        if key in user_settings[user_id]:
            # Check if the value is a range definition (stored as a dictionary with min/max)
            if isinstance(user_settings[user_id][key], dict) and 'type' in user_settings[user_id][key]:
                if user_settings[user_id][key]['type'] == 'range':
                    # Generate a new random value within the range for each snapshot
                    min_val = user_settings[user_id][key]['min']
                    max_val = user_settings[user_id][key]['max']
                    
                    if user_settings[user_id][key].get('is_date', False):
                        # Handle date range
                        start_date = datetime.strptime(min_val, '%d.%m.%Y')
                        end_date = datetime.strptime(max_val, '%d.%m.%Y')
                        # Make end_date inclusive by adding one day
                        end_date = end_date + timedelta(days=1)
                        # Calculate random date between start and end (inclusive)
                        delta = end_date - start_date
                        random_days = random.randint(0, delta.days - 1)
                        random_date = start_date + timedelta(days=random_days)
                        values[key] = random_date.strftime('%d.%m.%Y')
                    elif user_settings[user_id][key].get('is_int', False):
                        # Integer range
                        values[key] = random.randint(int(min_val), int(max_val))
                    else:
                        # Float range
                        values[key] = round(random.uniform(min_val, max_val), 2)
                else:
                    values[key] = user_settings[user_id][key]['value']
            else:
                values[key] = user_settings[user_id][key]
        else:
            if callable(default):
                values[key] = default()
            else:
                values[key] = default
    
    # Special handling for trader_id if trader_id_prefix is set
    if "trader_id_prefix" in user_settings[user_id] and user_settings[user_id]["trader_id_prefix"] is not None:
        # Check if we're using an incremented prefix from a multi-snapshot generation
        if "current_trader_prefix" in user_settings[user_id]:
            prefix = user_settings[user_id]["current_trader_prefix"]
        else:
            prefix = user_settings[user_id]["trader_id_prefix"]
            
        # Generate random 6 digits to complete the 8-digit trader ID
        random_suffix = random.randint(0, 999999)
        # Format: prefix (2 digits) + random suffix (padded to 6 digits)
        values["trader_id"] = f"{prefix}{random_suffix:06d}"
    
    # Calculate vol_share if not explicitly set
    if "vol_share" not in user_settings[user_id]:
        if isinstance(values["balance"], (int, float)):
            values["vol_share"] = round(float(values["balance"]) * 0.04, 2)
    
    # Format numeric values to ensure proper display
    # For monetary values, use 2 decimal places
    for key in ["balance", "deposits_sum", "bonuses_sum", "withdrawals_sum", 
                "pending_withdrawals_sum", "turnover_all", "turnover_clear", 
                "pl_all", "vol_share"]:
        if isinstance(values[key], (int, float)):
            values[key] = f"{float(values[key]):.2f}"
            
    # For integer values, remove decimal points
    for key in ["trader_id", "link_id", "deposits_count", "bonuses_count", 
                "withdrawals_count", "pending_withdrawals_count"]:
        if isinstance(values[key], (int, float)):
            values[key] = f"{int(values[key])}"
    
    # Format the snapshot with bold values using HTML formatting
    # Bold the header values
    snapshot = f"""<b>Trader # {values["trader_id"]}</b>
<b>Country: {values["country"]}</b>
<b>(Registration Date: {values["reg_date"]}</b>)
<b>Affiliate program: Turnover {values["affiliate_percent"]}%</b>
<b>Link Id: {values["link_id"]}</b>
---------------------------
Balance: $ <b>{values["balance"]}</b>
Deposits Count: <b>{values["deposits_count"]}</b>
Deposits Sum:<b> $ {values["deposits_sum"]}</b>
Bonuses Count: <b>{values["bonuses_count"]}</b>
Bonuses Sum:<b> $ {values["bonuses_sum"]}</b>
Withdrawals Count: <b>{values["withdrawals_count"]}</b>
Withdrawals Sum:<b> $ {values["withdrawals_sum"]}</b>
Pending Withdrawals Count: <b>{values["pending_withdrawals_count"]}</b>
Pending Withdrawals Sum:<b> $ {values["pending_withdrawals_sum"]}</b>
Turnover All:<b> $ {values["turnover_all"]}</b>
Turnover Clear: <b>$ {values["turnover_clear"]}</b>
P/L All:<b> $ {values["pl_all"]}</b>
P/L Clear: <b>{values["pl_clear"]}</b>
Vol Share:<b> $ {values["vol_share"]}</b>
Rev Share: <b>{values["rev_share"]}</b>
---------------------------
<a href="https://quotex-partner.com/statistics?search={values["trader_id"]}"><b>Open trader statistics page</b></a>
"""
    return snapshot

# Function to parse range input
def parse_range_input(input_str):
    if not input_str:
        return 0
        
    # Check if it's a range (contains '-')
    if '-' in input_str:
        try:
            min_val, max_val = input_str.split('-')
            min_val = float(min_val.strip())
            max_val = float(max_val.strip())
            
            # Instead of returning a random value, return a range definition
            # that will be used to generate random values for each snapshot
            result = {
                'type': 'range',
                'min': min_val,
                'max': max_val,
                'is_int': min_val.is_integer() and max_val.is_integer()
            }
            
            # Also generate an initial random value for immediate feedback
            if min_val.is_integer() and max_val.is_integer():
                result['value'] = random.randint(int(min_val), int(max_val))
            else:
                result['value'] = round(random.uniform(min_val, max_val + 0.001), 2)
                
            return result
        except ValueError:
            return 0
    else:
        try:
            # Single value
            return float(input_str.strip())
        except ValueError:
            return 0

# Function to parse custom command with multiple parameters
async def process_custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process a custom command with multiple parameters and create snapshots."""
    user_id = update.effective_user.id
    message_text = update.message.text.strip()
    
    # Check if this is a custom command format
    if not message_text.startswith('/'):
        return
    
    # Remove /custom prefix if present
    if message_text.lower().startswith('/custom'):
        message_text = message_text[7:].strip()
        if not message_text.startswith('/'):
            message_text = '/' + message_text
    
    # Normalize the message - ensure spaces between commands
    # This fixes issues like /setturnoverclear200/setplall4000
    message_text = re.sub(r'(\d+)/(set[a-z]+)', r'\1 /\2', message_text)
    
    # Extract all parameters from the message
    param_pattern = r'/([a-zA-Z]+)\s*([^/\s]+)?'  # Pattern to match /command value, value is optional
    params = re.findall(param_pattern, message_text)
    
    if not params:
        return
    
    # Initialize user settings if needed
    if user_id not in user_settings:
        user_settings[user_id] = {}
        
    # First, initialize all parameters to 0 except for special cases
    # This ensures any parameter not explicitly set will be 0
    initialize_user_settings_with_zeros(user_id)
    
    # Process each parameter
    for cmd, value in params:
        cmd = cmd.lower()
        
        # Map the command to the corresponding parameter
        param_mapping = {
            'setdate': 'reg_date',
            'setpercent': 'affiliate_percent',
            'setbalance': 'balance',
            'setdepositscount': 'deposits_count',
            'setdepositssum': 'deposits_sum',
            'setturnoverclear': 'turnover_clear',
            'setplall': 'pl_all',
            'setrevshare': 'rev_share',
            'setlinkid': 'link_id',
            'setbonusescount': 'bonuses_count',
            'setbonussum': 'bonuses_sum',
            'setwithdrawalscount': 'withdrawals_count',
            'setwithdrawalssum': 'withdrawals_sum',
            'setpendingwithdrawalscount': 'pending_withdrawals_count',
            'setpendingwithdrawalssum': 'pending_withdrawals_sum',
            'setturnoverall': 'turnover_all',
            'setplclear': 'pl_clear',
            'setvolshare': 'vol_share',
            'setcon': 'country'
        }
        
        if cmd in param_mapping:
            param = param_mapping[cmd]
            
            # If value is not provided, set to 0
            if not value:
                if param == 'reg_date':
                    user_settings[user_id][param] = datetime.today().strftime('%d.%m.%Y')
                else:
                    user_settings[user_id][param] = 0
            else:
                # Handle date format
                if param == 'reg_date':
                    if '-' in value:
                        # It's a date range
                        date_range = parse_date_range(value)
                        if date_range:
                            user_settings[user_id][param] = date_range
                    else:
                        # It's a single date
                        try:
                            # Validate date format
                            datetime.strptime(value, '%d.%m.%Y')
                            user_settings[user_id][param] = value
                        except ValueError:
                            await update.message.reply_text(f"Invalid date format for {cmd}. Use DD.MM.YYYY")
                # Handle special cases for text values
                elif param == 'country':
                    # Set country directly as a string
                    user_settings[user_id][param] = value
                # Handle numeric values
                else:
                    if '-' in value:
                        # It's a range
                        range_values = parse_range_input(value)
                        if range_values:
                            user_settings[user_id][param] = range_values
                    else:
                        # It's a single value
                        try:
                            if param in ['affiliate_percent', 'balance', 'deposits_sum', 'turnover_clear', 'pl_all', 'rev_share']:
                                user_settings[user_id][param] = float(value)
                            else:
                                user_settings[user_id][param] = int(value)
                        except ValueError:
                            await update.message.reply_text(f"Invalid value for {cmd}")
    
    # Check if there's an 8-digit trader ID in the message
    trader_id_match = re.search(r'\b\d{8}\b', message_text)
    if trader_id_match:
        trader_id = trader_id_match.group(0)
        # Set the trader ID as a string to preserve the exact format
        user_settings[user_id]['trader_id'] = trader_id
        # Generate and send a snapshot
        snapshot = generate_snapshot(user_id)
        await update.message.reply_html(snapshot)  # Use reply_html to render HTML properly
    else:
        # Confirm that parameters were set
        await update.message.reply_text("Parameters set. Send an 8-digit trader ID to generate a snapshot.")

# Function to parse date range input
def parse_date_range(input_str):
    if not input_str:
        return 0
        
    # Check if it's a range (contains '-')
    if '-' in input_str:
        try:
            # Format should be DD.MM.YYYY-DD.MM.YYYY
            start_date_str, end_date_str = input_str.split('-')
            
            # Parse start and end dates
            start_date = datetime.strptime(start_date_str.strip(), '%d.%m.%Y')
            end_date = datetime.strptime(end_date_str.strip(), '%d.%m.%Y')
            
            # Store as a range definition for generating random dates for each snapshot
            result = {
                'type': 'range',
                'min': start_date_str.strip(),
                'max': end_date_str.strip(),
                'is_date': True
            }
            
            # Calculate an initial random date for immediate feedback
            end_date_calc = end_date + timedelta(days=1)  # Make end_date inclusive
            delta = end_date_calc - start_date
            random_days = random.randint(0, delta.days - 1)
            random_date = start_date + timedelta(days=random_days)
            result['value'] = random_date.strftime('%d.%m.%Y')
            
            return result
        except ValueError as e:
            # If date parsing fails, return today's date
            logger.error(f"Date parsing error: {e}")
            return datetime.today().strftime('%d.%m.%Y')
    else:
        # Single date value
        try:
            # Validate the date format
            datetime.strptime(input_str.strip(), '%d.%m.%Y')
            return input_str.strip()
        except ValueError:
            # If date parsing fails, return today's date
            return datetime.today().strftime('%d.%m.%Y')

# Reset user settings to default
def reset_user_settings(user_id):
    if user_id in user_settings:
        del user_settings[user_id]
    return "All settings reset to default values."

# Initialize user settings with zeros
def initialize_user_settings_with_zeros(user_id):
    """Set all user settings to zero."""
    # Preserve trader ID if it exists
    trader_id = None
    if user_id in user_settings and 'trader_id' in user_settings[user_id]:
        trader_id = user_settings[user_id]['trader_id']
    
    # Reset user settings
    user_settings[user_id] = {}
    
    # Restore trader ID if it existed
    if trader_id:
        user_settings[user_id]['trader_id'] = trader_id
    
    # Set all numeric values to 0
    for key, default in default_values.items():
        if key in ['trader_id', 'trader_id_prefix'] and trader_id:
            # Skip trader ID fields if we already have a trader ID
            continue
        elif key == 'country':
            user_settings[user_id][key] = 'India'
        elif key == 'reg_date':
            user_settings[user_id][key] = datetime.today().strftime('%d.%m.%Y')
        elif key == 'pl_clear':
            user_settings[user_id][key] = '-'
        elif key == 'rev_share':
            user_settings[user_id][key] = '-'
        else:
            user_settings[user_id][key] = 0
    
    return True

# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user_id = update.effective_user.id
    
    # Reset user settings when starting
    reset_user_settings(user_id)
    
    await update.message.reply_text(
        "👋 Welcome to Quotex Partner Snapshot Generator Bot!\n\n"
        "Available Commands:\n\n"
        "/generate - Generate a snapshot with current settings\n"
        "/generate <count> - Generate multiple snapshots\n"
        "/reset - Reset all settings to default\n"
        "/zeros - Set all values to zero\n\n"
        "Customization Commands:\n"
        "/setdate <value> - Set registration date (DD.MM.YYYY or DD.MM.YYYY-DD.MM.YYYY for range)\n"
        "/setpercent <value> - Set affiliate percentage\n"
        "/setlinkid <value> - Set link ID\n"
        "/settraderid <value> - Set trader ID prefix (2-digit number)\n"
        "/setbalance <value> - Set balance (can be range like 100-500)\n"
        "/setdepositscount <value> - Set deposits count\n"
        "/setdepositssum <value> - Set deposits sum\n"
        "/setbonusescount <value> - Set bonuses count\n"
        "/setbonussum <value> - Set bonus sum\n"
        "/setwithdrawalscount <value> - Set withdrawals count\n"
        "/setwithdrawalssum <value> - Set withdrawals sum\n"
        "/setpendingwithdrawalscount <value> - Set pending withdrawals count\n"
        "/setpendingwithdrawalssum <value> - Set pending withdrawals sum\n"
        "/setturnoverall <value> - Set turnover all\n"
        "/setturnoverclear <value> - Set turnover clear\n"
        "/setplall <value> - Set P/L all\n"
        "/setplclear <value> - Set P/L clear\n"
        "/setvolshare <value> - Set vol share\n"
        "/setrevshare <value> - Set rev share\n"
        "/setcon <value> - Set country\n\n"
        "Examples:\n"
        "/setbalance 500-1000 - Set balance to random value between 500-1000\n"
        "/setdate 01.01.2025-31.12.2025 - Set date to random date in 2025\n"
        "/settraderid 51 - Set trader ID prefix to 51 (IDs will be 51XXXXXX)\n"
        "/setbalance - Set balance to 0 (empty command value defaults to 0)\n"
        "/generate 3 - Generate 3 snapshots with incrementing trader IDs"
    )

async def generate_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generate snapshots based on count."""
    try:
        user_id = update.effective_user.id
        
        # Default to 1 snapshot if no count provided
        count = 1
        if context.args:
            count = int(context.args[0])
            
        if count <= 0:
            await update.message.reply_text("Count must be a positive number.")
            return
            
        if count > 20:
            await update.message.reply_text("Maximum limit is 20 snapshots at once.")
            return
        
        # Check if trader_id_prefix is set
        trader_prefix_set = False
        current_prefix = None
        
        if user_id in user_settings and "trader_id_prefix" in user_settings[user_id]:
            trader_prefix_set = True
            current_prefix = user_settings[user_id]["trader_id_prefix"]
            
        for i in range(count):
            # If trader_id_prefix is set, increment it for each snapshot
            if trader_prefix_set:
                # Calculate the new prefix by adding i to the current prefix
                new_prefix = current_prefix + i
                # Store the incremented prefix temporarily
                user_settings[user_id]["current_trader_prefix"] = new_prefix
                
            snapshot = generate_snapshot(user_id)
            # Use parse_mode='HTML' to enable HTML formatting in the message
            await update.message.reply_text(snapshot, parse_mode='HTML')
            
    except ValueError:
        await update.message.reply_text("Please provide a valid number for count.")
    except Exception as e:
        logger.error(f"Error in generate_command: {e}")
        await update.message.reply_text(f"An error occurred: {str(e)}")

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reset all user settings to default."""
    user_id = update.effective_user.id
    message = reset_user_settings(user_id)
    await update.message.reply_text(message)

# Generic handler for all /set* commands
async def set_parameter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle all parameter setting commands."""
    try:
        user_id = update.effective_user.id
        command = update.message.text.split()[0].lower()
        
        # Initialize user settings if not exists
        if user_id not in user_settings:
            user_settings[user_id] = {}
        
        # Extract parameter name from command
        param = command.replace('/set', '').lower()
        
        # Map command parameters to internal parameter names
        param_mapping = {
            'date': 'reg_date',
            'percent': 'affiliate_percent',
            'linkid': 'link_id',
            'balance': 'balance',
            'depositscount': 'deposits_count',
            'depositssum': 'deposits_sum',
            'bonusescount': 'bonuses_count',
            'bonussum': 'bonuses_sum',
            'withdrawalscount': 'withdrawals_count',
            'withdrawalssum': 'withdrawals_sum',
            'pendingwithdrawalscount': 'pending_withdrawals_count',
            'pendingwithdrawalssum': 'pending_withdrawals_sum',
            'turnoverall': 'turnover_all',
            'turnoverclear': 'turnover_clear',
            'plall': 'pl_all',
            'plclear': 'pl_clear',
            'volshare': 'vol_share',
            'revshare': 'rev_share',
            'con': 'country',
            'traderid': 'trader_id_prefix'
        }
        
        # Debug log
        logger.info(f"Command: {command}, Param: {param}, Args: {context.args}")
        
        if param not in param_mapping:
            await update.message.reply_text(f"Unknown parameter: {param}")
            return
        
        internal_param = param_mapping[param]
        
        # Get the value from command arguments
        if not context.args:
            # If no value provided, set to 0 or appropriate default
            if internal_param in ['country']:
                user_settings[user_id][internal_param] = "India"
            elif internal_param in ['pl_clear', 'rev_share']:
                user_settings[user_id][internal_param] = "-"
            elif internal_param == 'trader_id_prefix':
                user_settings[user_id][internal_param] = None
                await update.message.reply_text(f"Trader ID prefix reset. Random trader IDs will be used.")
                return
            else:
                user_settings[user_id][internal_param] = 0
            await update.message.reply_text(f"{param.capitalize()} set to default value.")
            return
            
        value = ' '.join(context.args)
        
        # Special handling for different parameter types
        if internal_param in ['reg_date']:
            # Date format validation - now supports ranges
            if '-' in value:
                # Date range format
                try:
                    parsed_date = parse_date_range(value)
                    user_settings[user_id][internal_param] = parsed_date
                    
                    # Display message depends on whether it's a range or single date
                    if isinstance(parsed_date, dict) and parsed_date.get('type') == 'range':
                        await update.message.reply_text(f"{param.capitalize()} set to random date in range: {parsed_date['min']} to {parsed_date['max']}")
                    else:
                        await update.message.reply_text(f"{param.capitalize()} set to date: {parsed_date}")
                        
                    logger.info(f"Set date range: {value} -> {parsed_date}")
                except Exception as e:
                    await update.message.reply_text(f"Invalid date range format. Use DD.MM.YYYY-DD.MM.YYYY. Error: {str(e)}")
                    logger.error(f"Date range error: {e}")
                return
            elif re.match(r'^\d{2}\.\d{2}\.\d{4}$', value):
                user_settings[user_id][internal_param] = value
            else:
                await update.message.reply_text("Invalid date format. Use DD.MM.YYYY or DD.MM.YYYY-DD.MM.YYYY for range")
                return
        elif internal_param in ['country']:
            # String value
            user_settings[user_id][internal_param] = value
        elif internal_param in ['pl_clear', 'rev_share']:
            # Text value that can be '-'
            user_settings[user_id][internal_param] = value if value != '0' else '-'
        elif internal_param == 'trader_id_prefix':
            # Trader ID prefix must be a 2-digit number
            try:
                prefix = int(value)
                if prefix < 10 or prefix > 99:
                    await update.message.reply_text("Trader ID prefix must be a 2-digit number (10-99)")
                    return
                user_settings[user_id][internal_param] = prefix
                await update.message.reply_text(f"Trader ID prefix set to {prefix}. All generated trader IDs will start with {prefix} and increment for multiple snapshots.")
                return
            except ValueError:
                await update.message.reply_text("Trader ID prefix must be a 2-digit number (10-99)")
                return
        else:
            # Numeric values (can be ranges)
            try:
                parsed_value = parse_range_input(value)
                user_settings[user_id][internal_param] = parsed_value
            except ValueError:
                await update.message.reply_text(f"Invalid value for {param}. Must be a number or range (e.g., 100-500)")
                return
        
        # Display the current value (for ranges, show the initial random value)
        display_value = value
        if isinstance(value, dict) and 'type' in value and value['type'] == 'range':
            display_value = value['value']
            
            # For date ranges, show that it's a range
            if value.get('is_date', False):
                await update.message.reply_text(f"{param.capitalize()} set to random date in range: {value['min']} to {value['max']}")
                return
            else:
                # For numeric ranges, show that it's a range
                await update.message.reply_text(f"{param.capitalize()} set to random value in range: {value['min']} to {value['max']}")
                return
                
        await update.message.reply_text(f"{param.capitalize()} set to {display_value}")
        
    except Exception as e:
        logger.error(f"Error in set_parameter: {e}")
        await update.message.reply_text(f"An error occurred: {str(e)}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        "📋 Quotex Partner Snapshot Generator Help:\n\n"
        "Basic Commands:\n"
        "/start - Start the bot and reset settings\n"
        "/generate - Generate a snapshot with current settings\n"
        "/generate <count> - Generate multiple snapshots\n"
        "/reset - Reset all settings to default\n"
        "/zeros - Set all values to zero\n"
        "/help - Show this help message\n\n"
        "Customization Commands:\n"
        "Use these commands to set specific values:\n"
        "/setdate DD.MM.YYYY - Set exact registration date\n"
        "/setdate DD.MM.YYYY-DD.MM.YYYY - Set date range (random date picked)\n"
        "/setbalance 500 - Set exact balance\n"
        "/setbalance 100-1000 - Set balance range (random value picked)\n"
        "/settraderid 51 - Set trader ID prefix (2 digits only)\n\n"
        "Custom Command Format:\n"
        "You can combine multiple commands in a single message:\n"
        "/setdate 01.05.2025 /setpercent 5 /setbalance 5000 /setdepositscount 1 /setdepositssum 30 /setturnoverclear 200 /setplall 4000 /setrevshare 10\n"
        "Or use the /custom prefix:\n"
        "/custom /setdate 01.05.2025 /setpercent 5 /setbalance 5000\n"
        "Then send an 8-digit trader ID to generate a snapshot.\n\n"
        "Important Notes:\n"
        "- If you use a command without a value (e.g., /setbalance), it will set that value to 0\n"
        "- For date ranges, use format like: /setdate 01.01.2025-31.12.2025\n"
        "- For numeric ranges, use format like: /setbalance 100-500\n"
        "- When using /settraderid with multiple snapshots, the prefix will increment for each snapshot\n"
        "  Example: /settraderid 51 then /generate 3 will create IDs starting with 51, 52, 53\n\n"
        "After setting your parameters, use /generate to create snapshots."
    )

# Process trader ID message
async def process_trader_id_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process a trader ID message and generate a snapshot using that exact ID."""
    user_id = update.effective_user.id
    trader_id = update.message.text.strip()
    
    # Set the trader ID in user settings
    if user_id not in user_settings:
        user_settings[user_id] = {}
    
    # Use the exact trader ID provided by the user
    user_settings[user_id]['trader_id'] = trader_id
    
    # Generate and send a snapshot
    snapshot = generate_snapshot(user_id)
    await update.message.reply_html(snapshot)

def main() -> None:
    """Start the bot."""
    # Create the Application
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token or token == "your_bot_token_here":
        print("Error: TELEGRAM_BOT_TOKEN not properly set")
        print("Please add your bot token to the .env file:")
        print("1. Open the .env file in the project directory")
        print("2. Replace 'your_bot_token_here' with your actual bot token")
        return
        
    application = Application.builder().token(token).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("generate", generate_command))
    application.add_handler(CommandHandler("reset", reset_command))
    application.add_handler(CommandHandler("zeros", lambda update, context: initialize_user_settings_with_zeros(update.effective_user.id) and update.message.reply_text("All values set to zeros.")))
    application.add_handler(CommandHandler("custom", process_custom_command))
    
    # Add all the set parameter handlers
    set_commands = [
        "setdate", "setpercent", "setlinkid", "setbalance", 
        "setdepositscount", "setdepositssum", "setbonusescount", "setbonussum",
        "setwithdrawalscount", "setwithdrawalssum", "setpendingwithdrawalscount",
        "setpendingwithdrawalssum", "setturnoverall", "setturnoverclear",
        "setplall", "setplclear", "setvolshare", "setrevshare", "setcon", "settraderid"
    ]
    
    for cmd in set_commands:
        application.add_handler(CommandHandler(cmd, set_parameter))
    
    # Add handler for processing trader IDs after parameters have been set
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^\d{8}$'), 
        lambda update, context: process_trader_id_message(update, context)))
    
    # Add custom command handler for processing multiple parameters in one message
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^/'), process_custom_command))

    # Run the bot until the user presses Ctrl-C
    print("Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
