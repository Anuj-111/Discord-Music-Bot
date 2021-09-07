from pydantic import BaseModel,BaseConfig


class MyModel(BaseModel): #Just useful to have
    def __hash__(self):
        return hash((type(self),) + tuple(self.__dict__.values()))