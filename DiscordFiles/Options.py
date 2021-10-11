"""Options.py are for commands that manipulate the audio source's attributes."""

from source import(
    Source,
    player
)
from storage import(
    s_opts
)
from source import playmusic

import time

import discord
from discord.ext import commands

class Options(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    @commands.command(aliases=['vol'])
    async def volume(self,ctx,volume: int):
      if isinstance(ctx.channel, discord.DMChannel):
        await ctx.send(f'Use {self.bot.user.name} in a server please.')
        return None

      voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
      if ctx.author.voice and ctx.author.voice.channel == voice.channel:
        if voice and voice.is_connected():
          if volume > 250:
            await ctx.send("Sorry, volume has been capped to 250%.")
            volume = 250
          if volume < 0:
            await ctx.send("Source volume can't be negative")
            return None


        serverId = ctx.guild.id
        if serverId in player:
          voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
          voice.source.volume = volume / 100
          await ctx.send(f"Volume for this song has been adjusted {volume}%")
        else:
          await ctx.send("Audio source is not connected to channel.")
      else:
        await ctx.send("User not connected to channel")


    @commands.command(pass_context = True)
    async def loop(self,ctx):
      if isinstance(ctx.channel, discord.DMChannel):
        await ctx.send(f'Use {self.bot.user.name} in a server please.')
        return None

      voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
      serverId = ctx.guild.id
      if voice and voice.is_connected() and ctx.author.voice and ctx.author.voice.channel == voice.channel:
        if serverId in player:
          if player[serverId].loop == False:
            player[serverId].set_loop(True)
            await ctx.send("```Song has been looped🔁```")
          else:
            player[serverId].set_loop(False)
            await ctx.send("```Song has been unlooped🔁```")
      else:
        await ctx.send("User or bot not connected to channel")


    @commands.command(aliases=['options','settings'],pass_context = True)
    async def opts(self,ctx,setting: str,*,value=None):
      if isinstance(ctx.channel, discord.DMChannel):
        await ctx.send(f'Use {self.bot.user.name} in a server please.')
        return None
      serverId = ctx.guild.id
      if setting is None:
        pass
      elif setting.lower() == "speed":
        if serverId in player and ctx.voice_client.is_playing():
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
          if player[serverId].timeq[2] == 0:
            timepassed = int(time.time()-(player[serverId].timeq[0]+player[serverId].timeq[1]))
          else:
            timepassed = int(player[serverId].timeq[2]-player[serverId].timeq[0])
          if value1:
            timepassed = int(timepassed*value1)
          if timepassed < player[serverId].duration:
            tme = [timepassed,-int(timepassed*(value**-1))]
            player[serverId].set_repeat(True)
            volume = ctx.voice_client.source.volume
            ctx.voice_client.stop()
            playmusic(ctx,serverId,nowplaying=[player[serverId].data,tme],loop=player[serverId].loop,volume=volume)
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
        if serverId in player and ctx.voice_client.is_playing():
          if '8d' in s_opts[serverId][1]['temp']:
            del s_opts[serverId][1]['temp']['8d']
            await ctx.send("8d sound effect turned off")
          else:
            s_opts[serverId][1]['temp']['8d'] = 'apulsator=hz=0.125,'
            await ctx.send("8d sound effect turned on")

        if player[serverId].timeq[2] == 0:
            timepassed = int(time.time()-(player[serverId].timeq[0]+player[serverId].timeq[1]))
        else:
            timepassed = int(player[serverId].timeq[2]-player[serverId].timeq[0])

        if 'speed' in s_opts[serverId][1]['temp']:
          if len(s_opts[serverId][1]['temp']['speed']) > 12:
            speed = 4
          else:
            speed = float(s_opts[serverId][1]['temp']['speed'].split("=")[1][:-1])
          timetoreset = [int((timepassed*speed)), -int(timepassed)]
        else:
          timetoreset = [(timepassed), -(timepassed)]

        player[serverId].set_repeat(True)
        volume = ctx.voice_client.source.volume
        ctx.voice_client.stop()
        playmusic(ctx,serverId,nowplaying=[player[serverId].data,timetoreset],loop=player[serverId].loop,volume=volume)
        
      elif setting.lower() == "adveq":
        eqsets = discord.Embed(title=f"{self.bot.user.name}'s equalization",description='Pick from 5 standard presets or make your own by clicking the + button. If you are creating your own presets please prepare your settings beforehand. You can find info on the eq settings you can set in ```!opts eqinfo```.',colour=0x02C1ff)
        eqsets.add_field(name="Please Note:",value="Only create custom presets if you know what you're doing. Faulty presets may cause audio clipping and **damage your audio equipment.**",inline=False)
        eqsets.add_field(name='5 Standard presets:',value='1)Bass Boost, 2)High Boost, 3)Classic, 4)Vocal, 5)Rock')
        await self.seteq1(ctx,eqsets)
      
      elif setting.lower() == "soundcloud":
        if s_opts[serverId][1]['search'] != "scsearch:":
          s_opts[serverId][1]['search'] = 'scsearch:'
          await ctx.send("Default_Search set to SoundCloud")
        else:
          s_opts[serverId][1]['search'] = 'auto'
          await ctx.send("Default_Search set to Youtube")


    @commands.command(pass_context = True)
    async def forward(self,ctx,value:int):
      if isinstance(ctx.channel, discord.DMChannel):
        await ctx.send(f'Use {self.bot.user.name} in a server please.')
        return None
      serverId = ctx.guild.id
      
      
      if serverId in player and ctx.voice_client.is_playing() and ctx.author.voice and ctx.author.voice.channel == ctx.voice_client.channel:
        if player[serverId].timeq[2] == 0:
          timepassed = int(time.time()-(player[serverId].timeq[0]+player[serverId].timeq[1]))
        else:
          timepassed = int(player[serverId].timeq[2]-player[serverId].timeq[0])

        speed = 1
        if 'speed' in s_opts[serverId][1]['temp']:
          if len(s_opts[serverId][1]['temp']['speed']) > 12:
            speed = 4
          else:
            speed = float(s_opts[serverId][1]['temp']['speed'].split("=")[1][:-1])


        if player[serverId].is_live is True:
          await ctx.send('Livestream forwarding not setup yet!')
          return None
          """
          if player[serverId].duration is None:
            player[serverId].duration = timepassed*speed
            await ctx.send("You can't forward that far")
            return None
          elif int((timepassed*speed) +value) > player[serverId].duration:
            await ctx.send("You can't forward that far")
            return None
          """
        elif int((timepassed*speed) +value)> player[serverId].duration:
          await ctx.send("You can't forward that far")
          return None
          
        if speed == 1:
          timetoreset = [(timepassed + value), -(timepassed + value)]
        else:
          timetoreset = [int((timepassed*speed) + value), -int(timepassed + (value*(speed**-1)))]

        player[serverId].set_repeat(True)
        volume = ctx.voice_client.source.volume
        ctx.voice_client.stop()
        playmusic(ctx,serverId,nowplaying=[player[serverId].data,timetoreset],loop=player[serverId].loop,volume=volume)
        await ctx.send('**Song has been forwarded '+str(value)+' seconds**')
      else:
        await ctx.send("No song is being played in server vc or user not connected")

    @commands.command(pass_context = True)
    async def rewind(self,ctx,value:int):
      if isinstance(ctx.channel, discord.DMChannel):
        await ctx.send(f'Use {self.bot.user.name} in a server please.')
        return None
      serverId = ctx.guild.id
      if serverId in player and ctx.voice_client.is_playing() and ctx.author.voice and ctx.author.voice.channel == ctx.voice_client.channel:
        if player[serverId].timeq[2] == 0:
          timepassed = int(time.time()-(player[serverId].timeq[0]+player[serverId].timeq[1]))
        else:
          timepassed = int(player[serverId].timeq[2]-player[serverId].timeq[0])


        speed = 1
        if 'speed' in s_opts[serverId][1]['temp']:
          if len(s_opts[serverId][1]['temp']['speed']) > 12:
            speed = 4
          else:
            speed = float(s_opts[serverId][1]['temp']['speed'].split("=")[1][:-1])

        """
        if player[serverId].is_live is True:
          if player[serverId].duration is None or timepassed*speed > player[serverId].duration:
            player[serverId].duration = timepassed*speed
        """

        if player[serverId].is_live is True:
          await ctx.send('Livestream rewinding not setup yet!')
          return None
        elif value > timepassed*speed:
          await ctx.send("You can't rewind that far")
          return None
          
        if speed == 1:
          timetoreset = [(timepassed - value), -(timepassed - value)]
        else:
          timetoreset = [(timepassed - value), -int(timepassed - (value*(speed**-1)))]
        player[serverId].set_repeat(True)
        volume = ctx.voice_client.source.volume
        ctx.voice_client.stop()
        playmusic(ctx,serverId,nowplaying=[player[serverId].data,timetoreset],loop=player[serverId].loop,volume=volume)
        await ctx.send('**Song has been rewinded '+str(value)+' seconds**')
      else:
        await ctx.send("No song is being played in server vc or user not connected")
    


def setup(bot):
  bot.add_cog(Options(bot))