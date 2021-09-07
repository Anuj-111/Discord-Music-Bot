from botutils.extractors import(
    DefaultExtractor, 
    Extractors
)

from botutils.model import MyModel

from botutils.externalsearches import YoutubeSearch

import pydantic
from pydantic.fields import Field
from typing import Optional,FrozenSet



class Video(MyModel):
    video: str = Field(alias='url')
    url: str = Field(alias='webpage_url')
    title: str
    duration: Optional[int] = None
    is_live: Optional[bool] = False
    id: Optional[str] = None
    channel: Optional[str] = None
    thumbnail: Optional[str] = None
    tags: Optional[list[str]] = None

    author: str


    @pydantic.validator("title")
    @classmethod
    def check_title(cls,value):
        value.replace("**","").replace("[","").replace("]","")
        if len(value) > 100:
            return value[:100]
        return value

    @pydantic.validator('tags')
    @classmethod
    def check_tags(cls,value):
        if len(value) > 3:
            return frozenset(value[:3])
        return frozenset(value)
      
   
    class Config:
        allow_mutation = False



    
class FetchVideo():
    def __init__(self):
       self.extractors = {
            "default": DefaultExtractor,
            }
       self.externalsearch = {
           "default": YoutubeSearch,
           "yt": YoutubeSearch
       }

        
    async def get_singlevideo(self,channel,caller:str,request:str,search:str,setting:str="default")->Video:
        try:
            if not "." in request:
                await channel.send(f"`Searching for {request} with {search} settings`")
                request = self.externalsearch[setting]().search(request)

            await channel.send(f"`Attempting to request: {request}`")
            return Video(**await self.extractors[setting]().extract(caller,request,search))
        except Exception as e:
            print(e)
            return None


    async def get_playlist(self,caller:str,request:str,setting:str="default")->list:
        try:
            return [Video(**i) for i in ((await self.extractors[setting]().extract(caller,request,npl=False))['entries'])]
            
        except Exception as e:
            print(e)
            return None








