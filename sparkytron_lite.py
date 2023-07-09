#This should be a much lighter version of Sparkytron.
from dotenv import load_dotenv
import discord
from discord.ext import commands
from discord.utils import get
import os
import json
import openai
import asyncio
import random
import aiohttp

# env vars START
load_dotenv()

env_vars = {
    'openai.api_key': os.getenv('openai.api_key'),
    'discord_token': os.getenv('sparkytron_lite_token'),
}

#discord stuff START
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
#discord stuff END
openai.api_key = env_vars['openai.api_key']

async def create_channel_config(filepath):
    config_dict = {
        "personality":"average",
        "channel_topic":"casual",
        "chat_enabled":False,
        "commands_enabled":True,
        "chat_history_len":5,
        "react_to_msgs":False,
    }

    with open(filepath,"w") as f:
        json.dump(config_dict,f)
    print("Wrote config variables to file.")
        
async def get_channel_config(channel_id):
    filepath = "config/{0}.json".format(str(channel_id))
    if not os.path.exists(filepath):
        await create_channel_config(filepath)
    with open(filepath, "r") as f:
        config_dict = json.loads(f.readline())
    return config_dict
    
async def edit_channel_config(channel_id, key, value):
    config_file = "config/" + str(channel_id) + ".json"
    with open(config_file, 'r') as f:
        config_data = json.load(f)
    config_data[key] = value
    with open(config_file, "w") as f:
        json.dump(config_data, f)
    
async def react_to_msg(ctx, react):
    if True:
        if not random.randint(0,10) and ctx.author.id != 1126639833033494568: #this should be your bots author id
            prompt = "Send only an emoji as a discord reaction to the following chat message sent to you:\n"
            message = prompt + ctx.content[0] + '\n'
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {os.getenv("openai.api_key")}',
            }

            data = {
                "model": "text-davinci-003",
                "prompt": message,
            }

            url = "https://api.openai.com/v1/completions"

            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, headers=headers, json=data) as resp:
                        response_data = await resp.json()
                        reaction = response_data['choices'][0]['text']
                await ctx.add_reaction(reaction.strip())
            except Exception as error:
                print("Some error happened while trying to react to a message")
                print(str(error))
                print(response_data)
            
async def log_chat_and_get_history(ctx, logfile, channel_vars):          
    log_line = ctx.content
    log_line =  ctx.author.name + ": " + log_line  +"\n"
    chat_history = ""
    print("Logging: " + log_line, end="")
    with open(logfile, "a", encoding="utf-8") as f:
        f.write(log_line)
    with open(logfile, "r", encoding="utf-8") as f:
        for line in (f.readlines() [-int(channel_vars["chat_history_len"]):]):
            chat_history += line
    return chat_history

        
async def chat_response(ctx, channel_vars, chat_history_string): 
    async with ctx.channel.typing(): 
        await asyncio.sleep(1)
        prompt = f"You are a {channel_vars['personality']} chat bot named Sparkytron Lite created by @phixxy.com. Your personality should be {channel_vars['personality']}. You are currently in a {channel_vars['channel_topic']} chatroom. The message history is: {chat_history_string}"
        headers = { 
            'Content-Type': 'application/json', 
            'Authorization': f'Bearer {os.getenv("openai.api_key")}',
        }
        
        data = { 
            "model": "gpt-3.5-turbo", 
            "messages": [{"role": "user", "content": prompt}]
        }

        url = "https://api.openai.com/v1/chat/completions"

        try: 
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as resp:
                    response_data = await resp.json() 
                    response = response_data['choices'][0]['message']['content']
                    if "Sparkytron Lite:" in response[0:17]:
                        response = response.replace("Sparkytron Lite:", "")
                    max_len = 1999
                    if len(response) > max_len:
                        messages=[response[y-max_len:y] for y in range(max_len, len(response)+max_len,max_len)]
                    else:
                        messages=[response]
                    for message in messages:
                        await ctx.channel.send(message)

        except Exception as error: 
            print(error)
        
async def make_json_file(filename):
    if filename not in os.listdir():
        fileobj = open(filename,"w")
        fileobj.write("{}")
        fileobj.close()


@bot.command()        
async def question(ctx, model="gpt-3.5-turbo"):
    question = ctx.message.content.split(" ", maxsplit=1)[1]
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {os.getenv("openai.api_key")}',
    }

    data = {
        "model": model,
        "messages": [{"role": "user", "content": question}]
    }

    url = "https://api.openai.com/v1/chat/completions"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as resp:
                response_data = await resp.json()
                answer = response_data['choices'][0]['message']['content']

    except Exception as error:
        print(error)
    chunks = [answer[i:i+1999] for i in range(0, len(answer), 1999)]
    for chunk in chunks:
        await ctx.send(chunk)
            
@bot.command()        
async def personality(ctx):
    personality_type = ctx.message.content.split(" ", maxsplit=1)[1]
    await edit_channel_config(ctx.channel.id, "personality", personality_type)
    await ctx.send("Personality changed to " + personality_type)
            
@bot.command()        
async def chat(ctx, message):
    if "enable" in message:
        await edit_channel_config(ctx.channel.id, "chat_enabled", True)
        await ctx.send("Chat Enabled")
    elif "disable" in message:
        await edit_channel_config(ctx.channel.id, "chat_enabled", False)
        await ctx.send("Chat Disabled")
    else:
        await ctx.send("Usage: !chat (enable|disable)")
        
@bot.command()
async def reactions(ctx, message):
    if "enable" in message:
        await edit_channel_config(ctx.channel.id, "react_to_msgs", True)
        await ctx.send("Reactions Enabled")
    elif "disable" in message:
        await edit_channel_config(ctx.channel.id, "react_to_msgs", False)
        await ctx.send("Reactions Disabled")
    else:
        await ctx.send("Usage: !reactions (enable|disable)")  

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))
    #stuff to do if first run
    if not os.path.exists("logs/"):
        os.mkdir("logs")
    if not os.path.exists("config/"):
        os.mkdir("config")

@bot.event
async def on_message(ctx):
    logfile = "logs/{0}.log".format(str(ctx.channel.id))
    channel_vars = await get_channel_config(ctx.channel.id)

    await react_to_msg(ctx, channel_vars["react_to_msgs"]) #emoji reactions
    chat_history_string = await log_chat_and_get_history(ctx, logfile, channel_vars)

    if channel_vars["commands_enabled"] or (ctx.author.id == 242018983241318410 and ctx.content[0] == "!"):
        await bot.process_commands(ctx)
        if not channel_vars["commands_enabled"]:
            await ctx.channel.send("This command only ran because you set it to allow to run even when commands are disabled")

    if channel_vars["chat_enabled"] and not ctx.author.bot:
        if ctx.content and ctx.content[0] != "!":
            await chat_response(ctx, channel_vars, chat_history_string)
        elif not ctx.content:
            await chat_response(ctx, channel_vars, chat_history_string)

bot.run(env_vars["discord_token"])
