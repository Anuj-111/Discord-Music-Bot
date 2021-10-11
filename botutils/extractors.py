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
    async def extract(author:str,url:str,search:str='auto', npl:bool=True)-> dict:
        ydl = yt_dlp.YoutubeDL({
        'format': 'bestaudio/best',
        'restrictfilenames': True,
        'noplaylist': npl,
        'playlistend':25,
        'verbose': False,
        'quiet': True, 
        'default_search': search,
        'nocheckcertificate': True,
        'ignoreerrors': True,
        'no_warnings': False,
        'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
        })
      

        try:
          loop = asyncio.get_event_loop()
    
          data = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
          

          if 'entries' in data:
            if npl == False:
              for i in range(len(data['entries'])):
                data['entries'][i]['author'] = author
                return data
            else:
              data['entries'][0]['author'] = author
              data['entries'][0]['url'] = data['entries'][0]['formats'][0]['url']
              return data['entries'][0]
          else:
            data['author'] = author
            return data
        except Exception as e:
          print(e)
          return None




