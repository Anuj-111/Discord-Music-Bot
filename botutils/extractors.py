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
    async def extract(author:str,url:str,search:str, npl:str=True):
        ytdl_format_options = {
            'format': 'bestaudio/best',
            'restrictfilenames': True,
            'noplaylist': npl,
            'playliststart': 2,
            'playlistend':25,
            'verbose': False,
            'quiet': True, 
            'default_search': search,
            'nocheckcertificate': True,
            'ignoreerrors': True,
            'no_warnings': False,
            'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
        }
        ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

        try:
          loop = asyncio.get_event_loop()
          data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
          data['author'] = str(author)
          return data
        except Exception as e:
          print(e)
          return None




