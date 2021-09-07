from source import player
from botutils.extra import(
    toHMS
)


import os
import shutil
import asyncio




import discord
from discord.ext import commands
import yt_dlp
from yt_dlp import DownloadError
import lyricsgenius
genius = lyricsgenius.Genius("6U9CZ_uiDd6jCu7aLHD1Muc5JfDzy1FOueTIx4hrU4gHVxSwFBvHYEjLfWebxz7o")


class Misc(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    @commands.command(aliases=['sv'])
    async def save(self,ctx):
      if isinstance(ctx.channel, discord.DMChannel):
        await ctx.send(f'Use {self.bot.user.name} in a server please.')
        return None
      
      serverId = ctx.guild.id
      if serverId in player:
        embed = discord.Embed(title="**["+player[serverId].title+"]"+"("+player[serverId].url+")**",description = "```Song requested by: "+player[serverId].author+"||"+toHMS(player[serverId].duration),colour = 0xffa826)
        embed.set_footer(text=f"`Saved by {self.bot.user.name} in "+ctx.guild+" at "+str(ctx.message.created_at)+"`")
        user = await ctx.author.create_dm()
        await user.send(embed=embed)
    

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

    @commands.command(pass_context = True)
    async def lyrics(self,ctx,*,text=None):
      if not text:
        if ctx.guild.id in player:
          if player[ctx.guild.id].tags:
            words = player[ctx.guild.id].tags
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
  


def setup(bot):
  bot.add_cog(Misc(bot))