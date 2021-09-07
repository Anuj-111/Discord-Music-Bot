import time

from storage import(
    s_opts,
    tracks
)

from timer import gtimer
from botutils.extra import(
    reseteffects,
    getoptions
)

import discord



class Source(discord.PCMVolumeTransformer):
    def __init__(self, source,*,data,timeq=None,loop=False,ls=False,volume=0.50):
        super().__init__(source, volume)
        self.data = data
        self.id = data.id
        self.url = data.url 
        self.title = data.title
        self.duration = data.duration 
        self.thumbnail = data.thumbnail
        self.channel = data.channel
        self.tags = data.tags
        self.author = data.author
        self.ls = data.ls
        self.timeq = timeq
        self.loop = loop
        self.repeat = False
        

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
    def streamvideo(cls,data,ss=0,loop=False,options=None,volume=0.5):
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
      return cls(discord.FFmpegPCMAudio(data.video, **ffmpeg_options),data=data,timeq=[time.time() if not ss else time.time()+ss[1] ,0,0] if not loop else ["looped",0,0],loop=loop,volume=volume) 

player = dict()


def playmusic(ctx,id,nowplaying=None,loop=False,volume=None):
      if nowplaying:
        song_source = Source.streamvideo(nowplaying[0],loop=loop,ss=nowplaying[1],options=getoptions(id),volume=volume)
        player[id] = song_source
        try:
          ctx.voice_client.play(song_source, after=lambda e: reseteffects(id) or playmusic(ctx,id,loop=player[id].loop) if not song_source.repeat else song_source.set_repeat(False))
          return None
        except Exception:
          if not song_source.repeat:
            reseteffects(id) 
            playmusic(ctx,id,loop=player[id].loop)
          else:
            song_source.set_repeat(False)
          return None
      if id in player:
        if player[id].loop == True:
          loop = True
          nowplaying = player[id].data
      if not nowplaying:
        if id in tracks and len(tracks[id]) > 0:
          nowplaying = tracks[id].pop(0)
        else:
          del player[id]
          if not gtimer.checkentry(ctx.guild.id):
            gtimer.setentry(id,1)
          return None 
          
      song_source = Source.streamvideo(nowplaying,loop=loop,options=getoptions(id),volume=s_opts[id][1]['volume'])
      player[id] = song_source
      try:
        ctx.voice_client.play(song_source, after=lambda e: reseteffects(id) or playmusic(ctx,id,loop=player[id].loop) if not song_source.repeat else song_source.set_repeat(False))
        gtimer.delentry(ctx.guild.id)
      except Exception as e:
        print(e)
        if not song_source.repeat:
          reseteffects(id) 
          playmusic(ctx,id,loop=player[id].loop)
        else:
          song_source.set_repeat(False)
        return None