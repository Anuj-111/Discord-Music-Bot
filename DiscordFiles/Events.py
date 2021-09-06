from storage import(
    s_opts,
    tracks,
    timer
)
from source import player
from timer import gtimer
from botutils.extra import (
    toHMS,
    durationtillplay
    )

from datetime import datetime
import asyncio
import random

import discord
from discord import commands

class Events(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        now = datetime.now()
        await asyncio.sleep(60-now.second)
        gtimer.checktimer.start()
  
    @commands.Cog.listener()
    async def on_voice_state_update(self,ctx,before,after):
        if before.channel and not after.channel:
            voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice and not voice.is_connected():
            voice.cleanup()
            if ctx.guild.id in tracks:
                del tracks[ctx.guild.id]
                del s_opts[ctx.guild.id]
            if ctx.guild.id in player:
                if player[ctx.guild.id].loop:
                    player[ctx.guild.id].set_loop(False)
                gtimer.delentry(ctx.guild.id)   
        elif voice and len(voice.channel.members) == 1:
            if ctx.guild.id in player:
                if player[ctx.guild.id].loop:
                    player[ctx.guild.id].set_loop(False)
                gtimer.setentry(ctx.guild.id,2)
    
    async def checkconditions(self,ctx): 
      """Connection event for the bot"""

      channel = None
      try:
        if ctx.author.voice.channel:
          channel = ctx.author.voice.channel
      except Exception:
        await ctx.send("**User is not in voice Channel**")
        return False
      voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
      if voice and voice.is_connected():
        if voice.channel.id != channel.id and not voice.channel.members:
          await voice.move_to(channel)
        else:
          if voice.channel.id != channel.id:
            await ctx.send("**Bot already connected to different channel**")
      else:
        try:
          serverId = ctx.guild.id
          await channel.connect(timeout=60.0,reconnect=True)
          tracks[serverId] = []
          s_opts[serverId] = ["",{},0]
          s_opts[serverId][1]['volume'] = 0.75
          s_opts[serverId][1]['temp'] = dict()
          gtimer.setentry(ctx.guild.id,1)
        except asyncio.TimeoutError:
          await ctx.send('bot has disconnected')
      return True


    async def addedtoqueue(self,ctx,data,playlist,position: int,thumbnail=None):
     serverId = ctx.guild.id
     if position == 0:
       position = "Currently Playing"
     else:
       position = str(position)
     if isinstance(data.duration,int) and data.duration != 0:
       duration = toHMS(data.duration)
     else:
       duration = "Livestream"
     if position != "Currently Playing":
       dtp = toHMS(durationtillplay(serverId,int(position))) 
     else:
       dtp = "Now"
     if not playlist:
       notif = discord.Embed(title="Song Added to queue",description="**["+data.title+"]("+data.url+")**",colour= random.randint(0, 0xffffff))
       notif.add_field(name="Till Played",value=dtp if not data.ls and dtp else "livestream" ,inline=True)
       notif.add_field(name="Song Duration",value=duration if not data.ls else "livestream",inline=True)
       notif.add_field(name="Position",value=position,inline=False)
       if thumbnail:
         notif.set_thumbnail(url=thumbnail)
     else:
       notif = discord.Embed(title="Playlist added/being added to queue",description="**["+data.title+"]("+data.url+")**",colour= random.randint(0, 0xffffff))
       notif.add_field(name="**Till Played**",value="`"+dtp+"`",inline=True)
       notif.add_field(name="**Song Duration**",value="`"+duration+"`",inline=True)
       notif.add_field(name="**Position**",value=position,inline=False)
       if thumbnail:
         notif.set_thumbnail(url=thumbnail)
       notif.set_footer(text="`Playlist info may take some time.`")
     await ctx.send(embed=notif)
                    

        



def setup(bot):
  bot.add_cog(Events(bot))