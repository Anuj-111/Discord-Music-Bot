import os, json,shutil
import time
import random
import asyncio
import yt_dlp
from yt_dlp import DownloadError
import discord
from discord.channel import VoiceChannel
from discord.ext import commands,tasks
from youtube_search import YoutubeSearch 
import datetime

from discord.ext import commands
import lyricsgenius
genius = lyricsgenius.Genius("6U9CZ_uiDd6jCu7aLHD1Muc5JfDzy1FOueTIx4hrU4gHVxSwFBvHYEjLfWebxz7o")

class SessionFinished(Exception):
  pass

db = dict()
s_opts = dict()

class Timer():
    def __init__(self,bot):
        self.bot = bot
        self.check = dict()
        self.check2 = dict()

    def checkentry(self,serverId):
      in_check = False
      for key in self.check:
          if serverId in self.check[key]:
            in_check = True
            break
      return in_check
        
    def delentry(self,serverId):
      for key in self.check:
          if serverId in self.check[key]:
              self.check[key].remove(serverId)


    @tasks.loop(seconds=60) 
    async def checktimer(self):
        tme = time.time()
        now = datetime.datetime.now()
        if self.check:
          if str(now.minute) in self.check:
              for i in self.check[str(now.minute)]:
                if i in s_opts:
                  del s_opts[i]
                guild = await self.bot.fetch_guild(i)
                voice = discord.utils.get(self.bot.voice_clients, guild=guild)
                if voice:
                  voice.cleanup()
                  await voice.disconnect()
              del self.check[str(now.minute)]
        if self.check2:
          if str(now.minute) in self.check2:
            for serverId in self.check2[str(now.minute)]:
              guild = await self.bot.fetch_guild(serverId)
              voice = discord.utils.get(self.bot.voice_clients, guild=guild)
              if voice and len(voice.channel.members) == 1:
                if serverId in db:
                  del db[serverId]
                  del s_opts[serverId]
      
                voice.stop()
                voice.cleanup()
                await voice.disconnect()
            del self.check2[str(now.minute)]
              
                    
  
    def setentry(self,serverId,entryid):
      if entryid == 1:
        now = datetime.datetime.now()
        minute = now.minute + 3 if now.second < 30 else now.minute + 4
        if minute >= 60:
            minute -= 60
        if minute in self.check:
            self.check[str(minute)].add(serverId) 
        else:
            self.check[str(minute)] = set({serverId})
      elif entryid == 2:
        now = datetime.datetime.now()
        minute = now.minute + 3 if now.second < 30 else now.minute + 4
        if minute >= 60:
            minute -= 60
        if minute in self.check2:
            self.check2[str(minute)].add(serverId) 
        else:
            self.check2[str(minute)] = set({serverId})

    

      
class Source(discord.PCMVolumeTransformer):
    def __init__(self, source,*,data,timeq=None,loop=False,ls=False,volume=0.25):
        super().__init__(source, volume)
        self.data = data
        self.id = data.get('id',None)
        self.url = data.get('url',None)
        self.title = data.get('title',None)
        self.duration = data.get('duration',None) 
        self.thumbnail = data.get('thumbnail',None)
        self.channel = data.get('channel',None)
        self.tags = data.get('tags',None)
        self.author = data.get('author',None)
        self.ls = data.get('ls',None)
        self.timeq = timeq
        self.loop = loop
        self.repeat = False
        

    async def breakdownurl(self,url,serverId,Loop=None,npl=True):
        ytdl_format_options = {
        'format': 'bestaudio/best',
        'restrictfilenames': True,
        'noplaylist': npl,
        'playlistend':25,
        'verbose': False,
        'quiet': True, 
        'default_search': 'auto',
        'nocheckcertificate': True,
        'ignoreerrors': True,
        'no_warnings': False,
        'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
        }
        ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

        try:
          loop = Loop or asyncio.get_event_loop()
          data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
          return data
        except Exception:
          return None

    def set_loop(self,var):
      self.loop = var

    def set_repeat(self,var):
      self.repeat = var

    def set_pausetime(self,tme,pause=False):
      if pause:
        self.timeq[2] = tme
      if not pause:
        self.timeq[1] += int(tme-self.timeq[2])
        self.timeq[2] = 0 


    @classmethod
    def streamvideo(cls,data,ss=0,loop=False,options=None,volume=None):
      if ss:
        ffmpeg_options = {
        'options': '-vn '+options,
        "before_options": "-ss "+str(ss[0])+" -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
          }
      else:
        ffmpeg_options = {
        'options': '-vn '+options,#" -loglevel repeat+verbose"
        "before_options": " -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 1",
          }
      return cls(discord.FFmpegPCMAudio(data['video'], **ffmpeg_options),data=data,timeq=[time.time() if not ss else time.time()+ss[1] ,0,0] if not loop else ["looped",0,0],loop=loop,volume=volume) 



class Music(commands.Cog):

  def __init__(self,bot):
    self.bot = bot
    self.player = dict()
    self.timer = Timer(bot)
    
  @commands.Cog.listener()
  async def on_ready(self):
    now = datetime.datetime.now()
    await asyncio.sleep(60-now.second)
    self.timer.checktimer.start()
  
  @commands.Cog.listener()
  async def on_voice_state_update(self,ctx,before,after):
    if before.channel and not after.channel:
      voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
      if voice and not voice.is_connected():
        voice.cleanup()
        if ctx.guild.id in db:
          del db[ctx.guild.id]
          del s_opts[ctx.guild.id]
        if ctx.guild.id in self.player:
          if self.player[ctx.guild.id].loop:
            self.player[ctx.guild.id].set_loop(False)
        self.timer.delentry(ctx.guild.id)   
      elif voice and len(voice.channel.members) == 1:
        if ctx.guild.id in self.player:
          if self.player[ctx.guild.id].loop:
            self.player[ctx.guild.id].set_loop(False)
        self.timer.setentry(ctx.guild.id,2)
               
  @commands.command(aliases=['h'],pass_context= True)
  async def help(self,ctx):
    embed = discord.Embed(title="Google Docs documentation",description="**[Link to documentation](https://1pt.co/music)**",colour= random.randint(0, 0xffffff))
    embed.add_field(name='\u200b',value="Doc Written by:[Param Thakkar](https://www.param.me/)",inline=False)
    embed.set_author(name=f'{self.bot.user.name}',icon_url=self.bot.user.avatar_url)
    await ctx.send(embed=embed)
  
   
  @commands.command(aliases=['c','j','connect','summon'],pass_context=True)
  async def join(self,ctx):
    voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
    if isinstance(ctx.channel, discord.DMChannel):
      await ctx.send(f'Use {self.bot.user.name} in a server please.')
      return None
    if not(x := await self.checkconditions(ctx)):
      return

    
  @commands.command(aliases=['leav','dc','leave','stop'],pass_context = True)
  async def disconnect(self,ctx):
    voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
    if isinstance(ctx.channel, discord.DMChannel):
      await ctx.send(f'Use {self.bot.user.name} in a server please.')
      return None
    serverId = ctx.guild.id
    if serverId in db:
       del db[serverId]
       del s_opts[serverId]
    if voice and voice.is_connected():
      if len(voice.channel.members) == 1 or ctx.author.voice and ctx.author.voice.channel == voice.channel:
        if serverId in self.player:
          if self.player[serverId].loop == True:
            self.player[serverId].set_loop(False)
          voice.stop()
        voice.cleanup()
        await voice.disconnect()
        self.timer.delentry(ctx.guild.id)   
      else:
        await ctx.send("**User isn't connected to bot's voice channel**")
    else:
      await ctx.send("**Bot isn't connected**")

  @commands.command(aliases=['q'],pass_context= True)
  async def queue(self,ctx):
    if isinstance(ctx.channel, discord.DMChannel):
      await ctx.send(f'Use {self.bot.user.name} in a server please.')
      return None
    serverId = ctx.guild.id
    id = serverId
    count = 1
    embeds = []
    embed = discord.Embed(title=str(ctx.guild.name)+"'s Queue", colour= 0x8e0beb)
    if id in self.player:
      if self.player[id].loop == True:
        embed.set_footer(text="`Loop:`✔️")
      else:
        embed.set_footer(text="`Loop:`❌")
      embed.add_field(name="**Now Playing**",value="["+str(self.wslice(self.player[id].title,50))+"]("+self.player[id].url+")`|"+self.toHMS(self.player[id].duration)+"| Requested by: "+str(self.player[id].author)+"`",inline=False)
 
      if serverId in db: 
        for value,song in enumerate(db[serverId]):
          if value == 0:
             embed.add_field(name='Rest in Queue',value=str(value+1)+")["+self.wslice(song.get('title'),50)+"]("+song.get('url')+")`|"+self.toHMS(song.get('duration'))+"| Requested by: "+str(song.get('author'))+"`",inline = False)
          else:
            embed.add_field(name='\u200b',value=str(value+1)+")["+self.wslice(song.get('title'),50)+"]("+song.get('url')+")`|"+self.toHMS(song.get('duration'))+"| Requested by: "+str(song.get('author'))+"`",inline = False)
          if (value+2) % 10 == 0: 
            embeds.append(embed)
            count += 1
            embed = discord.Embed(title=str(ctx.guild.name)+"'s Queue'("+str(count)+")",colour=0x8e0beb)
      embeds.append(embed)
      if len(embeds) > 1:
        await self.pages(ctx.message,embeds)
      else:
        await ctx.send(embed=embeds[0])
    
    else:
      await ctx.send("**No songs in queue**")

  async def pages(self,msg,contents):
    pages = len(contents)
    cur_page = 1
    message = await msg.channel.send(embed=contents[cur_page-1])
    # getting the message object for editing and reacting

    await message.add_reaction("◀️")
    await message.add_reaction("▶️")
    buttons =  ["◀️", "▶️"]
    
    while True:
        try:
            reaction, user = await self.bot.wait_for("reaction_add", check=lambda reaction,user: user == msg.author and reaction.emoji in buttons, timeout=60)

            if str(reaction.emoji) == "▶️" and cur_page != pages:
                cur_page += 1
                await message.edit(embed=contents[cur_page-1])
                await message.remove_reaction(reaction, user)

            elif str(reaction.emoji) == "◀️" and cur_page > 1:
                cur_page -= 1
                await message.edit(embed=contents[cur_page-1])
                await message.remove_reaction(reaction, user)

            else:
                await message.remove_reaction(reaction, user)
               
        except asyncio.TimeoutError:
            await message.delete()
            break
  
  @commands.command(aliases=['np','nowplay'])
  async def nowplaying(self,ctx):
    if isinstance(ctx.channel, discord.DMChannel):
      await ctx.send(f'Use {self.bot.user.name} in a server please.')
      return None
    
    id = ctx.guild.id
    if id in self.player:
      if not self.player[id].loop and not self.player[id].ls:
        if self.player[id].timeq[2] == 0:
          timepassed = int(time.time()-(self.player[id].timeq[0]+self.player[id].timeq[1]))
        else:
          timepassed = int(self.player[id].timeq[2]-self.player[id].timeq[0])
        
        if 'speed' in s_opts[id][1]['temp']:
         if len(s_opts[id][1]['temp']['speed'])> 12:
           timepassed = timepassed * 4
         else:
            timepassed = int(timepassed *float(s_opts[id][1]['temp']['speed'].split("=")[1][:-1]))

        if timepassed > self.player[id].duration:
          timepassed = self.player[id].duration
        progressbar = self.progressbar(timepassed,self.player[id].duration)
        queuetime = self.toHMS(timepassed)+"/"+self.toHMS(self.player[id].duration)
      else:
        queuetime = "Infite or Looped"
        progressbar = self.progressbar(0,100)
        
      embed = discord.Embed(title="`"+queuetime+"`",description=progressbar,colour=0x000000)
      embed.set_author(name='Nowplaying: '+self.player[id].title,url=self.player[id].url,icon_url='https://cdn.discordapp.com/attachments/819709519063678978/882819723950182480/noice.gif')
      embed.set_image(url=self.player[id].thumbnail)
      if self.player[id].channel:
        embed.set_footer(text="From: "+self.player[id].channel+" and Requested by: "+self.player[id].author)
      else:
        embed.set_footer(text="Requested by: "+self.player[id].author)
      await ctx.send(embed=embed)
    else:
      await ctx.send("No songs are currently playing")
  
  def wslice(self,word,value):
      word.replace("**","")
      if len(word) > value:
        return word[:value-3]+"..."
      else:
        return word

  def progressbar(self,timepassed,duration):
    temp = ["▬","▬","▬","▬","▬","▬","▬","▬","▬","▬","▬","▬","▬","▬","▬","▬","▬","▬","▬","▬","▬","▬","▬","▬","▬"]
    temp.insert(int(timepassed/duration*100/4),"🔴")
    return "**|"+"".join(temp)+"|**"


  @commands.command(aliases=['sh'],pass_context = True)
  async def shuffle(self,ctx):
    if isinstance(ctx.channel, discord.DMChannel):
      await ctx.send(f'Use {self.bot.user.name} in a server please.')
      return None
    serverId = ctx.guild.id
    if serverId in db:
      random.shuffle(db[serverId])
      await ctx.send("`Song queue has been shuffled 🔀`")

  @commands.command(aliases=['rp'],pass_context = True)
  async def replay(self,ctx):
    if isinstance(ctx.channel, discord.DMChannel):
      await ctx.send(f'Use {self.bot.user.name} in a server please.')
      return None
    serverId = ctx.guild.id
    if serverId in self.player:
      db[serverId].insert(0,self.player[serverId].data)
      await ctx.send("Song has been requeued🔂")

  @commands.command(aliases=['sv'])
  async def save(self,ctx):
    if isinstance(ctx.channel, discord.DMChannel):
      await ctx.send(f'Use {self.bot.user.name} in a server please.')
      return None
    
    serverId = ctx.guild.id
    if serverId in self.player:
      embed = discord.Embed(title="**["+self.player[serverId].title+"]"+"("+self.player[serverId].url+")**",description = "```Song requested by: "+self.player[serverId].author+"||"+self.toHMS(self.player[serverId].duration),colour = 0xffa826)
      embed.set_footer(text=f"`Saved by {self.bot.user.name} in "+ctx.guild+" at "+str(ctx.message.created_at)+"`")
      user = await ctx.author.create_dm()
      await user.send(embed=embed)

  @commands.command(aliases=['vol'])
  async def volume(self,ctx,volume: int):
    if isinstance(ctx.channel, discord.DMChannel):
      await ctx.send(f'Use {self.bot.user.name} in a server please.')
      return None
    if volume > 250:
      await ctx.send("Sorry, volume has been capped to 250%.")
      volume = 250
    serverId = ctx.guild.id
    if serverId in self.player:
      voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
      voice.source.volume = volume / 100
      await ctx.send(f"Volume for this song has been adjusted {volume}%")
    else:
      await ctx.send("Audio source is not connected to channel.")

  @commands.command(aliases=['mv'],pass_context = True)
  async def move(self,ctx,value1:int,value2:int):
    if isinstance(ctx.channel, discord.DMChannel):
      await ctx.send(f'Use {self.bot.user.name} in a server please.')
      return None
    serverId = ctx.guild.id
    if value1 < 1 or value2 < 1 or value1 > len(db[serverId]) or value2 > len(db[serverId]):
      await ctx.send("Positions are out of query bounds")
    else:
      db[serverId][value1-1],db[serverId][value2-1] = db[serverId][value2-1],db[serverId][value1-1]
 
  

              
  @commands.command(aliases=['pt'],pass_context = True)
  async def playtop(self,ctx,*,request=None):
    if isinstance(ctx.channel, discord.DMChannel):
      await ctx.send(f'Use {self.bot.user.name} in a server please.')
      return None
    if not (x := await self.checkconditions(ctx)):
      return
    livestream = False
    
    if request is None:
      return
    
    if not "." in request:
      await ctx.send("`Searching for "+request+" on Youtube`")
      try:
        ytrequest = json.loads(YoutubeSearch(request, max_results=1).to_json())
        request = 'https://www.youtube.com/watch?v='+str(ytrequest['videos'][0]['id'])
        if ytrequest['videos'][0]['publish_time'] == 0:
          livestream = True
      except Exception:
        await ctx.send("`No searches found.`")
        return 
    
    serverId = ctx.guild.id

    await ctx.send("`Attempting to request "+request+"`")
    info = await Source.breakdownurl(self,request,serverId,Loop = self.bot.loop,npl=False)
    if info is None:
      await ctx.send("`Invalid URL`")
      return None
    else:
      if 'entries' in info: 
        info = info['entries'][0]

    if 'is_live' in info and info['is_live'] or 'duration' in info and not info['duration']:
      livestream = True
     

    playlist = True if 'list=' in info else False
    song_info = {'video':info.get('url',None), 'url': request,'id':info.get('id',None),'title':info.get('title',None),'duration':int(info.get('duration',None)) if info.get('duration',None) else None,'thumbnail':info.get('thumbnail',None),'channel':info.get('channel',None),'tags':info.get('tags',None)[:3] if info.get('tags',None) else None,'author': str(ctx.author),'ls':livestream}
    if serverId in self.player:
      db[serverId].insert(0,song_info)
      await self.addedtoqueue(ctx,song_info,playlist,1,thumbnail=song_info.get('thumbnail',None))
    else:
      db[serverId].append(song_info)
      await self.addedtoqueue(ctx,song_info,playlist,0,thumbnail=song_info.get('thumbnail',None))
      self.playmusic(ctx,serverId)

    if not playlist:
      return None

    info2 = await Source.breakdownurl(self,request,serverId,Loop = self.bot.loop,npl=False)
    if serverId in db:
        if db[serverId][0]['id'] == info.get('id',None):
          firstsong = db[serverId].pop(0)
    else:
        firstsong = None

    if "entries" in info2:
      del info2["entries"][0]
      for entry in reversed(info2["entries"]):
        db[serverId].insert(0,{'video':entry.get('url',None),'url':entry.get('webpage_url',None),'thumbnail':entry.get('thumbnail',None),'channel':entry.get('channel',None),'tags':entry.get('tags',None)[:3] if entry.get('tags',None) else None,'id':entry.get('id',None),'title':entry.get('title',None),'duration':int(entry.get('duration',None)) if info.get('duration',None) else None,'author': str(ctx.author),'ls':False})
      if firstsong:
        db[serverId].insert(0,firstsong)
    else:
      return None
        

  @commands.command(aliases=['ps'],pass_context = True)
  async def playskip(self,ctx,*,request=None):
    
    if isinstance(ctx.channel, discord.DMChannel):
      await ctx.send(f'Use {self.bot.user.name} in a server please.')
      return None
  
    if not (x := await self.checkconditions(ctx)):
      return
    
    if request is None:
      return
    livestream = False
    

    if not "." in request:
      await ctx.send("`Searching for "+request+" on Youtube`")
      try:
        ytrequest = json.loads(YoutubeSearch(request, max_results=1).to_json())
        request = 'https://www.youtube.com/watch?v='+str(ytrequest['videos'][0]['id'])
        if ytrequest['videos'][0]['publish_time'] == 0:
          livestream = True
          
        
      except Exception:
        await ctx.send("`No Searches found.`")
        return 
    
    serverId = ctx.guild.id


    await ctx.send("`Searching for "+request+" on Youtube`")
    info = await Source.breakdownurl(self,request,serverId,Loop = self.bot.loop)
    if info is None:
      await ctx.send("`Invalid URL`")
      return None
    else:
      if 'entries' in info:
        info = info['entries'][0]
        
    if info['is_live'] or info['duration'] == 0.0:
      livestream = True

    playlist = True if "list=" in request else False
    song_info = {'video':info.get('url',None), 'url': request,'id':info.get('id',None),'title':info.get('title',None),'duration':int(info.get('duration',None)) if info.get('duration',None) else None,'thumbnail':info.get('thumbnail',None),'channel':info.get('channel',None),'tags':info.get('tags',None)[:3] if info.get('tags',None) else None,'author': str(ctx.author),'ls':livestream}

    db[serverId].insert(0,song_info)
    await self.addedtoqueue(ctx,song_info,playlist,0,thumbnail=song_info.get('thumbnail',None))


    if serverId in self.player:
      if self.player[serverId].loop == True:
        self.player[serverId].set_loop(False)
      voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
      if voice and voice.is_playing() or voice.is_paused():
        voice.stop()
      await ctx.send("```Song has been skipped⏭️```")
    else:
      self.playmusic(ctx,serverId)

    if not playlist:
      return None

    info2 = await Source.breakdownurl(self,request,serverId,Loop = self.bot.loop,npl=False)

    if "entries" in info2:
      del info2["entries"][0]
      for entry in reversed(info2["entries"]):
         db[serverId].insert(0,{'video':entry.get('url',None),'url':entry.get('webpage_url',None),'thumbnail':entry.get('thumbnail',None),'channel':entry.get('channel',None),'tags':entry.get('tags',None)[:3] if entry.get('tags',None) else None,'id':entry.get('id',None),'title':entry.get('title',None),'duration':int(entry.get('duration',None)) if info.get('duration',None) else None,'author': str(ctx.author),'ls':False})
    else:
      return None
      

  @commands.command(aliases=['p','pla'],pass_context = True)
  async def play(self,ctx,*,request=None):
    
    if isinstance(ctx.channel, discord.DMChannel):
      await ctx.send(f'Use {self.bot.user.name} in a server please.')
      return None

    if not (x := await self.checkconditions(ctx)):
      return

    if request is None:
      return

    livestream = False
        
    if not "." in request:
          await ctx.send("`Searching for "+request+" on Youtube`")
          try:
            ytrequest = json.loads(YoutubeSearch(request, max_results=1).to_json())
            request = 'https://www.youtube.com/watch?v='+str(ytrequest['videos'][0]['id'])
            if ytrequest['videos'][0]['publish_time'] == 0:
              livestream = True
  
          except Exception:
            await ctx.send("`No searches found.`")
            return None
    
    serverId = ctx.guild.id

    await ctx.send("`Attempting to request "+request+"`")
    info = await Source.breakdownurl(self,request,serverId,Loop = self.bot.loop)
    if info is None:
      await ctx.send("`Invalid URL`")
      return None
    else:
      if "entries" in info:
        info = info['entries'][0]

    if 'is_live' in info  and info['is_live']  or 'duration' in info and not info['duration']:
      livestream = True

    playlist = True if 'list=' in request else False
    
    song_info = {'video':info.get('url',None), 'url': request,'id':info.get('id',None),'title':info.get('title',None),'duration':int(info.get('duration',None)) if info.get('duration',None) else None,'thumbnail':info.get('thumbnail',None),'channel':info.get('channel',None),'tags':info.get('tags',None)[:3] if info.get('tags',None) else None,'author': str(ctx.author),'ls':livestream}
    

    if serverId in self.player:
      db[serverId].append(song_info)
      await self.addedtoqueue(ctx,song_info,playlist,len(db[serverId]),thumbnail=song_info.get('thumbnail',None))
    else:
      db[serverId].append(song_info)
      await self.addedtoqueue(ctx,song_info,playlist,0,thumbnail=song_info.get('thumbnail',None))
      self.playmusic(ctx,serverId)

    if not playlist:
      return None

    
    info2 = await Source.breakdownurl(self,request,serverId,Loop = self.bot.loop,npl=False)
    
    if "entries" in info2:
      del info2["entries"][0]
      for entry in info2["entries"]:
        db[serverId].append({'video':entry.get('url',None),'url':entry.get('webpage_url',None),'thumbnail':entry.get('thumbnail',None),'channel':entry.get('channel',None),'tags':entry.get('tags',None)[:3] if entry.get('tags',None) else None,'id':entry.get('id',None),'title':entry.get('title',None),'duration':int(entry.get('duration',None)) if info.get('duration',None) else None,'author': str(ctx.author),'ls':False})
    else:
      return None
    
   
    

  @commands.command(aliases=['paus'],pass_context = True)
  async def pause(self,ctx):
     voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
     if isinstance(ctx.channel, discord.DMChannel):
        await ctx.send(f'Use {self.bot.user.name} in a server please.')
        return None

     if voice and voice.is_playing():
       serverId = ctx.guild.id
       self.player[serverId].set_pausetime(time.time(),pause=True)
       voice.pause()
       await ctx.send("Music has been paused")
     else:
       await ctx.send("No music is playing")


  @commands.command(aliases=['resum'],pass_context = True)
  async def resume(self,ctx):
    if isinstance(ctx.channel, discord.DMChannel):
      await ctx.send(f'Use {self.bot.user.name} in a server please.')
      return None
    voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)

    if voice and voice.is_paused():
      serverId = ctx.guild.id
      self.player[serverId].set_pausetime(time.time())
      voice.resume()
      await ctx.send("Music has been resumed!")

  @commands.command(aliases=['fs','skip'],pass_context = True)
  async def forceskip(self,ctx):
    if isinstance(ctx.channel, discord.DMChannel):
      await ctx.send(f'Use {self.bot.user.name} in a server please.')
      return None
    voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
    if voice and voice.is_connected():
      serverId = ctx.guild.id
      if serverId in self.player:
        if self.player[serverId].loop == True:
          self.player[serverId].set_loop(False)
        if voice.is_playing() or voice.is_paused():
          voice.stop()
        await ctx.send("```Song has been skipped⏭️```")
  
  @commands.command(aliases=['clea','clean'])
  async def clear(self,ctx):
    if isinstance(ctx.channel, discord.DMChannel):
      await ctx.send(f'Use {self.bot.user.name} in a server please.')
      return None
    serverId = ctx.guild.id
    author = ctx.message.content.split(" ",1)[1] if len(ctx.message.content.split(" ",1)) > 1 else None
    if author is None:
      if serverId in db and len(db[serverId]) > 0:
        db[serverId].clear()
        await ctx.send("```Queue has been Cleared 🧹```")
      else:
        await ctx.send("```Nothing to Clear ¯\_(ツ)_/¯```")
      return None
    if serverId in db:
      guild = self.bot.get_guild(int(serverId))
      author = int(author[3:-1])
      name = await guild.fetch_member(author)
      if name is None:
        return
      maxv = len(db[serverId])
      count = 0
      i = 0
      while i < maxv:
        if db[serverId][i]['author'] == str(name):
          del db[serverId][i]
          maxv -= 1
          count += 1      
        else:
          i += 1
     
      await ctx.send("```css\n"+str(count)+" entries by:"+str(name.name)+" have been cleared from Queue 🧹```")

  @commands.command(aliases=['searc','s'],pass_context = True)
  async def search(self,ctx,*,request):
    voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
    if isinstance(ctx.channel, discord.DMChannel):
      await ctx.send(f'Use {self.bot.user.name} in a server please.')
      return None
      
    if not (x := await self.checkconditions(ctx)):
      return

    await ctx.send("`Searching for "+request+" on Youtube`")
    try:
      embed = discord.Embed(title="Videos:"+request ,colour = 0x0beb61)
      ytrequest = json.loads(YoutubeSearch(request, max_results=7).to_json())
      for i,video in enumerate(ytrequest['videos']):
          embed.add_field(name='\u200b',value='**'+str(i+1)+")["+video.get('title')+']('+'https://www.youtube.com/watch?v='+video.get('id')+')|('+str(video.get('duration'))+')**\n'+'`Author:'+video.get('channel')+'||Views:'+str(video.get('views'))+'`',inline=False)
      await ctx.send(embed=embed)
    except Exception:
      await ctx.send("`No searches found.`")
      return 
  
    try:
      def check(m):
        return m.content.isdigit() and m.channel == ctx.channel
      msg = await self.bot.wait_for('message',check=check,timeout=60)
      value = int(msg.content)
      livestream = False
      if value <= len(ytrequest['videos']):
        request = 'https://www.youtube.com/watch?v='+str(ytrequest['videos'][value-1]['id'])
        info = await Source.breakdownurl(self,request,ctx.guild.id,Loop = self.bot.loop)
        if info is None:
          await ctx.send("`Invalid URL`")
          return None
        if ytrequest['videos'][value-1]['publish_time'] == 0:
          livestream = True
        serverId = ctx.guild.id
        db[serverId].append((x:={'video':info.get('url',None), 'url': request,'id':info.get('id',None),'title':info.get('title',None),'duration':int(info.get('duration',None)) if info.get('duration',None) else None,'thumbnail':info.get('thumbnail',None),'channel':info.get('channel',None),'tags':info.get('tags',None)[:3] if info.get('tags',None) else None,'author': str(ctx.author),'ls':livestream}))
        await self.addedtoqueue(ctx,x,False,len(db[serverId]),thumbnail=x.get('thumbnail',None))
        if not serverId in self.player:
          self.playmusic(ctx,serverId)
      
    except asyncio.TimeoutError:
      return None 
     
  @commands.command(pass_context = True)
  async def loop(self,ctx):
    if isinstance(ctx.channel, discord.DMChannel):
      await ctx.send(f'Use {self.bot.user.name} in a server please.')
      return None

    serverId = ctx.guild.id
    if serverId in self.player:
      if self.player[serverId].loop == False:
        self.player[serverId].set_loop(True)
        await ctx.send("```Song has been looped🔁```")
      else:
        self.player[serverId].set_loop(False)
        await ctx.send("```Song has been unlooped🔁```")

  async def checkconditions(self,ctx):
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
        db[serverId] = []
        s_opts[serverId] = ["",{},0]
        s_opts[serverId][1]['volume'] = 0.75
        s_opts[serverId][1]['temp'] = dict()
        self.timer.setentry(ctx.guild.id,1)
      except asyncio.TimeoutError:
        await ctx.send('bot has disconnected')
    return True

  @commands.command(pass_context = True)
  async def forward(self,ctx,value:int):
    if isinstance(ctx.channel, discord.DMChannel):
      await ctx.send(f'Use {self.bot.user.name} in a server please.')
      return None
    serverId = ctx.guild.id
    if serverId in self.player and ctx.voice_client.is_playing():
      if self.player[serverId].timeq[2] == 0:
        timepassed = int(time.time()-(self.player[serverId].timeq[0]+self.player[serverId].timeq[1]))
      else:
        timepassed = int(self.player[serverId].timeq[2]-self.player[serverId].timeq[0])

      speed = 1
      if 'speed' in s_opts[serverId][1]['temp']:
        if len(s_opts[serverId][1]['temp']['speed']) > 12:
          speed = 4
        else:
          speed = float(s_opts[serverId][1]['temp']['speed'].split("=")[1][:-1])


      if self.player[serverId].ls is True:
        await ctx.send('Livestream forwarding not setup yet!')
        return None
        """
        if self.player[serverId].duration is None:
          self.player[serverId].duration = timepassed*speed
          await ctx.send("You can't forward that far")
          return None
        elif int((timepassed*speed) +value) > self.player[serverId].duration:
          await ctx.send("You can't forward that far")
          return None
        """
      elif int((timepassed*speed) +value)> self.player[serverId].duration:
        await ctx.send("You can't forward that far")
        return None
        
      if speed == 1:
        timetoreset = [(timepassed + value), -(timepassed + value)]
      else:
        timetoreset = [int((timepassed*speed) + value), -int(timepassed + (value*(speed**-1)))]

      self.player[serverId].set_repeat(True)
      volume = ctx.voice_client.source.volume
      ctx.voice_client.stop()
      self.playmusic(ctx,serverId,nowplaying=[self.player[serverId].data,timetoreset],loop=self.player[serverId].loop,volume=volume)
      await ctx.send('**Song has been forwarded '+str(value)+' seconds**')
    else:
     await ctx.send("No song is being played in server vc")

  @commands.command(pass_context = True)
  async def rewind(self,ctx,value:int):
    if isinstance(ctx.channel, discord.DMChannel):
      await ctx.send(f'Use {self.bot.user.name} in a server please.')
      return None
    serverId = ctx.guild.id
    if serverId in self.player and ctx.voice_client.is_playing():
      if self.player[serverId].timeq[2] == 0:
        timepassed = int(time.time()-(self.player[serverId].timeq[0]+self.player[serverId].timeq[1]))
      else:
        timepassed = int(self.player[serverId].timeq[2]-self.player[serverId].timeq[0])


      speed = 1
      if 'speed' in s_opts[serverId][1]['temp']:
        if len(s_opts[serverId][1]['temp']['speed']) > 12:
          speed = 4
        else:
          speed = float(s_opts[serverId][1]['temp']['speed'].split("=")[1][:-1])

      """
      if self.player[serverId].ls is True:
        if self.player[serverId].duration is None or timepassed*speed > self.player[serverId].duration:
          self.player[serverId].duration = timepassed*speed
      """

      if value > timepassed*speed:
        await ctx.send("You can't rewind that far")
        return None
        
      if speed == 1:
        timetoreset = [(timepassed - value), -(timepassed - value)]
      else:
        timetoreset = [(timepassed - value), -int(timepassed - (value*(speed**-1)))]
      self.player[serverId].set_repeat(True)
      volume = ctx.voice_client.source.volume
      ctx.voice_client.stop()
      self.playmusic(ctx,serverId,nowplaying=[self.player[serverId].data,timetoreset],loop=self.player[serverId].loop,volume=volume)
      await ctx.send('**Song has been rewinded '+str(value)+' seconds**')
    else:
      await ctx.send("No song is being played in server vc")

  @commands.command(pass_context = True)
  async def test(self,ctx,options=None):
    if ctx.author.id == 278646990777221120:
      if isinstance(ctx.channel, discord.DMChannel):
       await ctx.send(f'Use {self.bot.user.name} in a server please.')
       return None 
      await ctx.author.voice.channel.connect(timeout=60.0,reconnect=True)
      """
      if s_opts[id][1]['temp']:
        options = s_opts[id][1]['temp']
      else:
        options = s_opts[id][0]
      """
      
      options = ' -af "volume=5dB" -af "equalizer=f=10:width_type=q:width=1.4:g=-3,equalizer=f=21:width_type=q:width=1.4:g=-3,equalizer=f=42:width_type=q:width=1.4:g=-3,equalizer=f=83:width_type=q:width=1.4:g=-3,equalizer=f=166:width_type=q:width=1.4:g=-3,equalizer=f=333:width_type=q:width=1.4:g=-3,equalizer=f=577:width_type=q:width=1.4:g=-3,equalizer=f=1000:width_type=q:width=1.4:g=-3,equalizer=f=2000:width_type=q:width=1.4:g=-1,equalizer=f=4000:width_type=q:width=1.4:g=1,equalizer=f=8000:width_type=q:width=1.4:g=3.5,equalizer=f=16000:width_type=q:width=1.4:g=6,equalizer=f=20000:width_type=q:width=3:g=8"'
      options = ""
      #-af loudnorm=I=-6:TP=-1.5:LRA=4
      ffmpeg_options= {
            'options': '-vn'+options,} 
      ctx.voice_client.play(discord.FFmpegPCMAudio("./testfile/UXgSy7Q1McY.mp3", **ffmpeg_options),after=lambda e: print("Done"))
      ctx.voice_client.source.volume = 0.5
      
  
  @commands.command(aliases=['options','settings'],pass_context = True)
  async def opts(self,ctx,setting: str,*,value=None):
    if isinstance(ctx.channel, discord.DMChannel):
      await ctx.send(f'Use {self.bot.user.name} in a server please.')
      return None
    serverId = ctx.guild.id
    if setting is None:
      pass
    elif setting.lower() == "speed":
      if serverId in self.player and ctx.voice_client.is_playing():
        value1 = None
        if 'speed' in s_opts[serverId][1]['temp']:
          if len(s_opts[serverId][1]['temp']['speed'])> 12:
            value1 = 4.0
          else:
            value1 = float(s_opts[serverId][1]['temp']['speed'].split("=")[1][:-1])

        if not value:
          if 'speed' in s_opts[serverId][1]['temp']:
            del s_opts[serverId][1]['temp']['speed']
            await ctx.send('Speed has been reset to **1x**')
            value = 1
        elif value.isdigit():
          if int(value) == 100:
            if 'speed' in s_opts[serverId][1]['temp']:
              del s_opts[serverId][1]['temp']['speed']
              await ctx.send("Speed has bas been reset to **1x**")
              value = 1
            else:
              return None
          else:
            value = (min(max(50,int(value)),200)/100.0)
            s_opts[serverId][1]['temp']['speed'] = f'atempo={value},'
            await ctx.send(f'Speed has been reset to **{value}x**')
        elif value == "pog":
          s_opts[serverId][1]['temp']['speed'] = 'atempo=2.0,atempo=2.0,'
          await ctx.send(f'Speed has been reset to **POGGERS(4x)**')
          value = 4
        else:
          return None
        if self.player[serverId].timeq[2] == 0:
          timepassed = int(time.time()-(self.player[serverId].timeq[0]+self.player[serverId].timeq[1]))
        else:
          timepassed = int(self.player[serverId].timeq[2]-self.player[serverId].timeq[0])
        if value1:
          timepassed = int(timepassed*value1)
        if timepassed < self.player[serverId].duration:
          tme = [timepassed,-int(timepassed*(value**-1))]
          self.player[serverId].set_repeat(True)
          volume = ctx.voice_client.source.volume
          ctx.voice_client.stop()
          self.playmusic(ctx,serverId,nowplaying=[self.player[serverId].data,tme],loop=self.player[serverId].loop,volume=volume)
    elif setting.lower() == "volume" or setting.lower() == "vol":
      if not value:
        if s_opts[serverId][1]['volume'] != 0.75:
          s_opts[serverId][1]['volume'] = 0.75
          await ctx.send("Default volume has been reset to 75%")
      if value.isdigit():
        value = min(max(25,int(value)),250)
        value = value/100
        s_opts[serverId][1]['volume'] = value
        await ctx.send(f'Default volume has been set to {value}')
    elif setting.lower() == "8d":
      if serverId in self.player and ctx.voice_client.is_playing():
        if '8d' in s_opts[serverId][1]['temp']:
          del s_opts[serverId][1]['temp']['8d']
          await ctx.send("8d sound effect turned off")
        else:
          s_opts[serverId][1]['temp']['8d'] = 'apulsator=hz=0.125,'
          await ctx.send("8d sound effect turned on")

      if self.player[serverId].timeq[2] == 0:
          timepassed = int(time.time()-(self.player[serverId].timeq[0]+self.player[serverId].timeq[1]))
      else:
          timepassed = int(self.player[serverId].timeq[2]-self.player[serverId].timeq[0])

      if 'speed' in s_opts[serverId][1]['temp']:
        if len(s_opts[serverId][1]['temp']['speed']) > 12:
          speed = 4
        else:
          speed = float(s_opts[serverId][1]['temp']['speed'].split("=")[1][:-1])
        timetoreset = [int((timepassed*speed)), -int(timepassed)]
      else:
        timetoreset = [(timepassed), -(timepassed)]

      self.player[serverId].set_repeat(True)
      volume = ctx.voice_client.source.volume
      ctx.voice_client.stop()
      self.playmusic(ctx,serverId,nowplaying=[self.player[serverId].data,timetoreset],loop=self.player[serverId].loop,volume=volume)
      
    elif setting.lower() == "adveq":
      eqsets = discord.Embed(title=f"{self.bot.user.name}'s equalization",description='Pick from 5 standard presets or make your own by clicking the + button. If you are creating your own presets please prepare your settings beforehand. You can find info on the eq settings you can set in ```!opts eqinfo```.',colour=0x02C1ff)
      eqsets.add_field(name="Please Note:",value="Only create custom presets if you know what you're doing. Faulty presets may cause audio clipping and **damage your audio equipment.**",inline=False)
      eqsets.add_field(name='5 Standard presets:',value='1)Bass Boost, 2)High Boost, 3)Classic, 4)Vocal, 5)Rock')
      await self.seteq1(ctx,eqsets)


  @commands.command(pass_context = True)
  async def lyrics(self,ctx,*,text=None):
    if not text:
      if ctx.guild.id in self.player:
        if self.player[ctx.guild.id].tags:
          words = self.player[ctx.guild.id].tags
        else:
          await ctx.send("No lyrics found in genius database")
    else:
      words = [text]
    for word in words:
      songs = genius.search_songs(word)
      if songs['hits']:
        song = songs['hits'][0]['result']
        title = song.get('title_with_featured',None) or song.get('title',None) or "Nothing"
        url = song.get('url',None)
        lyrics =  genius.lyrics(song_url=url)
        embed = discord.Embed(title=title,description=lyrics[:4096])
        embed.set_thumbnail(url=song['song_art_image_thumbnail_url'])
        embed.set_footer(text="Requested by:"+str(ctx.author.name))
        await ctx.send(embed=embed)
        break
      await asyncio.sleep(0.5)
    else:
      await ctx.send("No lyrics found in genius database")
  



  """
  async def seteq1(self,ctx,content):20
  
    
    serverId = ctx.guild.id
    allbuttons = ['1️⃣','2️⃣️','3️⃣','4️⃣','5️⃣','6️⃣','7️⃣','8️⃣','9️⃣','🔟']
    button = []
    length = len(s_opts[serverId][1]['presets'])
    for i in range(length):
      button.append(allbutons[i])
    if length != 10:
      buttons.append('➕')
    message = ctx.send(embed=content)
    for i in buttons:
      message.add_reaction(i)

    while True:
      try:
        reaction, user = await self.bot.wait_for("reaction_add", check=lambda reaction,user: user == ctx.author and reaction.emoji in buttons, timeout=60)

        if str(reaction.emoji) == '➕':
          raise SessionFinished
        elif str(reaction.emoji) == '1️⃣':
          s_opts[serverId][0] = s_opts[serverId][1]['presets'][0]
          await ctx.send('**Preset has been changed to 1**')
          message.delete()
          return None
        elif str(reaction.emoji) == '2️⃣':
          s_opts[serverId][0] = s_opts[serverId][1]['presets'][1]
          await ctx.send('**Preset has been changed to 2**')
          message.delete()
          return None
        elif str(reaction.emoji) == '3️⃣':
          s_opts[serverId][0] = s_opts[serverId][1]['presets'][2]
          await ctx.send('**Preset has been changed to 3**')
          message.delete()
          return None
        elif str(reaction.emoji) == '4️⃣':
          s_opts[serverId][0] = s_opts[serverId][1]['presets'][3]
          await ctx.send('**Preset has been changed to 4**')
          message.delete()
          return None
        elif str(reaction.emoji) == '5️⃣':
          s_opts[serverId][0] = s_opts[serverId][1]['presets'][4]
          await ctx.send('**Preset has been changed to 5**')
          message.delete()
          return None
        elif str(reaction.emoji) == '6️⃣':
          s_opts[serverId][0] = s_opts[serverId][1]['presets'][5]
          await ctx.send('**Preset has been changed to 6**')
          message.delete()
          return None
        elif str(reaction.emoji) == '7️⃣':
          s_opts[serverId][0] = s_opts[serverId][1]['presets'][6]
          await ctx.send('**Preset has been changed to 7**')
          message.delete()
          return None
        elif str(reaction.emoji) == '8️⃣':
          s_opts[serverId][0] = s_opts[serverId][1]['presets'][7]
          message.delete()
          await ctx.send('**Preset has been changed to 8**')
          return None
        elif str(reaction.emoji) == '9️⃣':
          s_opts[serverId][0] = s_opts[serverId][1]['presets'][8]
          await ctx.send('**Preset has been changed to 9**')
          message.delete()
          return None
        elif str(reaction.emoji) == "🔟":
          s_opts[serverId][0] = s_opts[serverId][1]['presets'][9]
          await ctx.send('**Preset has been changed to 10**')
          message.delete()
          return None
     
      except (asyncio.TimeoutError,SessionFinished) as err:
        if err == asyncio.TimeoutError:
          await ctx.send('**Timeout 60 seconds has passed**')
          message.delete()
          return None
        elif err == SessionFinished:
          break
    embed = discord.Embed(title='Step 0:',description='How do you want to add your settings.\n**1)**All at once\n**2)**Step by Step',colour=0x02C1ff)
    embed.set_footer(text="All steps after this(60 seconds) will timeout in 5 minutes")
    await message.edit(embed=embed)
    buttons = ['1️⃣','2️⃣️']
    option = 0 
    while True:
      try:
        reaction, user = await self.bot.wait_for("reaction_add", check=lambda reaction,user: user == ctx.author and reaction.emoji in buttons, timeout=60)

        if str(reaction.emoji) == '1️⃣':
          options = 1
          raise SessionFinished
        elif str(reaction.emoji) == '2️⃣️':
          options = 2
          raise SessionFinished

      except (asyncio.TimeoutError,SessionFinished) as err:
        if err == asyncio.TimeoutError:
          await ctx.send('**Timeout 60 seconds has passed**')
          message.delete()
          return None
        elif err == SessionFinished:
          break 
    if options == 1:
      embed = discord.Embed(title='Please send a message in this exact format',colour=0x02C1ff)
      embed.add_field(name="**1)Enter preamp value**",value="start off your message with preamp value and seperate by |")
      embed.add_field(name="**2)For each frequency**",value="After insert in format the format: frequencyvalue,type(q:Quality,o:Octave,h:Hz,s:Slope),typevalue,gain")
      embed.add_field(name="**3) Seperate each frequency**",value="By inserting a | after each entry(don't need it for the last one)")
      embed.add_field(name="Example:",value="5|0,q,1.4,3|250,q,2.4,-3.5|1000,q,4.8,4.5|5000,q,1.4,-4")
      embed.set_footer(text="The whole entry should be sent in one message")
      def check()
        def checkeqset()
    """




  




  """
    elif setting == "bass":
      if not value or value == "reset":
        if 'bass' in s_opts[serverId][1]:
          temp = s_opts[serverId][1]['bass']
          s_opts[serverId][1]['bass'] = 0
          if not 'treble' in s_opts[serverId][1]:
            s_opts[serverId][1]['temp'].replace(" -af bass=g="+str(temp),"")
          else:
            s_opts[serverId][1]['temp'].replace(" bass=g="+str(temp),"")
          tme = 10
          self.playmusic(ctx,serverId,tme)
      elif value.isdigit(): 
         value = int(value)
         value = max(min(value,200),-200)
         value /= 20
         if 'bass' in s_opts[serverId][1]:
           s_opts[serverId][1]['temp'].replace("-af bass=g="+str(s_opts[serverId][1]['bass']),"-af bass=g"+str(value))
         elif 'treble' in s_opts[serverId][1]:
           s_opts[serverId][1]['temp'].replace("-af treble=g="+str(s_opts[serverId][1]['treble']),"-af bass=g="+str(value)+" treble=g="+str(s_opts[serverId][1]['treble']))
         else:
           s_opts[serverId][1]['temp'] += " -af bass=g="+str(value)
         s_opts[serverId][1]['bass'] = value
         if ctx.voice_client.is_playing():
            tme = 10
            if self.player[serverId].timeq[2] == 0:
              timepassed = int(time.time()-(self.player[serverId].timeq[0]+self.player[serverId].timeq[1]))
            else:
              timepassed = int(self.player[serverId].timeq[2]-self.player[serverId].timeq[0])
            tme = [timepassed,-timepassed]
            self.player[serverId].set_repeat(True)
            ctx.voice_client.stop()
            self.playmusic(ctx,serverId,tme)
      else:
          await ctx.send('<0-200)>')
          return None
    elif setting == "treble":
      if not value or value == "reset":
        if 'treble' in self.player[serverId][1]:
          temp = self.player[serverId][1]['treble']
          s_opts[serverId][1]['treble'] = 0
          if 'bass' in s_opts[id][1]:
            s_opts[serverId][1]['temp'].replace(" treble=g="+str(temp),"")
          else:
            s_opts[serverId][1]['temp'].replace(" -af treble=g="+str(temp),"")
          self.playmusic(ctx,serverId,tme)
      elif value.isdigit(): 
         value = int(value)
         value = max(min(value,200),-200)
         value /= 20
         if 'treble' in s_opts[serverId][1]:
            s_opts[id][1]['temp'].replace("treble=g="+str(s_opts[serverId][1]['treble']),"treble=g="+str(value))
         elif 'bass' in s_opts[serverId][1]:
           s_opts[serverId][1]['temp'].replace("-af bass=g="+str(s_opts[serverId][1]['bass']),"-af bass=g="+str(s_opts[serverId][1]['bass'])+" treble=g="+str(value))
         else:
           s_opts[serverId][1]['temp'] += " -af treble=g="+str(value)
         s_opts[serverId][1]['treble'] = value
         if ctx.voice_client.is_playing():
            tme = 10
            
            if self.player[serverId].timeq[2] == 0:
              timepassed = int(time.time()-(self.player[serverId].timeq[0]+self.player[serverId].timeq[1]))
            else:
              timepassed = int(self.player[serverId].timeq[2]-self.player[serverId].timeq[0])
            tme = [timepassed,-timepassed]
            self.player[serverId].set_repeat(True)
            
            ctx.voice_client.stop()
            self.playmusic(ctx,serverId,tme)
      else:
          await ctx.send('<(0-200)>')
          return None
    """

       
  def playmusic(self,ctx,id,nowplaying=None,loop=False,volume=None):
      if nowplaying:
        player = Source.streamvideo(nowplaying[0],loop=loop,ss=nowplaying[1],options=self.getoptions(id),volume=volume)
        self.player[id] = player
        try:
          ctx.voice_client.play(player, after=lambda e: self.reseteffects(id) or self.playmusic(ctx,id,loop=self.player[id].loop) if not player.repeat else player.set_repeat(False))
          return None
        except Exception:
          if not player.repeat:
            self.reseteffects(id) 
            self.playmusic(ctx,id,loop=self.player[id].loop)
          else:
            player.set_repeat(False)
          return None
      if id in self.player:
        if self.player[id].loop == True:
          loop = True
          nowplaying = self.player[id].data
      if not nowplaying:
        if id in db and len(db[id]) > 0:
          nowplaying = db[id].pop(0)
        else:
          del self.player[id]
          if not self.timer.checkentry(ctx.guild.id):
            self.timer.setentry(id,1)
          return None 
          
      player = Source.streamvideo(nowplaying,loop=loop,options=self.getoptions(id),volume=s_opts[id][1]['volume'])
      self.player[id] = player
      try:
        ctx.voice_client.play(player, after=lambda e: self.reseteffects(id) or self.playmusic(ctx,id,loop=self.player[id].loop) if not player.repeat else player.set_repeat(False))
        self.timer.delentry(ctx.guild.id)
      except Exception:
        if not player.repeat:
          self.reseteffects(id) 
          self.playmusic(ctx,id,loop=self.player[id].loop)
        else:
          player.set_repeat(False)
        return None

  def getoptions(self,serverId):
    if serverId in s_opts:
      if s_opts[serverId][1]['temp']:
        temp = '-af "'
        for key in s_opts[serverId][1]['temp']:
          temp += s_opts[serverId][1]['temp'][key]
        temp = temp[:-1] + '"'
        return temp
      else:
        return ''
    else:
      return ''


  def reseteffects(self,id):
    if id in s_opts:
      if s_opts[id][1]['temp']:
        s_opts[id][1]['temp'].clear()
    
  
  async def addedtoqueue(self,ctx,data,playlist,position: int,thumbnail=None):
    serverId = ctx.guild.id
    if position == 0:
      position = "Currently Playing"
    else:
      position = str(position)
    if isinstance(data['duration'],int) and data['duration'] != 0:
      duration = self.toHMS(data['duration'])
    else:
      duration = "Livestream"
    if position != "Currently Playing":
      dtp = self.toHMS(self.durationtillplay(serverId,int(position))) 
    else:
      dtp = "Now"
    if not playlist:
      notif = discord.Embed(title="Song Added to queue",description="**["+data.get('title')+"]("+data.get('url')+")**",colour= random.randint(0, 0xffffff))
      notif.add_field(name="Till Played",value=dtp if not data.get('ls') and dtp else "livestream" ,inline=True)
      notif.add_field(name="Song Duration",value=duration if not data.get('ls') else "livestream",inline=True)
      notif.add_field(name="Position",value=position,inline=False)
      if thumbnail:
        notif.set_thumbnail(url=thumbnail)
      
    else:
      notif = discord.Embed(title="Playlist added/being added to queue",description="**["+data.get('title')+"]("+data.get('url')+")**",colour= random.randint(0, 0xffffff))
      notif.add_field(name="**Till Played**",value="`"+dtp+"`",inline=True)
      notif.add_field(name="**Song Duration**",value="`"+duration+"`",inline=True)
      notif.add_field(name="**Position**",value=position,inline=False)
      if thumbnail:
        notif.set_thumbnail(url=thumbnail)
      notif.set_footer(text="`Playlist info may take some time.`")
    await ctx.send(embed=notif)

    


  def durationtillplay(self,id,position):
   td = 0
   if id in db:
     for i in range(position-1):
       td += db[id][i].get('duration')
   if id in self.player:
    if self.player[id].timeq[2] == 0:
      timepassed = int(time.time()-(self.player[id].timeq[0]+self.player[id].timeq[1]))
    else:
      timepassed = int(self.player[id].timeq[2]-self.player[id].timeq[0])
    if 'speed' in s_opts[id][1]['temp']:
      if len(s_opts[id][1]['temp']['speed'])> 12:
        timepassed = timepassed * 4
      else:
        timepassed = int(timepassed *float(s_opts[id][1]['temp']['speed'].split("=")[1][:-1]))
    if timepassed < self.player[id].duration:
      td += self.player[id].duration - timepassed
   return td
    
  def toHMS(self,s):
    if isinstance(s,int):
      if s > 36000:
        return "%02d:%02d:%02d" % (s/60**2, s/60%60, s%60)
      elif s > 3600:
        return "%d:%02d:%02d" % (s/60**2, s/60%60, s%60)
      elif s > 600:
        return "%02d:%02d" %(s/60%60, s%60)
      else:
        return "%d:%02d" %(s/60%60, s%60)
    else:
      return ""

  
  @commands.cooldown(15,604800,type=commands.BucketType.member)
  @commands.command(aliases=['dl'],pass_context = True)
  async def download(self,ctx,*,url):
    member = ctx.author
    authorId = str(ctx.author.id)
    dlopts ={
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }], 
    'outtmpl':"./download/"+authorId+"/%(title)s.%(ext)s",
    'default_search': 'auto',
    'max_filesize': 60000000,
    'quiet': True,
    'noplaylist': True,
    }
    with yt_dlp.YoutubeDL(dlopts) as ydl:
      info = ydl.extract_info(url,download=False)
      if info['duration'] > 600 or info['duration'] == 0:
        await ctx.send('Song duration can not be more than 10 mins')
      else:
        try:
          os.makedirs('./download/'+authorId)
          ydl.download([url])
        except DownloadError:
          await ctx.send('Download failed.Make sure file is smaller than 60mb.')
    for file in os.listdir('./download/'+authorId):
      if file.endswith('.mp3'):
        user = await member.create_dm()
        await user.send(file=discord.File(r'./download/'+authorId+'/'+file))
      shutil.rmtree('./download/'+authorId)
      break
    


def setup(bot):
  bot.add_cog(Music(bot))
  