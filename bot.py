
import os
from timer import(
  gtimer
)

import discord
from discord.ext import commands


_admins = [278646990777221120]



bot = commands.Bot(command_prefix = "!",case_insensitive =True,activity = discord.Game(name="Music for your ❤️"))
bot.remove_command('help')

@bot.event
async def on_ready():
  gtimer.setup(bot)
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
    bot.load_extension(f'DiscordFiles.{extension}')
    await ctx.send("{} loaded".format(extension))
  
@bot.command()
async def unload(ctx,extension):
  if ctx.author.id in _admins:
    bot.unload_extension(f'DiscordFiles.{extension}')
    await ctx.send("{} unloaded".format(extension))
  
@bot.command()
async def reload(ctx,extension):
  if ctx.author.id in _admins:
    bot.unload_extension(f'DiscordFiles.{extension}')
    bot.load_extension(f'DiscordFiles.{extension}')
    await ctx.send("{} reloaded".format(extension))


for filename in os.listdir("./DiscordFiles"):
  if filename.endswith(".py"):
    bot.load_extension(f"DiscordFiles.{filename[:-3]}")



bot.run("ODcwNDE5ODkwMjI4NTY4MTE1.YQMfsQ.UvCIVgaeYkmm99zkSlgWjCV0aKM")
