from enum import Enum,auto
import asyncio
from abc import ABC, abstractmethod

import yt_dlp


class Extractors(ABC):
    
    @abstractmethod
    async def extract():
        pass

class DefaultExtractor(Extractors):

    """Fetches video info from yt-dlp"""
    @staticmethod
    async def extract(author:str,url:str,search:str=None, npl:bool=True)-> dict:
        ydl = yt_dlp.YoutubeDL({'format': 'bestaudio/best',
              'restrictfilenames': True,
              'noplaylist': npl,
              'forceduration': "auto",
              'playliststart':1,
              'playlistend':25,
              'verbose': False,
              'quiet': True, 
              'default_search': 'auto',
              'nocheckcertificate': True,
              'ignoreerrors': True,
              'no_warnings': False,
              'source_address': '0.0.0.0' })
      

        try:
          loop = asyncio.get_event_loop()
          data = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
          
          if npl is False:
            if 'entries' in data:
              for i in range(len(data['entries'])):
                data['entries'][i]['author'] = author
          else:
            data['author'] = author
 
          return data
        except Exception as e:
          print(e)
          return None




