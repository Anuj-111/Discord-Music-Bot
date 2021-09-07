"""Music.py encapsulates all the basic commands in a basic voice bot"""
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
    serverId = ctx.guild.id
    if serverId in tracks:
       del tracks[serverId]
       del s_opts[serverId][1][serverId]
    if voice and voice.is_connected():
      if len(voice.channel.members) == 1 or ctx.author.voice and ctx.author.voice.channel == voice.channel:
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
    
    serverId = ctx.guild.id
    playlist = True if 'list=' in request else False #Need to evaluate early to send user this check before first song is played
    

    if isinstance(ctx.channel, discord.DMChannel): #No point of putting this in another function
      await ctx.send(f'Use {self.bot.user.name} in a server please.')
      return None

    if not (x := await Events.checkconditions(self.bot,ctx)) and request is None: #Allow the user to summon bot(join) without making a request
      return
    

    await ctx.send(f"`Attempting to request: {request}`")
    if (video:= await FetchVideo().get_singlevideo(str(ctx.author),request,search = s_opts[serverId][1]['search'])) is None: 
        await ctx.send("Error occured while fetching video.")
        return
    
    request = video.url

    
    tracks[serverId].append(video)
    message = await Events.addedtoqueue(ctx,video,playlist,len(tracks[serverId]),thumbnail=video.thumbnail)
    await ctx.send(embed=message)

    if not serverId in player:
      playmusic(ctx,serverId) #Plays the song if nothing is in the queue



    if playlist is True: #Playlist and first song is split because playlist takes time to load. We'll let the first song play while playlist song queues up. 

        if (videos:= await FetchVideo().get_playlist(str(ctx.author),request)) is None: 
          await ctx.send("Error occured while fetching playlist")
          return
        
        tracks[serverId].extend(videos)


  @commands.command(aliases=['ps'],pass_context = True)
  async def playskip(self,ctx,*,request=None)-> None:

    serverId = ctx.guild.id
    playlist = True if 'list=' in request else False #Need to evaluate early to send user this check before first song is played
    

    if isinstance(ctx.channel, discord.DMChannel):
      await ctx.send(f'Use {self.bot.user.name} in a server please.')
      return None

    if not (x := await Events.checkconditions(self.bot,ctx)) and request is None: #Allow the user to summon bot(join) without making a request
      return

    await ctx.send(f"`Attempting to request: {request}`")
    if (video:= await FetchVideo().get_singlevideo(str(ctx.author),request,search = s_opts[serverId][1]['search'])) is None: 
      await ctx.send("Error occured while fetching video.")
      return

    request = video.url
  
    tracks[serverId].insert(0,video)
    message = await Events.addedtoqueue(ctx,video,playlist,0,thumbnail=video.thumbnail)
    await ctx.send(embed=message)

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

    serverId = ctx.guild.id
    playlist = True if 'list=' in request else False #Need to evaluate early to send user this check before first song is played
    search = "auto"#s_opts[serverId][1]['search']

    if isinstance(ctx.channel, discord.DMChannel):
      await ctx.send(f'Use {self.bot.user.name} in a server please.')
      return None

    if not (x := await Events.checkconditions(self.bot,ctx)) and request is None: #Allow the user to summon bot(join) without making a request
      return

    await ctx.send(f"`Attempting to request: {request}`")
    if (video:= await FetchVideo().get_singlevideo(str(ctx.author),request,search=s_opts[serverId][1]['search'])) is None: 
      await ctx.send("Error occured while fetching video.")
      return
    

    request = video.url
    tracks[serverId].insert(0,video)

    if serverId in player:
      tracks[serverId].insert(0,video)
      message = await Events.addedtoqueue(ctx,video,playlist,1,thumbnail=video.thumbnail)
      await ctx.send(embed=message)
    else:
      message = await Events.addedtoqueue(ctx,video,playlist,0,thumbnail=video.thumbnail)
      await ctx.send(embed=message)
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
      else:
        return None


def setup(bot):
  bot.add_cog(Music(bot))
  