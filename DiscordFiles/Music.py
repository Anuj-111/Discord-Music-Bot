"""Music.py encapsulates all the basic commands for a basic voice bot."""

from source import (
  playmusic,
  player
)

from storage import (
tracks,
s_opts
)

from timer import gtimer
from botutils.fetchvideo import FetchVideo
from DiscordFiles.Events import Events

import time

import discord
from discord.ext import commands


class Music(commands.Cog):
  def __init__(self,bot):
    self.bot = bot


  @commands.command(aliases=['c','j','connect','summon'],pass_context=True)
  async def join(self,ctx):
    voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
    if isinstance(ctx.channel, discord.DMChannel):
      await ctx.send(f'Use {self.bot.user.name} in a server please.')
      return None
    if not(x := await Events.checkconditions(self.bot,ctx)):
      return

  @commands.command(aliases=['leav','dc','leave','stop'],pass_context = True)
  async def disconnect(self,ctx):
    voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
    if isinstance(ctx.channel, discord.DMChannel):
      await ctx.send(f'Use {self.bot.user.name} in a server please.')
      return None

    if voice and voice.is_connected():
      if len(voice.channel.members) == 1 or ctx.author.voice and ctx.author.voice.channel == voice.channel:
        serverId = ctx.guild.id
        if serverId in tracks:
          del tracks[serverId]
          del s_opts[serverId]
      
        if serverId in player:
          if player[serverId].loop == True:
            player[serverId].set_loop(False)
          voice.stop()
        voice.cleanup()
        await voice.disconnect()
        gtimer.delentry(ctx.guild.id)   
      else:
        await ctx.send("**User isn't connected to bot's voice channel**")
    else:
      await ctx.send("**Bot isn't connected**")


  @commands.command(aliases=['p','pla'],pass_context = True)
  async def play(self,ctx,*,request=None)->None:
    """The model of all the play functions are as follows: 1)Get first video. 2)Play or queue first video. 3)Get Playlist if any. 4)Queue playlist. The playmusic function
    is recursive. Hence, when you see voice.stop() instead of playmusic(), it is indicating that the song is skipped and next song will be queue."""
  
    if isinstance(ctx.channel, discord.DMChannel): #No point of putting this in another function
      await ctx.send(f'Use {self.bot.user.name} in a server please.')
      return None

    if not (x := await Events.checkconditions(self.bot,ctx)) or request is None: #Allow the user to summon bot(join) without making a request
      return
    


    serverId = ctx.guild.id
    playlist = True if 'list=' in request else False #Need to evaluate early to send user this check before first song is played
    

    if (video:= await FetchVideo().get_singlevideo(ctx.channel,str(ctx.author),request,search = s_opts[serverId][1]['search'])) is None: 
        await ctx.send("Error occured while fetching video.")
        return

    

    message = await Events.addedtoqueue(ctx,video,playlist,len(tracks[serverId]),thumbnail=video.thumbnail)
    await ctx.send(embed=message)
    tracks[serverId].append(video)

    if not serverId in player:
      playmusic(ctx,serverId) #Plays the song if nothing is in the queue



    if playlist is True: #Playlist and first song is split because playlist takes time to load. We'll let the first song play while playlist song queues up. 

        if (videos:= await FetchVideo().get_playlist(str(ctx.author),request)) is None: 
          await ctx.send("Error occured while fetching playlist")
          return
        
        tracks[serverId].extend(videos)


  @commands.command(aliases=['ps'],pass_context = True)
  async def playskip(self,ctx,*,request=None)-> None:
    

    if isinstance(ctx.channel, discord.DMChannel):
      await ctx.send(f'Use {self.bot.user.name} in a server please.')
      return None

    if not (x := await Events.checkconditions(self.bot,ctx)) or request is None: #Allow the user to summon bot(join) without making a request
      return None


    serverId = ctx.guild.id
    playlist = True if 'list=' in request else False #Need to evaluate early to send user this check before first song is played

    
    if (video:= await FetchVideo().get_singlevideo(ctx.channel,str(ctx.author),request,search = s_opts[serverId][1]['search'])) is None: 
      await ctx.send("Error occured while fetching video.")
      return None

  
    
    message = await Events.addedtoqueue(ctx,video,playlist,0,thumbnail=video.thumbnail)
   
    tracks[serverId].insert(0,video)

    if serverId in player:
      if player[serverId].loop == True:
        player[serverId].set_loop(False)

      voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
      voice.stop() #Playmusic uses a recursive function. Stopping plays next track
      await ctx.send("Song has been skipped")
    else:
      playmusic(ctx,serverId) #If no song in playlist, init playmusic function
    
      
    if playlist is True:
      if (videos:= await FetchVideo().get_playlist(str(ctx.author),request)) is None: 
        await ctx.send("Error occured while fetching playlist")
        return

      
      for video in reversed(videos):
        tracks[serverId].insert(0,video)
    
  @commands.command(aliases=['pt'],pass_context = True)
  async def playtop(self,ctx,*,request:str=None)->None:


    if isinstance(ctx.channel, discord.DMChannel):
      await ctx.send(f'Use {self.bot.user.name} in a server please.')
      return None

    if not (x := await Events.checkconditions(self.bot,ctx)) or request is None: #Allow the user to summon bot(join) without making a request
      return

    
    serverId = ctx.guild.id
    playlist = True if 'list=' in request else False #Need to evaluate early to send user this check before first song is played


    
    if (video:= await FetchVideo().get_singlevideo(ctx.channel,str(ctx.author),request,search=s_opts[serverId][1]['search'])) is None: 
      await ctx.send("Error occured while fetching video.")
      return
    

    if serverId in player:
      tracks[serverId].insert(0,video)
      message = await Events.addedtoqueue(ctx,video,playlist,1,thumbnail=video.thumbnail)
      await ctx.send(embed=message)
      tracks[serverId].insert(0,video)
    else:
      message = await Events.addedtoqueue(ctx,video,playlist,0,thumbnail=video.thumbnail)
      await ctx.send(embed=message)
      tracks[serverId].insert(0,video)
      playmusic(ctx,serverId)
    
    if playlist is True:
      if (videos:= await FetchVideo().get_playlist(str(ctx.author),request)) is None: 
        await ctx.send("Error occured while fetching playlist")
        return
   
      if serverId in tracks and tracks[serverId]:
        if tracks[serverId][0].id == video.id:
          firstsong = tracks[serverId].pop(0) 
      else:
        firstsong = None
     
      
      for video in reversed(videos):
        tracks[serverId].insert(0,video) 
      if firstsong:
        tracks[serverId].insert(0,firstsong) 
      

  @commands.command(aliases=['fs','skip'],pass_context = True)
  async def forceskip(self,ctx):
    if isinstance(ctx.channel, discord.DMChannel):
      await ctx.send(f'Use {self.bot.user.name} in a server please.')
      return None
    voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
    if voice and voice.is_connected() and ctx.author.voice and ctx.author.voice.channel == voice.channel:
      serverId = ctx.guild.id
      if serverId in player:
        if player[serverId].loop == True:
          player[serverId].set_loop(False)
        if voice.is_playing() or voice.is_paused():
          voice.stop()
        await ctx.send("```Song has been skipped⏭️```")
    else:
      await ctx.send("User or bot not connected to voice channel")

  @commands.command(aliases=['resum'],pass_context = True)
  async def resume(self,ctx):
    if isinstance(ctx.channel, discord.DMChannel):
      await ctx.send(f'Use {self.bot.user.name} in a server please.')
      return None
    voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

    if voice and voice.is_paused() and ctx.author.voice and ctx.author.voice.channel == voice.channel:
      serverId = ctx.guild.id
      player[serverId].set_pausetime(time.time())
      voice.resume()
      await ctx.send("Music has been resumed!")
    else:
      await ctx.send("No music paused or user not connected to vc")
    
  @commands.command(aliases=['paus'],pass_context = True)
  async def pause(self,ctx):
     voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
     if isinstance(ctx.channel, discord.DMChannel):
        await ctx.send(f'Use {self.bot.user.name} in a server please.')
        return None

     if voice and voice.is_playing() and ctx.author.voice and ctx.author.voice.channel == voice.channel:
       serverId = ctx.guild.id
       player[serverId].set_pausetime(time.time(),pause=True)
       voice.pause()
       await ctx.send("Music has been paused")
     else:
       await ctx.send("No music playing or user not connected to vc")
    



def setup(bot):
  bot.add_cog(Music(bot))
  