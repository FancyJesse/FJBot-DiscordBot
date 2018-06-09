#!/usr/bin/env python3
from datetime import datetime
import sys, traceback
import asyncio

from discord.ext import commands
import discord

from utils.dbhandler import DBHandler
from utils import credentials, checks


startup_extensions = [
	'cogs.admin'
	,'cogs.member'
	,'cogs.wwe'
	,'cogs.twitter'
	,'cogs.chatango'
]
description='FJBot is a Discord Bot written in Python by FancyJesse'
bot = commands.Bot(command_prefix='!', description=description)

channel_debug = discord.Object(id=credentials.discord['channel']['debug'])

current_match = {}

def confirm_check(m):
	return m.content.upper() in ['Y','N']

# bot events
@bot.event
async def on_command_error(error, ctx):
	if 'is not found' in str(error):
		return
	if ctx.message.channel.is_private:
		pass
	else:
		owner = ctx.message.server.get_member(credentials.discord['owner_id'])
		if owner:
			await bot.send_message(owner, '```{}\n[#{}] {}: {}```'.format(error, ctx.message.channel, ctx.message.author, ctx.message.content))
		raise error		

@bot.event
async def on_member_join(member):
	role = discord.utils.get(member.server.roles, name=credentials.discord['role']['default'])
	await bot.add_roles(member, role)
	await bot.send_message(channel_general, 'Welcome to {}, {}! Say hi!'.format(member.server.name, member.mention))

@bot.event
async def on_message(message):
	if message.author.bot or not message.content.startswith('!'):
		return
	res = bot.dbhandler.discord_command(message.content.split(' ')[0])
	if res:
		await bot.send_message(message.channel, res['response'].replace('@mention', message.author.mention))
		bot.dbhandler.discord_command_cnt(res['id'])
	else:
		tokens = message.content.split(' ')
		message.content = '{} {}'.format(tokens[0].lower(), ' '.join(tokens[1:]))
		await bot.process_commands(message)

@bot.event
async def on_ready():
	bot.start_dt = datetime.now()
	print('[{}] Discord: Logged in as {}({})'.format(bot.start_dt, bot.user.name, bot.user.id))
		
if __name__ == '__main__':
	try:
		bot.dbhandler = DBHandler()
		for extension in startup_extensions:
			try:
				bot.load_extension(extension)
			except Exception as e:
				print(f'Failed to load extension {extension}.', file=sys.stderr)
				traceback.print_exc()
		bot.run(credentials.discord['access_token'])
	except KeyboardInterrupt:
		pass
	finally:
		bot.logout()
		print('[{}] FJBOT: END'.format(datetime.now()))
		print('Total Tasks: {}'.format(len(asyncio.Task.all_tasks())))
		print('Active Tasks: {}'.format(len([t for t in asyncio.Task.all_tasks() if not t.done()])))
