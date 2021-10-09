"""Queue.py is for commands that have to do with displaying or manipulating the queue. """

from botutils.extra import(
  progressbar,
  wslice,
  toHMS,
  pages,
)
import time
from source import player
from storage import(
  tracks,
  s_opts
)

import random

import discord
from discord.ext import commands

class Queue(commands.Cog):
    def __init__(self,bot):
        self.bot = bot
    
    @commands.command(aliases=['q'],pass_context= True)
    async def queue(self,ctx):
      if isinstance(ctx.channel, discord.DMChannel):
        await ctx.send(f'Use {self.bot.user.name} in a server please.')
        return None
      serverId = ctx.guild.id
      serverId = serverId
      count = 1
      embeds = []
      embed = discord.Embed(title=str(ctx.guild.name)+"'s Queue", colour= 0x8e0beb)
      if serverId in player:
        if player[serverId].loop == True:
          embed.set_footer(text="`Loop:`✔️")
        else:
          embed.set_footer(text="`Loop:`❌")
        embed.add_field(name="**Now Playing**",value="["+str(wslice(player[serverId].title,50))+"]("+player[serverId].url+")`|"+toHMS(player[serverId].duration)+"| Requested by: "+player[serverId].author+"`",inline=False)
  
        if serverId in tracks: 
          for value,song in enumerate(tracks[serverId]):
            if value == 0:
              embed.add_field(name='Rest in Queue',value=str(value+1)+")["+wslice(song.title,50)+"]("+song.url+")`|"+toHMS(song.duration)+"| Requested by: "+song.author+"`",inline = False)
            else:
              embed.add_field(name='\u200b',value=str(value+1)+")["+wslice(song.title,50)+"]("+song.url+")`|"+toHMS(song.duration)+"| Requested by: "+song.author+"`",inline = False)
            if (value+2) % 10 == 0: 
              embeds.append(embed)
              count += 1
              embed = discord.Embed(title=str(ctx.guild.name)+"'s Queue'("+str(count)+")",colour=0x8e0beb)
        embeds.append(embed)
        if len(embeds) > 1:
          await pages(self.bot,ctx.message,embeds)
        else:
          await ctx.send(embed=embeds[0])
      
      else:
        await ctx.send("**No songs in queue**")

    @commands.command(aliases=['np','nowplay'])
    async def nowplaying(self,ctx):
      if isinstance(ctx.channel, discord.DMChannel):
        await ctx.send(f'Use {self.bot.user.name} in a server please.')
        return None
      
      serverId = ctx.guild.id
      if serverId in player:
        if not player[serverId].is_live:
          if player[serverId].timeq[2] == 0:
            timepassed = int(time.time()-(player[serverId].timeq[0]+player[serverId].timeq[1]))
          else:
            timepassed = int(player[serverId].timeq[2]-player[serverId].timeq[0])
          
          if 'speed' in s_opts[serverId][1]['temp']:
            if len(s_opts[serverId][1]['temp']['speed'])> 12:
              timepassed = timepassed * 4
            else:
                timepassed = int(timepassed *float(s_opts[serverId][1]['temp']['speed'].split("=")[1][:-1]))

            if timepassed > player[serverId].duration:
             timepassed = player[serverId].duration
          bar = progressbar(timepassed,player[serverId].duration)
          queuetime = toHMS(timepassed)+"/"+toHMS(player[serverId].duration)
        else:
            queuetime = "N/A(Livestream)"
            bar = progressbar(0,100)
            
        embed = discord.Embed(title="`"+queuetime+"`",description=bar,colour=0x000000)
        embed.set_author(name='Nowplaying: '+player[serverId].title,url=player[serverId].url,icon_url='https://cdn.discordapp.com/attachments/819709519063678978/882819723950182480/noice.gif')
        embed.set_image(url=player[serverId].thumbnail)
        if player[serverId].channel:
          embed.set_footer(text="From: "+player[serverId].channel+" and Requested by: "+player[serverId].author)
        else:
          embed.set_footer(text="Requested by: "+player[serverId].author)
        await ctx.send(embed=embed)
      else:
        await ctx.send("No songs are currently playing")
      
        
    @commands.command(aliases=['sh'],pass_context = True)
    async def shuffle(self,ctx):
      if isinstance(ctx.channel, discord.DMChannel):
        await ctx.send(f'Use {self.bot.user.name} in a server please.')
        return None
      serverId = ctx.guild.id
      if serverId in tracks:
        random.shuffle(tracks[serverId])
        await ctx.send("`Song queue has been shuffled 🔀`")

    @commands.command(aliases=['rp'],pass_context = True)
    async def replay(self,ctx):
      if isinstance(ctx.channel, discord.DMChannel):
        await ctx.send(f'Use {self.bot.user.name} in a server please.')
        return None
      serverId = ctx.guild.id
      if serverId in player:
        tracks[serverId].insert(0,player[serverId].data)
        await ctx.send("Song has been requeued🔂")

    @commands.command(aliases=['mv'],pass_context = True)
    async def move(self,ctx,value1:int,value2:int):
      if isinstance(ctx.channel, discord.DMChannel):
        await ctx.send(f'Use {self.bot.user.name} in a server please.')
        return None
      serverId = ctx.guild.id
      if value1 < 1 or value2 < 1 or value1 > len(tracks[serverId]) or value2 > len(tracks[serverId]):
        await ctx.send("Positions are out of query bounds")
      else:
        tracks[serverId][value1-1],tracks[serverId][value2-1] = tracks[serverId][value2-1],tracks[serverId][value1-1]
    

    @commands.command(aliases=['clea','clean'])
    async def clear(self,ctx):
      if isinstance(ctx.channel, discord.DMChannel):
        await ctx.send(f'Use {self.bot.user.name} in a server please.')
        return None
      serverId = ctx.guild.id
      author = ctx.message.content.split(" ",1)[1] if len(ctx.message.content.split(" ",1)) > 1 else None
      if author is None:
        if serverId in tracks and len(tracks[serverId]) > 0:
          tracks[serverId].clear()
          await ctx.send("```Queue has been Cleared 🧹```")
        else:
          await ctx.send("```Nothing to Clear ¯\_(ツ)_/¯```")
        return None
      if serverId in tracks:
        guild = self.bot.get_guild(int(serverId))
        author = int(author[3:-1])
        name = await guild.fetch_member(author)
        if name is None:
          return
        maxv = len(tracks[serverId])
        count = 0
        i = 0
        while i < maxv:
          if tracks[serverId][i].author == str(name):
            del tracks[serverId][i]
            maxv -= 1
            count += 1      
          else:
            i += 1
      
        await ctx.send("```css\n"+str(count)+" entries by:"+str(name.name)+" have been cleared from Queue 🧹```")




  

def setup(bot):
  bot.add_cog(Queue(bot))
