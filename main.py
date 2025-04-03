import subprocess
import sys
import os
import random
import http.client
import json
import time
import threading
from datetime import datetime

try:
    from rich.console import Console
    from rich.table import Table
    from rich import box
    from rich.text import Text
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "rich"])
    os.system('cls' if os.name == 'nt' else 'clear')
    input("Successfully installed requirements, press Enter to restart.")
    os.execl(sys.executable, sys.executable, *sys.argv)

console = Console()

def load_config():
    with open('./config.json') as f:
        config_data = json.load(f)['Config'][0]
        config_data['delay'] = int(config_data['delay'])
        return config_data

config = load_config()
header_data = { 
    "Content-Type": "application/json", 
    "User-Agent": "DiscordBot", 
    "Authorization": config['token']  
}

channel_status = {str(index + 1): {"id": channel_id, "status": "OFF", "last_msg": "", "error": "", "delay_left": 0} for index, channel_id in enumerate(config['channels'])}
bot_active = True
bot_threads = {}

messages = config['message'].split("\n")  # Splitting into multiple lines

def get_connection():
    return http.client.HTTPSConnection("discord.com", 443)

def send_message(channel_id):
    full_message = "\n".join(messages)  # Send full message instead of one line
    message_data = json.dumps({"content": full_message, "tts": False})

    try:
        conn = get_connection()
        conn.request("POST", f"/api/v10/channels/{channel_status[channel_id]['id']}/messages", message_data, header_data)
        resp = conn.getresponse()
        
        if 199 < resp.status < 300:
            channel_status[channel_id]['status'] = "ALIVE"
            channel_status[channel_id]['last_msg'] = datetime.now().strftime('%I:%M %p')  # Format as "11:19 AM"
            channel_status[channel_id]['error'] = ""
        else:
            channel_status[channel_id]['status'] = "ERROR"
            channel_status[channel_id]['error'] = f"HTTP {resp.status}"
    except Exception as e:
        channel_status[channel_id]['status'] = "ERROR"
        channel_status[channel_id]['error'] = str(e)

def channel_loop(channel_id):
    while bot_active and channel_status[channel_id]['status'] == "ON":
        send_message(channel_id)
        time.sleep(config['delay'])

def toggle_channel(channel_id):
    if channel_id not in channel_status:
        console.print("[red]Invalid Channel Tag.[/red] Please enter a valid tag number.")
        return
    
    if channel_status[channel_id]['status'] == "ON":
        channel_status[channel_id]['status'] = "OFF"
    else:
        channel_status[channel_id]['status'] = "ON"
        thread = threading.Thread(target=channel_loop, args=(channel_id,), daemon=True)
        bot_threads[channel_id] = thread
        thread.start()
    
    display_ui()  # Refresh UI only when action occurs

def update_config():
    with open('./config.json', 'w') as f:
        config['channels'] = [channel['id'] for channel in channel_status.values()]
        json.dump({"Config": [config]}, f, indent=4)

def display_ui():
    os.system('cls' if os.name == 'nt' else 'clear')  # Clear console before updating UI

    table = Table(title="Discord Bot Control Panel", box=box.SIMPLE, show_lines=True)
    table.add_column("Tag", justify="left", style="cyan", no_wrap=True)
    table.add_column("Channel ID", justify="left", style="magenta")
    table.add_column("Status", justify="left")
    table.add_column("Last Message Sent", justify="center")
    table.add_column("Error", justify="center")
    table.add_column("Delay Left", justify="right")

    for tag, status_data in channel_status.items():
        status_color = "green" if status_data["status"] == "ALIVE" else "red" if status_data["status"] == "ERROR" else "yellow"
        status_text = Text(status_data["status"], style=status_color)
        
        table.add_row(
            tag,
            status_data['id'],
            status_text,
            status_data['last_msg'] or "-",
            status_data['error'] or "-",
            str(round(status_data['delay_left'], 2))
        )
    
    console.print(table)

if __name__ == '__main__':
    while bot_active:
        display_ui()
        user_input = input("[A]dd channel, [R]emove channel, [T]oggle channel, [E]xit: ").strip().lower()
        
        if user_input.startswith('t'):
            channel_tag = input("Enter Channel Tag to Toggle: ").strip()
            toggle_channel(channel_tag)
        
        elif user_input.startswith('e'):
            bot_active = False
            break
