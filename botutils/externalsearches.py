from abc import ABC, abstractmethod

from youtube_search import YoutubeSearch 
import json  

class Searches(ABC):
    
    @abstractmethod
    def search():
        pass

    @abstractmethod
    def multi_search():
        pass

class YoutubeSearch(Searches):

    @staticmethod      
    def search(request:str):
          try:
            ytrequest = json.loads(YoutubeSearch(request, max_results=1).to_json())
            request = 'https://www.youtube.com/watch?v='+str(ytrequest['videos'][0]['id'])
            return request
          except Exception as e:
            print(e)
            return None

    @staticmethod
    def multi_search(request:str,index:int):
        pass