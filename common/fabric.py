from .loadEx import load
from dataclasses import asdict, dataclass, field
from inspect import getmembers, isclass, signature
from pyarrow import _flight
from sys import modules

@dataclass
class Genre:
    name: str
    url: str

@dataclass
class Daylist:
    track: str
    date: str
    listen: int = field(default=1)

@dataclass
class DivvyBikes_Files:
    filename: str
    last_modified: str
    id: str
    size: str

@dataclass
class Arrow_Flight_RPC_Info:
    schema: _flight.SchemaResult
    rows: int
    size: int
    ticket: _flight.Ticket
    expiration_time: str = field(default='')

@dataclass
class Arrow_Flight_RPC_Conn:
    client: _flight.FlightClient
    authenticate: _flight.FlightCallOptions
    descriptor: _flight.FlightDescriptor

@dataclass
class Arrow_Flight_RPC_Extras:
    command: str = field(default='')
    path: str = field(default='')

@dataclass
class Arrow_Flight_RPC:
    info: Arrow_Flight_RPC_Info
    conn: Arrow_Flight_RPC_Conn
    extras: Arrow_Flight_RPC_Extras

@dataclass
class Event_Date:
    dateTime: str
    timeZone: str = field(default=load.timezone_default())

@dataclass
class Event:
    summary: str
    description: str
    colorId: str
    start: dict
    end: dict 
    visibility: str = field(default="public")


class mount:

    @property
    def __classes(self):
        for classname in [
            classname for classname, classdesc in getmembers(
                modules[__name__], isclass
            ) if load.path(__file__).name.strip('.py') in str(classdesc) 
            and classname != self.__class__.__name__
        ]:
            if (params := signature(globals()[classname].__init__).parameters):
                yield {
                    classname: [
                        key for key, value in params.items() 
                        if '=' not in str(value) and key != 'self'
                    ]
                }

    @staticmethod
    def data(*, classname: str | None = None, **kwargs):
        if not classname:
            for classEx in mount().__classes:
                if list(classEx.values())[0] == list(kwargs.keys()):
                    classname = ''.join(classEx.keys())
                    break
        if (data := globals()[classname](**kwargs)):
            if 'Arrow_Flight' in classname:
                return data
            return asdict(data)
        
        
        
