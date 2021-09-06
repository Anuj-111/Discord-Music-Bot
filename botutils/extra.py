"""Just random useful functions"""
from storage import(
    tracks,
    s_opts
)

import time
import asyncio




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


def progressbar(self,timepassed,duration):
    temp = ["▬","▬","▬","▬","▬","▬","▬","▬","▬","▬","▬","▬","▬","▬","▬","▬","▬","▬","▬","▬","▬","▬","▬","▬","▬"]
    temp.insert(int(timepassed/duration*100/4),"🔴")
    return "**|"+"".join(temp)+"|**"

def wslice(self,word,value):
    word.replace("**","")
    if len(word) > value:
      return word[:value-3]+"..."
    else:
        return word

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

def durationtillplay(self,id,position):
   td = 0
   if id in tracks:
     for i in range(position-1):
       td += tracks[id][i].get('duration')
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

