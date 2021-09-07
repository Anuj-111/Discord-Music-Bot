
import os
from timer import(
  gtimer,
  Timer
)

import discord
from discord.ext import commands


_admins = [278646990777221120]



bot = commands.Bot(command_prefix = "!",case_insensitive =True,activity = discord.Game(name="Music for your ❤️"))
bot.remove_command('help')

@bot.event
async def on_ready():
  gtimer = Timer(bot)
  print(type(gtimer))
  print("Bot online")
  

  

@bot.event
async def on_command_error(ctx, error):
  if isinstance(error, commands.CommandNotFound):# or isinstance(error,commands.CommandInvokeError):
      pass
  else:
      raise error

@bot.command()
async def load(ctx,extension):
  if ctx.author.id in _admins:
    bot.load_extension(f'cogs.{extension}')
    await ctx.send("{} loaded".format(extension))
  
@bot.command()
async def unload(ctx,extension):
  if ctx.author.id in _admins:
    bot.unload_extension(f'cogs.{extension}')
    await ctx.send("{} unloaded".format(extension))
  
@bot.command()
async def reload(ctx,extension):
  if ctx.author.id in _admins:
    bot.unload_extension(f'cogs.{extension}')
    bot.load_extension(f'cogs.{extension}')
    await ctx.send("{} reloaded".format(extension))


for filename in os.listdir("./cogs"):
  if filename.endswith(".py"):
    bot.load_extension(f"cogs.{filename[:-3]}")



bot.run("ODcwNDE5ODkwMjI4NTY4MTE1.YQMfsQ.UvCIVgaeYkmm99zkSlgWjCV0aKM")
