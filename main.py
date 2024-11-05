#!/bin/python3
import discord
from discord.ext import commands, tasks
from discord import option
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

# Set up logging
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# Basic on_ready event
@bot.event
async def on_ready():
    await bot.sync_commands()
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="your commands (and pretending to care 😏)."))
    print('Bot is ready')

@bot.event
async def on_command_error(ctx, exception):
    if isinstance(exception, commands.errors.CommandNotFound):
        await ctx.respond(f"Command `{ctx.invoked_with}` not found.", ephemeral=True)
    elif isinstance(exception, commands.errors.MissingPermissions):
        await ctx.respond(f"Sorry, you don't have the required permissions to run this command.", ephemeral=True)
    elif isinstance(exception, commands.errors.MissingRequiredArgument):
        await ctx.respond(f"Please provide all required arguments.", ephemeral=True)
    elif isinstance(exception, commands.errors.BadArgument):
        await ctx.respond(f"Invalid argument.", ephemeral=True)
    else:
        await ctx.respond(f"Sorry, something went wrong.", ephemeral=True)
    print(f"Command `{ctx.invoked_with}` failed with the following error:\n{exception}")

# Basic ping command
@bot.slash_command(name="ping")
async def ping(ctx):
    """
    Pings the bot. Usage: /ping
    """
    try:
        await ctx.respond(f"Pong! Latency is {bot.latency}",ephemeral=True)
    except Exception as e:
        await ctx.respond(f"Error: {e}",ephemeral=True)

# Level system
def calculate_level(messages):
    level = 1
    while level < 100 and messages >= ((level ** 2) * 25):
        level += 1
    return level

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
        print(f"{message.author} sent a message: {message.content}")
        # response = openai.Moderation.create(
        #     input=message
        # )
        # output = response["results"][0]
        with open("users.json", "r") as fi:
            users = json.load(fi)
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
@bot.slash_command(name='level')
async def level(ctx,username: typing.Optional[discord.Member]):
    """
    Check anyone's level in the server. Usage: /level [user], Displays your level if user=None.
    """
    with open("users.json", "r") as f:
        users = json.load(f)
    user = username or ctx.author
    if str(user.id) in users:
        level = users[str(user.id)]["level"]
        await ctx.respond(f"{user.mention}, your current level is {level}.",ephemeral=True)
    else:
        await ctx.respond(f"{user.mention}, you haven't sent any messages yet.",ephemeral=True)

@bot.slash_command(name='brag')
async def brag(ctx):
    """
    Brag your level. Usage: /brag
    """
    await ctx.response.defer()
    with open("users.json", "r") as f:
        users = json.load(f)
    user = ctx.author
    if str(user.id) in users:
        level = users[str(user.id)]["level"]
        await ctx.respond(f"@here!! {user.mention} is level {level}!!")
    else:
        await ctx.respond(f"<:PogChomp:1072477340011088544> {user.mentions}, You haven't sent any mesaages in this server yet")


@bot.slash_command(name='leaderboard')
async def leaderboard(ctx):
    """
    Check the Top Messegers on the Server. Usage: /leaderboard
    """
    await ctx.response.defer()
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
    await ctx.followup.send(leaderboard_str)


# Moderation commands

@bot.slash_command(name='ban')
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason:str):
    """
    Bans a member from the server. Usage: /ban [member]
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

@bot.slash_command(name='kick')
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason:str):
    """
    Kicks a member from the server. Usage: /kick [member]
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

@bot.slash_command(name='purge')
@commands.has_permissions(manage_messages=True)
async def purge(ctx, number: int):
    """
    Purges messages in the current channel.Usage: /purge [number]
    """
    await ctx.channel.purge(limit=number)
    await ctx.respond(f"{number} messages have been cleared.",ephemeral=True)
    log_channel = discord.utils.get(ctx.guild.channels, name="logs")
    if log_channel:
        embed = discord.Embed(title="Messages Cleared", color=0xFF5733)
        embed.add_field(name="Moderator", value=f"{ctx.author.mention} ({ctx.author})")
        embed.add_field(name="Amount", value=number)
        await log_channel.send(embed=embed)

@bot.slash_command(name='addrole')
@commands.has_permissions(manage_roles=True)
async def addrole(ctx, member: discord.Member, *, role: discord.Role):
    """
    Adds a role from a member. Usage: /addrole [member] [role]
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

@bot.slash_command(name='removerole')
@commands.has_permissions(manage_roles=True)
async def removerole(ctx, member: discord.Member, *, role: discord.Role):
    """
    Removes a role from a member. Usage: /removerole [member] [role]
    """
    try:
        await member.remove_roles(role)
        await ctx.respond(f"{role.name} has been removed from {member.mention}.",ephemeral=True)
    except discord.Forbidden:
        await ctx.respond("I don't have the required permissions to do this.",ephemeral=True)
    except discord.HTTPException:
        await ctx.respond("An error occurred while attempting to remove the role.",ephemeral=True)

@bot.slash_command(name='embed')
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
@bot.slash_command(name='apply-for-role')
async def apply_for_role(ctx, *, option_role: discord.Role):
    """
    Apply for roles. Request the admins/moderators to give you a role. Usage: /apply-for-role [role]
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

@bot.slash_command(name="dm")
@commands.has_role("Admin")
async def msg(ctx, member: discord.Member, message: str):
    """
    Message a member as the bot. Usage: /warn [Member] [Message]
    :param member: The member to message
    :param message: The message to send
    """
    try:
        await member.send(content=message)
        await ctx.respond("DM'd Member!",ephemeral=True)
    except discord.Forbidden:
        await ctx.respond("Failed to send a warning message. The user may have their DMs disabled.",ephemeral=True)

import asyncio, random
import time as atime

@bot.slash_command(name="role-giveaway")
@commands.has_role("Admin")
async def role_giveaway(ctx, time: int, role: discord.Role, channel: discord.TextChannel, winners: int = 1):
    """
    Starts a giveaway for a role for a specified time. Usage: /role_giveaway [Time in seconds] [role]
    :param ctx: The context of the command
    :param time: The time in seconds for the giveaway
    :param role: The role to be given away
    :param channel: The channel to send the giveaway embed in
    :param winners: The number of winners
    """
    print(time, role, channel, winners)
    # await ctx.response.defer()
    embedResponse = discord.Embed(title="Done!", description=f"Embed for the giveaway for **{role.name}** has been sent!", color=0xffd700)
    await ctx.respond(embed=embedResponse,ephemeral=True)
    # await ctx.response.send_message(embed=embedResponse,ephermal=True)
    cTime=atime.time()
    eTime=cTime+time
    # Create the embed
    embed = discord.Embed(title="🎉 Giveaway Time!", description=f"React to this message to enter the giveaway for the **{role.name}** role!", color=0xffd700)
    embed.add_field(name="Time remaining", value=f"<t:{eTime}:R>")
    embed.set_footer(text="Good luck!")
    enter_button = discord.ui.button(label="Enter Giveaway!", style=discord.ButtonStyle.green)
    # discord.ui.View(enter_button)
    # enter_action_row = discord.ActionRow(enter_button)
    #bot.add_view(enter_action_row)

    # Send the embed and add the reaction
    message = await ctx.channel.send(embed=embed, view=discord.ui.View(enter_button, timeout=time))

    # Define the check to only allow the user who initiated the command to interact with the button
    def check(interaction: discord.Interaction):
        return interaction.user == ctx.author

    # Wait for the user to click the button to enter the giveaway
    interaction = await bot.wait_for("button_click", check=check)

    # Add the user who clicked the button to the list of entries
    entries = [interaction.user]

    # Wait for the user to click the button to enter the giveaway
    interaction = await bot.wait_for("button_click", check=check)

    # Add the user who clicked the button to the list of entries
    entries = [interaction.user]
    interaction = await bot.wait_for("button_click", check=check, timeout=time)
    if interaction.user in entries:
        await interaction.response.send_message("You have already entered the giveaway!", ephemeral=True)
    else:
     entries.append(interaction.user)

    await asyncio.sleep(time)

    users = entries
    #users = list(filter(lambda u: not u.bot, users))
    winnerlist=[]
    mentions=""
    for i in range(winners):
        winner=random.choice(users)
        winnerlist.append(winner)
        mentions+="{winner.mention}"
        users.remove(winner)
        winner.add_roles(role)
    # Update the original embed with the winner information
    embed.add_field(name="Winner", value=mentions)
    embed.set_footer(text="Congratulations!")
    await message.edit(embed=embed)
        
@bot.slash_command(name="giveaway")
async def giveaway(ctx, time: int, *, prize: str, channel: discord.TextChannel, winners: int = 1):
    """
    Starts a giveaway with a specified time and prize. Usage: /giveaway [Time in seconds] [Prize]
    :param ctx: The context of the command
    :param time: The time in seconds for the giveaway
    :param prize: The prize to be given away
    """
    
    print(time, role, channel, winners)
    # await ctx.response.defer()
    embedResponse = discord.Embed(title="Done!", description=f"Embed for the giveaway for **{prize}** has been sent!", color=0xffd700)
    await ctx.respond(embed=embedResponse,ephemeral=True)
    # await ctx.response.send_message(embed=embedResponse,ephermal=True)
    cTime=atime.time()
    eTime=cTime+time
    # Create the embed
    embed = discord.Embed(title="🎉 Giveaway Time!", description=f"React to this message to enter the giveaway for **{prize}**!", color=0xffd700)
    embed.add_field(name="Time remaining", value=f"<t:{eTime}:R>")
    embed.set_footer(text="Good luck!")
    enter_button = discord.ui.Button(label="Enter Giveaway!", style=discord.ButtonStyle.green)
    enter_action_row = discord.ActionRow(enter_button)
    #bot.add_view(enter_action_row)

    # Send the embed and add the reaction
    message = await ctx.channel.send(embed=embed, view=discord.ui.View(enter_action_row))

    # Define the check to only allow the user who initiated the command to interact with the button
    def check(interaction: discord.Interaction):
        return interaction.user == ctx.author

    # Wait for the user to click the button to enter the giveaway
    interaction = await bot.wait_for("button_click", check=check)

    # Add the user who clicked the button to the list of entries
    entries = [interaction.user]

    # Wait for the user to click the button to enter the giveaway
    interaction = await bot.wait_for("button_click", check=check)

    # Add the user who clicked the button to the list of entries
    entries = [interaction.user]
    interaction = await bot.wait_for("button_click", check=check, timeout=time)
    if interaction.user in entries:
        await interaction.response.send_message("You have already entered the giveaway!", ephemeral=True)
    else:
     entries.append(interaction.user)

    await asyncio.sleep(time)

    users = entries
    #users = list(filter(lambda u: not u.bot, users))
    winnerlist=[]
    mentions=""
    for i in range(winners):
        winner=random.choice(users)
        winnerlist.append(winner)
        mentions+="{winner.mention}"
        # winner = random.choice(users)
    # Update the original embed with the winner information
    
    embed.add_field(name="Winner", value=mentions)
    embed.set_footer(text="Congratulations!")
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

@bot.slash_command(name="ask-gpt")
async def ask_gpt(ctx, prompt:str):
    """Use the GPT3 AI Model. e.g. /ask-gpt [prompt]"""
    await ctx.response.defer()
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

@bot.slash_command(name="poll")
async def poll(ctx, title, option1, option2, option3:typing.Optional[str], option4:typing.Optional[str], option5:typing.Optional[str], option6:typing.Optional[str], option7:typing.Optional[str], option8:typing.Optional[str]):
    """Create a poll. e.g. /poll title option1 option2 option3 ..."""
    await ctx.response.defer()
    options = [option1, option2,option3,option4,option5,option6,option7,option8]
    reactions = ["\U0001f1e6", "\U0001f1e7", "\U0001f1e8", "\U0001f1e9", "\U0001f1ea", "\U0001f1eb", "\U0001f1ec", "\U0001f1ed"][:len(options)]
    embed = discord.Embed(title=title, color=discord.Color.blue())
    for i in range(len(options)):
        if options[i] == None:
           break
        embed.add_field(name=f"{reactions[i]} {options[i]}", value="\u200b", inline=False)
    message = await ctx.send(embed=embed)
    for i in reactions:
        if options[reactions.index(i)] == None:
           break
        await message.add_reaction(i)
    await ctx.respond("Done",ephemeral=True)

tick="✅"
# tick="✔️"
cross="❌"
@bot.slash_command(name="yes-no-poll")
async def yes_no_poll(ctx, title, description=''):
    """
    Create a Yes/No Poll. e.g. - /poll [title] [description]
    """
    await ctx.response.defer()
    
    if description == '':
        embed = discord.Embed(title=title, description=description, color=0x00ff00)
    else:
        embed = discord.Embed(title=title, color=0x00ff00)
    embed.set_author(name=ctx.author.nick, icon_url=ctx.author.avatar.url)
    message = await ctx.send(embed=embed)

    await message.add_reaction(tick)
    await message.add_reaction(cross)
    await ctx.respond("Done!", ephemeral=True)

client=bot

# Coin flip command
@client.command(name='coinflip')
async def coinflip(ctx):
    """Flip a coin. e.g. /coinflip"""
    await ctx.response.defer()
    outcomes = ['Heads', 'Tails']
    response = 'The coin landed on ' + random.choice(outcomes) + '!'
    await ctx.respond(response)

from thefuzz import fuzz 

# Eight ball command
@client.command(name='8ball')
async def eight_ball(ctx, question):
    """Ask a question. e.g. /8ball [question]"""
    await ctx.response.defer()
    responses = ['It is certain.', 'It is decidedly so.', 'Without a doubt.', 'Yes – definitely.', 'You may rely on it.', 'As I see it, yes.', 'Most likely.', 'Outlook good.', 'Yes.', 'Signs point to yes.', 'Reply hazy, try again.', 'Ask again later.', 'Better not tell you now.', 'Cannot predict now.', 'Concentrate and ask again.', 'Don\'t count on it.', 'Outlook not so good.', 'My sources say no.', 'Very doubtful.']
    response = random.choice(responses)
    if fuzz.token_set_ratio(question,"are you smart?")>70:
        await ctx.respond("Yes!")
        return
    if fuzz.token_set_ratio(question,"are you dumb?")>70:
        await ctx.respond("No!")
        return
    if fuzz.token_set_ratio(question,"am i smart?")>70:
        await ctx.respond("Yes! Well maybe not, idk, I'm just a Bot.")
        return
    if fuzz.token_set_ratio(question,"am i dumb?")>70:
        await ctx.respond("No! Well maybe, idk, I'm just a Bot.")
        return
    await ctx.respond(response)

# Role info command
@client.command(name='roleinfo')
async def roleinfo(ctx, role: discord.Role):
    """Show information about a role. e.g. /roleinfo [role]"""
    await ctx.response.defer()
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
    await ctx.response.defer()
    num = random.randint(int(min_num), int(max_num))
    await ctx.respond(num)

# Serverinfo command
@bot.slash_command(name='serverinfo', description='Displays information about the server')
async def serverinfo(ctx):
    server = ctx.guild
    roles = len(server.roles)
    emojis = len(server.emojis)
    channels = len(server.channels)
    members = server.member_count
    created_at = server.created_at.strftime('%Y-%m-%d %H:%M:%S')
    #region = str(server.region).capitalize()
    text_channels = len(server.text_channels)
    voice_channels = len(server.voice_channels)
    embed = discord.Embed(title=server.name, description=server.id, color=0x00ff00)
    embed.add_field(name="Owner", value=server.owner, inline=False)
    #embed.add_field(name="Region", value=region, inline=False)
    embed.add_field(name="Members", value=members, inline=False)
    embed.add_field(name="Created At", value=created_at, inline=False)
    embed.add_field(name="Channels", value=channels, inline=False)
    embed.add_field(name="Text Channels", value=text_channels, inline=True)
    embed.add_field(name="Voice Channels", value=voice_channels, inline=True)
    embed.add_field(name="Roles", value=roles, inline=False)
    embed.add_field(name="Emojis", value=emojis, inline=False)
    await ctx.respond(embed=embed)

# Avatar command
@client.command(name='avatar')
async def avatar(ctx, user: typing.Optional[discord.Member]):
    """Shows a user's avatar, if username not supplied, shows your own avatar. e.g. /avatar [user]"""
    await ctx.response.defer()
    user = user or ctx.author
    embed = discord.Embed(title=user.name + '\'s avatar')
    embed.set_image(url=user.avatar.url)
    await ctx.respond(embed=embed)

# Unban command
@client.command(name='unban')
@commands.has_permissions(ban_members=True)
async def unban(ctx, member:discord.Member):
    """Unbans a user. e.g. /unban [member]"""
    await ctx.response.defer()
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
async def ud(ctx, term:str):
    """Search the meaning of any word. e.g. /ud [term]"""
    await ctx.response.defer()
    term = term.lower().replace(" ", "+")
    url = f"https://www.urbandictionary.com/define.php?term={term}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            soup = BeautifulSoup(await response.text(), 'html.parser')
            meaning = soup.find('div', {'class': 'meaning'}).text
            example = soup.find('div', {'class': 'example'}).text
            await ctx.respond(f"**{term.capitalize()}**: {meaning}\n\n*Example: {example}*")

import requests

# Cat command
@client.command(name='cat', help='Shows pictures of cats')
async def cat(ctx):
    """
    This command retrieves a random cat picture from TheCatAPI and sends it in the chat. Usage: /cat
    """
    await ctx.response.defer()
    response = requests.get('https://api.thecatapi.com/v1/images/search').json()
    if len(response) > 0 and 'url' in response[0]:
        cat_url = response[0]['url']
        await ctx.respond(cat_url)
    else:
        await ctx.respond("Could not find any cat pictures.")

# Dog command
@client.command(name='dog', help='Shows pictures of dogs')
async def dog(ctx):
    """
    This command retrieves a random dog picture from the Dog API and sends it in the chat. Usage: /dog
    """
    await ctx.response.defer()
    response = requests.get('https://dog.ceo/api/breeds/image/random').json()
    if 'message' in response:
        dog_url = response['message']
        await ctx.respond(dog_url)
    else:
        await ctx.respond("Could not find any dog pictures.")

# Joke command
@client.command(name='joke', help='Shows a random joke')
async def joke(ctx):
    """
    This command retrieves a random joke from Official Joke API and sends it in the chat. Usage: /joke
    """
    await ctx.response.defer()
    response = requests.get('https://official-joke-api.appspot.com/jokes/random').json()
    if 'setup' in response and 'punchline' in response:
        joke_setup = response['setup']
        joke_punchline = response['punchline']
        await ctx.respond(f"{joke_setup}\n\n{joke_punchline}")
    else:
        await ctx.respond("Could not find any jokes.")

@client.command(name='quote')
async def quote(ctx):
    """Shows a random quote. e.g. /quote"""
    await ctx.response.defer()
    response = requests.get('https://zenquotes.io/api/random').json()[0]
    quote = f"{response['q']} - {response['a']}"
    await ctx.respond(quote)

import google_translator

@client.command(name='translate')
async def translate(ctx, source_lang: str, target_lang: str, *, text: str):
    """Translates a given text from one language to another. e.g. /translate en hi Hello"""
    await ctx.response.defer()
    try:
        translator = google_translator()
        translation = translator.translate(text, lang_src=source_lang, lang_tgt=target_lang)
        await ctx.respond(f"Translated text: {translation}")
    except ValueError as e:
        await ctx.respond(f"Sorry, I could not translate the given text. Please check the source and target languages.")

@client.command(name='numberfact')
async def number_fact(ctx, number: int):
    """Shows a random fact about a given number. e.g. /numberfact 42"""
    await ctx.response.defer()
    response = requests.get(f'http://numbersapi.com/{number}/trivia').text
    await ctx.respond(response)

import json
from datetime import datetime as dtime
#from datetime import datetime

@bot.slash_command(name="warn")
@commands.has_role("Moderator")
async def warn(ctx, member: discord.Member, reason: str):
    """
    Warns a member. Usage: /warn @member [reason]
    """
    await ctx.response.defer()
    embed = discord.Embed(title="⚠️Warning!⚠️", description=f"You have been warned for {reason}.\nPlease follow the rules.", color=discord.Color.red())
    embed.set_author(name=f"{ctx.author}", icon_url=ctx.author.avatar.url)
    embed.set_footer(text="Thank you for being a part of the Delhi Public School Server.")
    
    try:
        await member.send(embed=embed)
    except discord.Forbidden:
        await ctx.respond("Failed to send a warning message. The user may have their DMs disabled.", ephemeral=True)
        return
    now = dtime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    warning = {"member_id": str(member.id), "member_name": member.display_name, "moderator_id": str(ctx.author.id), "moderator_name": ctx.author.display_name, "reason": reason, "timestamp": timestamp}
    
    with open("warnings.json", "r") as f:
        warnings = json.load(f)
    
    if str(member.id) not in warnings:
        warnings[str(member.id)] = []
    
    warnings[str(member.id)].append(warning)
    
    with open("warnings.json", "w") as f:
        json.dump(warnings, f)
    
    await ctx.respond(f"{member.mention} has been warned.",ephemeral=True)
    
@bot.slash_command(name="warnings")
async def warnings(ctx, member: discord.Member = None):
    """Shows warnings for a member. Usage: /warnings [member]"""
    await ctx.response.defer()
    if not member:
        member = ctx.author
    with open("warnings.json", "r") as f:
        data = json.load(f)
    if str(member.id) not in data:
        await ctx.respond("No warnings found for this member.")
        return
    warnings = data[str(member.id)]
    embed = discord.Embed(title=f"Warnings for {member.display_name}", color=discord.Color.red())
    for warning in warnings:
        moderator = await bot.fetch_user(warning["moderator"])
        embed.add_field(name=f"Warning from {moderator.display_name}", value=f"Reason: {warning['reason']} - Time: {warning['timestamp']}")
    await ctx.send(embed=embed)

@bot.slash_command(name="guild-warnings")
@commands.has_role("Moderator")
async def guild_warnings(ctx):
    """Displays all warnings given in the server. Usage: /guild-warnings"""
    await ctx.response.defer()
    with open("warnings.json", "r") as f:
        warnings = json.load(f)
    if not warnings:
        await ctx.respond("No warnings have been given in this server.", ephemeral=True)
        return
    embed = discord.Embed(title="Server Warnings", color=discord.Color.red())
    for member_id, member_warnings in warnings.items():
        member = ctx.guild.get_member(int(member_id))
        if not member:
            continue
        warnings_list = "\n".join(f"• {warning['reason']}" for warning in member_warnings)
        embed.add_field(name=member.display_name, value=warnings_list, inline=False)
    await ctx.respond(embed=embed)

@client.command(name='slowmode')
@commands.has_permissions(manage_channels=True)
async def slowmode(ctx, delay: int):
    """Sets the slowmode delay for the channel. Usage: /slowmode <delay in seconds>"""
    if delay < 0:
        await ctx.respond('Delay cannot be negative.',ephemeral=True)
    elif delay > 21600:
        await ctx.respond('Delay cannot be greater than 6 hours.',ephemeral=True)
    else:
        await ctx.channel.edit(slowmode_delay=delay)
        await ctx.respond(f'Successfully set the slowmode delay of this channel to {delay} seconds.',ephemeral=True)

# Quote command
@bot.slash_command(name="quote-msg")
async def quote_message(ctx, message_id: int):
    """
    Quotes a message. Usage: /quote-message <message_id>
    """
    message_id=int(message_id)
    msg=await ctx.channel.fetch_message(message_id)
    embed=discord.Embed(description=msg.content, color=discord.Color.blurple())
    embed.set_author(name=msg.author.display_name, icon_url=msg.author.avatar.url)
    embed.set_footer(text=f"Message ID: {msg.id}")
    await ctx.respond(embed=embed)

import datetime, psutil

# Uptime command
@bot.slash_command(name='uptime', description='Displays the bot uptime')
async def uptime(ctx):
    uptime = datetime.datetime.now() - bot.boot_time
    hours, remainder = divmod(int(uptime.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    days, hours = divmod(hours, 24)
    await ctx.respond(f"Uptime: {days}d {hours}h {minutes}m {seconds}s",ephemeral=True)


# CPU command
@bot.slash_command(name='cpu', description='Displays CPU usage')
async def cpu(ctx):
    cpu_percent = psutil.cpu_percent()
    await ctx.respond(f'CPU Usage: {cpu_percent}%', ephemeral=True)

# Memory command
@bot.slash_command(name='memory', description='Displays memory usage')
async def memory(ctx):
    memory = psutil.virtual_memory()
    total = round(memory.total/(1024*1024), 2)
    used = round(memory.used/(1024*1024), 2)
    percent = memory.percent
    await ctx.respond(f'Memory Usage: {used} MB/{total} MB ({percent}%)',ephemeral=True)

@client.command(name='timer')
async def timer(ctx, seconds):
    """Sets a timer for the given number of seconds. e.g. /timer 60"""
    #await ctx.response.defer()
    try:
        seconds = int(seconds)
    except ValueError:
        await ctx.response.send_message("Please provide a valid number of seconds.")
        return
    if seconds < 1 or seconds > 3600:
        await ctx.response.send_message("Please provide a number of seconds between 1 and 3600.")
        return
    timer_embed = discord.Embed(
        title="⏰ Timer", description=f"Timer set for {seconds} seconds.", color=discord.Color.blue())
    timer_message = await ctx.send(embed=timer_embed)
    await ctx.respond("Done!",ephemeral=True)
    while seconds > 0:
        timer_embed.description = f"Time remaining: {seconds} seconds."
        await timer_message.edit(embed=timer_embed)
        await asyncio.sleep(1)
        seconds -= 1
        await timer_message.edit(embed=timer_embed)
    timer_embed.description = "Time's up!"
    await timer_message.edit(embed=timer_embed)

# Run the bot
bot.run(bot_token)
