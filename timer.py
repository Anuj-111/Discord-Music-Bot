from storage import s_opts,tracks


import datetime
import time

from discord import utils
from discord.ext import tasks



#responsible for disconnecting bots when not disconnected manually

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
                voice = utils.get(self.bot.voice_clients, guild=guild)
                if voice:
                  voice.cleanup()
                  await voice.disconnect()
              del self.check[str(now.minute)]
        if self.check2:
          if str(now.minute) in self.check2:
            for serverId in self.check2[str(now.minute)]:
              guild = await self.bot.fetch_guild(serverId)
              voice = utils.get(self.bot.voice_clients, guild=guild)
              if voice and len(voice.channel.members) == 1:
                if serverId in tracks:
                  del tracks[serverId]
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


gtimer = None




