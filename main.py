import discord
import json
import FreeSimpleGUI as sg

intents = discord.Intents.default()
intents.guilds = True

# Создание GUI
def create_gui():
    layout = [
        [sg.Text('Bot Token:'), sg.InputText(key='-TOKEN-', size=(40, 1))],
        [sg.Text('Guild ID:'), sg.InputText(key='-GUILD_ID-', size=(40, 1))],
        [sg.Button('Create Backup'), sg.Button('Restore Server'), sg.Button('Delete All Channels'), sg.Button('Save Config'), sg.Button('Load Config')],
        [sg.Multiline(size=(70, 10), key='-LOG-', disabled=True)]
    ]
    
    window = sg.Window('Discord Server Backup', layout)

    while True:
        event, values = window.read()
        
        if event == sg.WINDOW_CLOSED:
            break
        elif event == 'Create Backup':
            run_discord_task(values['-TOKEN-'], values['-GUILD_ID-'], backup_server, window)
        elif event == 'Restore Server':
            run_discord_task(values['-TOKEN-'], values['-GUILD_ID-'], restore_server, window)
        elif event == 'Delete All Channels':
            run_discord_task(values['-TOKEN-'], values['-GUILD_ID-'], delete_all_channels, window)
        elif event == 'Save Config':
            save_config(values['-TOKEN-'], values['-GUILD_ID-'], window)
        elif event == 'Load Config':
            load_config(window)

    window.close()

def save_config(bot_token, guild_id, window):
    config = {
        'bot_token': bot_token,
        'guild_id': guild_id
    }
    with open('config.json', 'w') as f:
        json.dump(config, f)
    log_message(window, "Configuration saved.")

def load_config(window):
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            window['-TOKEN-'].update(config.get('bot_token', ''))
            window['-GUILD_ID-'].update(config.get('guild_id', ''))
        log_message(window, "Configuration loaded.")
    except FileNotFoundError:
        log_message(window, "Configuration file not found.")

def log_message(window, message):
    window['-LOG-'].update(message + '\n', append=True)

def run_discord_task(bot_token, guild_id, task, window):
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        log_message(window, f'Logged in as {client.user}')
        await task(client, int(guild_id), window)
        await client.close()

    client.run(bot_token)

async def backup_server(client, guild_id, window):
    backup_data = {}
    guild = client.get_guild(guild_id)

    # Сохранение структуры категорий и каналов
    backup_data['categories'] = []
    for category in guild.categories:
        cat_data = {
            'name': category.name,
            'channels': []
        }
        for channel in category.channels:
            if isinstance(channel, discord.TextChannel):
                channel_type = 'text'
            elif isinstance(channel, discord.VoiceChannel):
                channel_type = 'voice'
            elif isinstance(channel, discord.ForumChannel):
                channel_type = 'forum'
            else:
                continue
            cat_data['channels'].append({
                'name': channel.name,
                'type': channel_type
            })
        backup_data['categories'].append(cat_data)

    # Сохранение каналов вне категорий
    backup_data['channels'] = []
    for channel in guild.channels:
        if channel.category is None:
            if isinstance(channel, discord.TextChannel):
                channel_type = 'text'
            elif isinstance(channel, discord.VoiceChannel):
                channel_type = 'voice'
            elif isinstance(channel, discord.ForumChannel):
                channel_type = 'forum'
            else:
                continue
            backup_data['channels'].append({
                'name': channel.name,
                'type': channel_type
            })
    
    with open('server_backup.json', 'w') as f:
        json.dump(backup_data, f)
    
    log_message(window, "Backup created successfully!")

async def restore_server(client, guild_id, window):
    try:
        with open('server_backup.json', 'r') as f:
            backup_data = json.load(f)

        guild = client.get_guild(guild_id)

        # Восстановление категорий и каналов
        for category_data in backup_data['categories']:
            category = await guild.create_category(name=category_data['name'])
            for channel_data in category_data['channels']:
                if channel_data['type'] == 'text':
                    await category.create_text_channel(name=channel_data['name'])
                elif channel_data['type'] == 'voice':
                    await category.create_voice_channel(name=channel_data['name'])
                elif channel_data['type'] == 'forum':
                    await category.create_forum(name=channel_data['name'])

        # Восстановление каналов вне категорий
        for channel_data in backup_data['channels']:
            if channel_data['type'] == 'text':
                await guild.create_text_channel(name=channel_data['name'])
            elif channel_data['type'] == 'voice':
                await guild.create_voice_channel(name=channel_data['name'])
            elif channel_data['type'] == 'forum':
                await guild.create_forum(name=channel_data['name'])

        log_message(window, "Server restored successfully!")
    except FileNotFoundError:
        log_message(window, "Backup file not found!")

# Функция для удаления всех каналов и категорий
async def delete_all_channels(client, guild_id, window):
    guild = client.get_guild(guild_id)
    
    for channel in guild.channels:
        try:
            await channel.delete()
        except discord.errors.HTTPException as e:
            if e.code == 50074:
                log_message(window, f"Skipping required community channel: {channel.name}")
            else:
                log_message(window, f"Error deleting channel {channel.name}: {e}")

    log_message(window, "All deletable channels and categories have been deleted successfully!")

create_gui()
