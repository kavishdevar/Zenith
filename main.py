#!/bin/python3
import discord
from discord.ext import commands, tasks
# from discord import app_commands
import sqlite3
import json
from config import bot_token, openai_token
intents = discord.Intents.all()

# Create the client

bot = discord.Bot()

import logging

# Set up logging
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# Basic on_ready event
@bot.event
async def on_ready():
    await bot.sync_commands(guild_ids=[1071784179748048956])
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="https://bit.ly/InviteZenith"))
    print('Bot is ready')

# Basic ping command
@bot.command(name="ping")
async def ping(ctx):
    """
    Pings the bot.
    Usage: /ping
    """
    await ctx.respond(f"Pong! Latency is {bot.latency}",ephemeral=True)

# Level system
def calculate_level(messages):
    level = 1
    while level < 100 and messages >= ((level ** 2) * 25):
        level += 1
    return level
import json
# Rank system
def calculate_rank(level):
    if level >= 30:
        return "gold"
    elif level >= 15:
        return "silver"
    elif level >= 10:
        return "bronze"
    else:
        return "none"


@bot.event
async def on_message(message):
    if not message.author.bot:
        with open("users.json", "r") as f:
            users = json.load(f)
        # Add user to dictionary if they're not already in it
        if str(message.author.id) not in users:
            users[str(message.author.id)] = {
                "messages": 0,
                "level": 1
            }

        # Increment message count and update level if necessary
        users[str(message.author.id)]["messages"] += 1
        level = calculate_level(users[str(message.author.id)]["messages"])
        if level > users[str(message.author.id)]["level"]:
            users[str(message.author.id)]["level"] = level
            rank = calculate_rank(level)

            # Assign role based on rank
            if rank == "gold":
                role = discord.utils.get(message.guild.roles, name="gold")
                if role:
                    await message.author.add_roles(role)
            elif rank == "silver":
                role = discord.utils.get(message.guild.roles, name="silver")
                if role:
                    await message.author.add_roles(role)
            elif rank == "bronze":
                role = discord.utils.get(message.guild.roles, name="bronze")
                if role:
                    await message.author.add_roles(role)

        # Save changes to file
        with open("users.json", "w") as f:
            json.dump(users, f)

import typing
@bot.command(name='level')
async def level(ctx,username: typing.Optional[discord.Member]):
    """
    Check anyone's level in the server.
    Usage: /level [user]. If no username supplied, displays your level.
    """
    with open("users.json", "r") as f:
        users = json.load(f)
    user = username or ctx.author
    if str(user.id) in users:
        level = users[str(user.id)]["level"]
        await ctx.respond(f"{user.mention}, your current level is {level}.",ephemeral=True)
    else:
        await ctx.respond(f"{user.mention}, you haven't sent any messages yet.",ephemeral=True)

@bot.command(name='brag')
async def brag(ctx):
    """
    Brag your level
    Usage: /brag
    """
    with open("users.json", "r") as f:
        users = json.load(f)
    user = ctx.author
    if str(user.id) in users:
        level = users[str(user.id)]["level"]
        await ctx.respond(f"@here!! {user.mention} is level {level}!!")
    else:
        await ctx.respond(f"POG! :Pog_Chomp: {user.mention}, you haven't sent any messages yet.")

@bot.command(name='leaderboard')
async def leaderboard(ctx):
    """
    Check the Top Messegers on the Server.
    Usage: /leaderboard
    """
    with open("users.json", "r") as f:
        users = json.load(f)
    leaderboard = sorted(users.items(), key=lambda x: x[1]["level"], reverse=True)
    leaderboard = leaderboard[:10]
    leaderboard_str = "```\nLeaderboard:\n"
    for i, (user_id, user_data) in enumerate(leaderboard):
        user = await bot.fetch_user(int(user_id))
        level = user_data["level"]
        leaderboard_str += f"{i+1}. {user.name}#{user.discriminator} - Level {level}\n"
    leaderboard_str += "```"
    await ctx.respond(leaderboard_str)


# Moderation commands

@bot.command(name='ban')
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason:str):
    """
    Bans a member from the server.
    Usage: /ban [member]
    """
    if member == ctx.message.author:
        await ctx.respond("You cannot ban yourself.")
        return
    if reason == "":
        return

    message = f"You have been banned from {ctx.guild.name} for {reason}"
    await member.send(message)
    await member.ban(reason=reason)
    await ctx.respnd(f"{member} has been banned for {reason}.",ephemeral=True)
    log_channel = discord.utils.get(ctx.guild.channels, name="logs")
    if log_channel:
        embed = discord.Embed(title="Member Banned", color=0xFF5733)
        embed.add_field(name="User", value=f"{member.mention} ({member})")
        embed.add_field(name="Moderator", value=f"{ctx.author.mention} ({ctx.author})")
        embed.add_field(name="Reason", value=reason)
        await log_channel.send(embed=embed)

@bot.command(name='kick')
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason:str):
    """
    Kicks a member from the server.
    Usage: /kick [member]
    """
    if member == ctx.message.author:
        await ctx.respond("You cannot kick yourself.")
        return
    if reason == "":
        return
    message = f"You have been kicked from {ctx.guild.name} for {reason}"
    await member.send(message)
    await member.kick(reason=reason)
    await ctx.respond(f"{member} has been kicked for {reason}.",ephemeral=True)
    log_channel = discord.utils.get(ctx.guild.channels, name="logs")
    if log_channel:
        embed = discord.Embed(title="Member Kicked", color=0xFF5733)
        embed.add_field(name="User", value=f"{member.mention} ({member})")
        embed.add_field(name="Moderator", value=f"{ctx.author.mention} ({ctx.author})")
        embed.add_field(name="Reason", value=reason)
        await log_channel.send(embed=embed)

@bot.command(name='purge')
@commands.has_permissions(manage_messages=True)
async def purge(ctx, number: int):
    """
    Purges messages in the current channel.
    Usage: /purge [number]
    """
    await ctx.channel.purge(limit=number)
    await ctx.respond(f"{number} messages have been cleared.",ephemeral=True)
    log_channel = discord.utils.get(ctx.guild.channels, name="logs")
    if log_channel:
        embed = discord.Embed(title="Messages Cleared", color=0xFF5733)
        embed.add_field(name="Moderator", value=f"{ctx.author.mention} ({ctx.author})")
        embed.add_field(name="Amount", value=number)
        await log_channel.send(embed=embed)

@bot.command(name='addrole')
@commands.has_permissions(manage_roles=True)
async def addrole(ctx, member: discord.Member, *, role: discord.Role):
    """
    Adds a role from a member.
    Usage: /addrole [member] [role]
    """
    await member.add_roles(role)
    await ctx.respond(f"{role} has been added to {member.mention}.",ephemeral=True)
    log_channel = discord.utils.get(ctx.guild.channels, name="logs")
    if log_channel:
        embed = discord.Embed(title="Role Added", color=0xFF5733)
        embed.add_field(name="User", value=f"{member.mention} ({member})")
        embed.add_field(name="Role", value=role)
        embed.add_field(name="Moderator", value=f"{ctx.author.mention} ({ctx.author})")
        await log_channel.send(embed=embed)

@bot.command(name='removerole')
@commands.has_permissions(manage_roles=True)
async def removerole(ctx, member: discord.Member, *, role: discord.Role):
    """
    Removes a role from a member.
    Usage: /removerole [member] [role]
    """
    try:
        await member.remove_roles(role)
        await ctx.respond(f"{role.name} has been removed from {member.mention}.",ephemeral=True)
    except discord.Forbidden:
        await ctx.respond("I don't have the required permissions to do this.",ephemeral=True)
    except discord.HTTPException:
        await ctx.respond("An error occurred while attempting to remove the role.",ephemeral=True)

@bot.command(name='embed')
@commands.has_role('Helper')
async def embed(ctx, channel: discord.TextChannel, title: str, author: str, author_dp: typing.Optional[str]=None, text: typing.Optional[str]=None, img_url: typing.Optional[str]=None, thumbnail: typing.Optional[str]=None, ftext:str="Thank You!", ficon:typing.Optional[str]=None):
    """Create an embed message"""
    commandcompleteembed = discord.Embed(
        title="Completed",
        description="Your command has been executed. The embed has been created and sent!",
        color=0x00FF00
    )
    await ctx.response.send_message(embed=commandcompleteembed)
    embed = discord.Embed(
        title=title,
        description=text,
        color=0x00FF00
    )
    if author_dp!=None:
        embed.set_author(name=author, icon_url=author_dp)
    else:
        embed.set_author(name=author)
    if img_url!=None:
        embed.set_image(url=img_url)
    if thumbnail!=None:
        embed.set_thumbnail(url=thumbnail)
    if ficon!=None:
        embed.set_footer(text=ftext,icon_url=ficon)
    else:
        embed.set_footer(text=ftext)
    await channel.send(embed=embed)

# Apply for role command
@bot.command(name='apply-for-role')
async def apply_for_role(ctx, *, option_role: discord.Role):
    """
    Apply for roles. Request the admins/moderators to give you a role.
    Usage: /apply-for-role [role]
    """
    if ctx.channel.name != 'ask-for-roles':
        await ctx.respond('This command can only be run in the \#ask-for-roles channel.',ephemeral=True)
        return

    # DM the user with the instructions and form link
    dm_msg = (f'Your request for the role {option_role} has been received. '
              'The admins have also been notified about this request. '
              'Thank you for being a member of the DPS84 Server.\n\n'
              'To complete your request, you will have to fill form at the link sent to you in you DM.\n\n'
              'Please note that the initial Moderators and Helper roles were assigned on first-come-first basis because of lack of staff.')
    await ctx.author.send(dm_msg)
    await ctx.respond(f'Applied! Your request for the role {option_role} has been received. '
                   'The admins have also been notified about this request. '
                   'Thank you for being a member of the DPS84 Server.\n\n'
                   'To complete your request, you will have to fill form at the link sent to you in you DM.\n\n'
                   'Please note that the initial Moderators and Helper roles were assigned on first-come-first basis because of lack of staff.',ephemeral=True)

    # Send a message to the #role-requests channel
    channel = discord.utils.get(ctx.guild.channels, name='role-requests')
    if channel:
        msg = f'Hey! {ctx.author.mention} has requested you to give them the {option_role} role.\n\nThank You!'
        await channel.send(msg)

@bot.command(name="warn")
@commands.has_role("Moderator")
async def warn(ctx, member: discord.Member, reason: str):
    """
    Warns a member for a specific reason.
    Usage: /warn [Member] [Reason]
    """
    embed = discord.Embed(title="⚠️Warning!⚠️", description=f"You have been warned for {reason}. Please follow the rules.", color=discord.Color.red())
    embed.set_author(name=f"{ctx.author}")
    embed.set_footer(text="Thank you for being a part of the Delhi Public School Server.",ephemeral=True)
    try:
        await member.send(embed=embed)
    except discord.Forbidden:
        ctx.respond("Failed to send a warning message. The user may have their DMs disabled.",ephemeral=True)
    alert_message = f"⚠️ **{member.display_name}** has been warned by a staff member. Reason: {reason}."
    await discord.utils.get(name='alerts').send(content=alert_message)
    ctx.respond("Member Warned!")

@bot.command(name="msg")
@commands.has_role("Admin")
async def msg(ctx, member: discord.Member, message: str):
    """
    Message a member as the bot.
    Usage: /warn [Member] [Message]
    """
    try:
        await ctx.respond("DM'd Member!",ephemeral=True)
        await member.send(content=message)
    except discord.Forbidden:
        await ctx.respond("Failed to send a warning message. The user may have their DMs disabled.",ephemeral=True)

import asyncio, random

@bot.command(name="role_giveaway")
async def role_giveaway(ctx, time: int, *, role: discord.Role):
    """
    Starts a giveaway for a role for a specified time.
    Usage: /role_giveaway [Time in seconds] [role]
    """
    channel = bot.get_channel(1074973882211123221)  # Replace with the actual ID of the #giveaways channel

    embedResponse = discord.Embed(title="Done!", description=f"Embed for the giveaway for **{role.name}** has been sent!", color=0xffd700)
    await ctx.respond("Done!",embed=embedResponse,ephemeral=True)

    total_seconds = time
    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    if days > 0:
        time_remaining = f"{days} day{'s' if days != 1 else ''}"
    elif hours > 0:
        time_remaining = f"{hours} hour{'s' if hours != 1 else ''}"
    elif minutes > 0:
        time_remaining = f"{minutes} minute{'s' if minutes != 1 else ''}"
    else:
        time_remaining = f"{seconds} second{'s' if seconds != 1 else ''}"

    # Create the embed
    embed = discord.Embed(title="🎉 Giveaway Time!", description=f"React to this message to enter the giveaway for the **{role.name}** role!", color=0xffd700)
    embed.add_field(name="Time remaining", value=f"{time_remaining}")
    embed.set_footer(text="Good luck!")

    # Send the embed and add the reaction
    message = await channel.send(embed=embed)

    # Adds a reaction to the giveaway message
    await message.add_reaction('🎉')

 # Update the remaining time every 10 seconds
    for remaining_time in range(time, -1, -10):
        embed.set_field_at(index=0, name="Time remaining", value=f"{remaining_time} seconds")
        await message.edit(embed=embed)
        await asyncio.sleep(10)

    # Waits for the specified time
    await asyncio.sleep(time)

    # Retrieves all users who reacted to the message
    message = await channel.fetch_message(message.id)
    reaction = next(filter(lambda r: str(r.emoji) == '🎉', message.reactions), None)
    if reaction is None:
        await channel.send("No one reacted to the giveaway message. The giveaway is cancelled.")
    else:
        users = await reaction.users().flatten()
        users = list(filter(lambda u: not u.bot, users))
        winner = random.choice(users)
        # Update the original embed with the winner information
        embed.add_field(name="Winner", value=winner.mention)
        embed.set_footer(text="Congratulations!")
        await message.edit(embed=embed)
        
@bot.command(name="giveaway")
async def giveaway(ctx, time: int, *, prize: str):
    """
    Starts a giveaway with a specified time and prize.
    Usage: /giveaway [Time in seconds] [Prize]
    """
    channel = bot.get_channel(1074973882211123221)
    
    embedResponse = discord.Embed(title="Done!", description=f"Embed for the giveaway for **{prize}** has been sent!", color=0xffd700)
    
    await ctx.respond("Done!",embed=embedResponse,ephemeral=True)

    total_seconds = time
    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    if days > 0:
        time_remaining = f"{days} day{'s' if days != 1 else ''}"
    elif hours > 0:
        time_remaining = f"{hours} hour{'s' if hours != 1 else ''}"
    elif minutes > 0:
        time_remaining = f"{minutes} minute{'s' if minutes != 1 else ''}"
    else:
        time_remaining = f"{seconds} second{'s' if seconds != 1 else ''}"

    # Create the embed
    embed = discord.Embed(title="🎉 Giveaway Time!", description=f"React to this message to enter the giveaway for **{prize}**!", color=0xffd700)
    embed.add_field(name="Time remaining", value=f"{time_remaining}")
    embed.set_footer(text="Good luck!")

    # Send the embed and add the reaction
    message = await channel.send(embed=embed)
    await message.add_reaction('🎉')

    # Wait for the specified time
    await asyncio.sleep(time)

    # Retrieve all users who reacted to the message
    message = await channel.fetch_message(message.id)
    reaction = next(filter(lambda r: str(r.emoji) == '🎉', message.reactions), None)
    if reaction is None:
        await channel.send("No one reacted to the giveaway message. The giveaway is cancelled.")
    else:
        users = await reaction.users().flatten()
        users = list(filter(lambda u: not u.bot, users))
        winner = random.choice(users)

        # Update the original embed with the winner information
        embed.add_field(name="Winner", value=winner.mention)
        embed.set_footer(text="Congratulations {winner.mention}! You will be rewarded soon.")

        # Send the updated embed to the channel
        await message.edit(embed=embed)

import openai

# Set up the OpenAI API client
openai.api_key = openai_token

import json
from datetime import datetime, timedelta

PROMPT_LIMIT = 5
PROMPT_TIME_LIMIT_HOURS = 24
PROMPT_FILE_PATH = "user_prompts.json"

def load_user_prompts():
    try:
        with open(PROMPT_FILE_PATH, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_user_prompts(user_prompts):
    with open(PROMPT_FILE_PATH, "w") as f:
        json.dump(user_prompts, f)

user_prompts = load_user_prompts()

@bot.command(name="ask-gpt")
async def ask_gpt(ctx, prompt:str):
    user_id = str(ctx.author.id)
    
    if user_id in user_prompts:
        num_prompts = user_prompts[user_id]["num_prompts"]
        last_prompt_time = datetime.fromisoformat(user_prompts[user_id]["last_prompt_time"])
        if num_prompts >= PROMPT_LIMIT and datetime.now() - last_prompt_time < timedelta(hours=PROMPT_TIME_LIMIT_HOURS):
            await ctx.respond("You have reached the limit of {} prompts in the last {} hours.".format(PROMPT_LIMIT, PROMPT_TIME_LIMIT_HOURS), ephemeral=True)
            return
    
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        temperature=0.5,
        max_tokens=100,
        n=1,
        stop=None
    )
    
    if user_id not in user_prompts:
        user_prompts[user_id] = {"num_prompts": 1, "last_prompt_time": datetime.now().isoformat()}
    else:
        user_prompts[user_id]["num_prompts"] += 1
        user_prompts[user_id]["last_prompt_time"] = datetime.now().isoformat()
    
    save_user_prompts(user_prompts)
    
    await ctx.send("**\\> {}**\n```{}```".format(prompt, response.choices[0].text))

emojis=["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
@bot.command(name="poll")
async def poll(ctx, title, option1, option2, option3='', option4='', option5='', option6='', option7='', option8=''):
    """
    Create a Poll. e.g. - /poll [title] [option1] [option2]...
    """
    options = [option1,option2,option3,option4,option5,option6,option7,option8]
    message = ""
    await ctx.respond("Done!",ephemeral=True)
    for i in range(len(options)):
        while options[i] != '':
            message += emojis[i] + ". " + options[i] + "\n"
    embed = discord.Embed(title=title, description=message, color=0x00ff00)
    embed.set_author(name=ctx.author.nick, icon_url=ctx.author.avatar.url)
    message = await ctx.send(embed=embed)
    for i in range(0, len(options)):
        await message.add_reaction(emojis[i])
tick="✅"
# tick="✔️"
cross="❌"
@bot.command(name="yes-no-poll")
async def yes_no_poll(ctx, title, description=0):
    """
    Create a Yes/No Poll. e.g. - /poll [title] [description]
    """
    await ctx.respond("Done!",ephemeral=True)
    if description == '':
        embed = discord.Embed(title=title, description=description, color=0x00ff00)
    else:
        embed = discord.Embed(title=title, color=0x00ff00)
    embed.set_author(name=ctx.author.nick, icon_url=ctx.author.avatar.url)
    message = await ctx.send(embed=embed)

    await message.add_reaction(tick)
    await message.add_reaction(cross)

client=bot

# Coin flip command
@client.command(name='coinflip')
async def coinflip(ctx):
    """Flip a coin. e.g. /coinflip"""
    outcomes = ['Heads', 'Tails']
    response = 'The coin landed on ' + random.choice(outcomes) + '!'
    await ctx.respond(response)
from thefuzz import fuzz 
# Eight ball command
@client.command(name='8ball')
async def eight_ball(ctx, question):
    """Ask a question. e.g. /8ball [question]"""
    if not question:
        await ctx.respond('Please ask a question!')
        return

    responses = ['It is certain.', 'It is decidedly so.', 'Without a doubt.', 'Yes – definitely.', 'You may rely on it.', 'As I see it, yes.', 'Most likely.', 'Outlook good.', 'Yes.', 'Signs point to yes.', 'Reply hazy, try again.', 'Ask again later.', 'Better not tell you now.', 'Cannot predict now.', 'Concentrate and ask again.', 'Don\'t count on it.', 'Outlook not so good.', 'My sources say no.', 'Very doubtful.']
    response = random.choice(responses)
    if fuzz.token_set_ratio(question,"are you smart?")>50:
        await ctx.respond("Yes!")
        return
    if fuzz.token_set_ratio(question,"are you dumb?")>50:
        await ctx.respond("No!")
        return
    if fuzz.token_set_ratio(question,"am i smart?")>50:
        await ctx.respond("Yes!")
        return
    if fuzz.token_set_ratio(question,"am i dumb?")>50:
        await ctx.respond("No!")
        return
    ctx.respond(response)
    

# Role info command
@client.command(name='roleinfo')
async def roleinfo(ctx, role: discord.Role):
    """Show information about a role. e.g. /roleinfo [role]"""

    embed = discord.Embed(title=role.name)
    embed.add_field(name='ID', value=role.id)
    embed.add_field(name='Created At', value=role.created_at.strftime('%m/%d/%Y'))
    embed.add_field(name='Color', value=role.color)
    embed.add_field(name='Hoisted', value=role.hoist)
    embed.add_field(name='Mentionable', value=role.mentionable)
    embed.add_field(name='Permissions', value='\n'.join([str(p[0]).replace('_', ' ').title() + ': ' + str(p[1]) for p in role.permissions]))
    await ctx.respond(embed=embed)

# Random number command
@client.command(name='random')
async def random_number(ctx, min_num=0, max_num=100):
    """Give a random number e.g. /random [min,def=0] [max,def=100]"""
    num = random.randint(int(min_num), int(max_num))
    await ctx.respond(num)

# Server info command
@client.command(name='serverinfo')
async def serverinfo(ctx):
    """View info about this server. e.g. /serverinfo"""
    server = ctx.guild
    embed = discord.Embed(title=server.name)
    embed.add_field(name='ID', value=server.id)
    embed.add_field(name='Owner', value=server.owner.mention)
    # embed.add_field(name='Region', value=str(server.region).title())
    embed.add_field(name='Created At', value=ctx.guild.created_at.strftime('%m/%d/%Y'))
    embed.add_field(name='Members', value=server.member_count)
    embed.add_field(name='Roles', value=len(server.roles))
    embed.add_field(name='Channels', value=len(server.channels))
    embed.set_thumbnail(url=server.icon.url)
    await ctx.respond(embed=embed)

# Avatar command
@client.command(name='avatar')
async def avatar(ctx, user: typing.Optional[discord.Member]):
    """Shows a user's avatar, if username not supplied, shows your own avatar. e.g. /avatar [user]"""
    user = user or ctx.author
    embed = discord.Embed(title=user.name + '\'s avatar')
    embed.set_image(url=user.avatar.url)
    await ctx.respond(embed=embed)

# Unban command
@client.command(name='unban')
@commands.has_permissions(ban_members=True)
async def unban(ctx, member:discord.Member):
    """Unbans a user. e.g. /unban [member]"""
    banned_users = await ctx.guild.bans()
    member_name, member_discriminator = member.split('#')

    for ban_entry in banned_users:
        user = ban_entry.user

        if (user.name, user.discriminator) == (member_name, member_discriminator):
            await ctx.guild.unban(user)
            await ctx.respond(f'{user.name} has been unbanned!')
            return

import aiohttp
from bs4 import BeautifulSoup

# Urban Dictionary command
@client.command(name='ud')
async def ud(ctx, *, term):
    term = term.lower().replace(" ", "+")
    url = f"https://www.urbandictionary.com/define.php?term={term}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            soup = BeautifulSoup(await response.text(), 'html.parser')
            meaning = soup.find('div', {'class': 'meaning'}).text
            example = soup.find('div', {'class': 'example'}).text
            await ctx.respond(f"**{term.capitalize()}**: {meaning}\n\n*Example: {example}*")


# Run the bot
bot.run(bot_token)
