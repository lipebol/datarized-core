from .utilize import Use
from dataclasses import asdict, dataclass, field as dataclassfield
from inspect import getmembers, isclass, signature
from pyarrow import _flight, binary, DataType, dictionary, field, list_, schema, Schema, struct
from sys import modules

# 'int' (signed) instead of 'uint' (unsigned) for dictionary indices.
# 'fixed_size_binary[22]' for Spotify IDs to eliminate offset overhead.

@dataclass
class Images_v2:
    struct: DataType = dataclassfield(
        default_factory=lambda: struct([
            field(
                'url', 'string', nullable=False, metadata={
                    'url': 'The direct web link to the hosted image file.'
                }
            ),
            field(
                'width', dictionary('int8', 'uint16'), nullable=False, metadata={
                    'width': 'The horizontal measurement of the image in pixels.'
                }
            ),
            field(
                'height', dictionary('int8', 'uint16'), nullable=False, metadata={
                    'height': 'The vertical measurement of the image in pixels.'
                }
            )
        ])
    )

@dataclass
class Copyrights_v2:
    struct: DataType = dataclassfield(
        default_factory=lambda: struct([
            field(
                'text', 'string', nullable=False, metadata={
                    'text': (
                        'The official legal notice, including '
                        'the year and the names of the rights holders.'
                    )
                }
            ), 
            field(
                'type', dictionary('int8', 'string'), nullable=False, metadata={
                    'type': (
                        'The specific legal category of the copyright: \n'
                        '-"C": Stands for Composition (the underlying lyrics and melody).\n'
                        '-"P": Stands for Phonogram (the actual sound recording or master).'
                    )
                }
            )
        ])
    )

@dataclass
class Album_v2:
    struct: DataType = dataclassfield(
        default_factory=lambda: struct([
            field(
                'albumid', binary(22), nullable=False, metadata={
                    'albumid': 'A unique identifier for the collection of songs.'
                }
            ),
            field(
                'name', 'string', nullable=False, metadata={
                    'name': 'The official title of the album.'
                }
            ),
            field(
                'album_type', dictionary('int8', 'string'), nullable=False, metadata={
                    'album_type': 'Defines if the release is a full "album" an "EP" or a "single".'
                }
            ),
            field(
                'release_date', 'string', nullable=False, metadata={
                    'release_date': 'The official day the music was made available to the public.'
                }
            ),
            field(
                'external_url', 'string', nullable=False, metadata={
                    'external_url': 'A direct link to stream or view the album on the platform.'
                }
            ),
            field(
                'images', list_(Images_v2().struct), metadata={
                    'images': (
                        'A list of cover art available in various '
                        'resolutions (small, medium, large).'
                    )
                }
            ),
            field(
                'total_tracks', 'uint8', nullable=False, metadata={
                    'total_tracks': 'The total number of songs included in this album.'
                }
            ),
            field(
                'copyrights', list_(Copyrights_v2().struct), metadata={
                    'copyrights': (
                        'Legal ownership details (C for compositions, '
                        'P for the phonographic sound recording).'
                    )
                }
            ),
            field(
                'label', dictionary('int16', 'string'), nullable=False, metadata={
                    'label': (
                        'The record company or organization responsible for '
                        'distributing the music.'
                    )
                }
            )
        ])
    )

@dataclass
class Genre_v2:
    struct: DataType = dataclassfield(
        default_factory=lambda: struct([
            field(
                'name', dictionary('int16', 'string'), nullable=False, metadata={
                    'name': 'Musical style associated with the artist.'
                }
            ),
            field('about', 'string', nullable=True, metadata={'about': ''})
        ])
    )

@dataclass
class Artist_v2:
    struct: DataType = dataclassfield(
        default_factory=lambda: struct([
            field(
                'artistid', binary(22), nullable=False, metadata={
                    'artistid': 'A unique identifier for each performer.'
                }
            ),
            field(
                'name', 'string', nullable=False, metadata={
                    'name': 'The stage name of the musician or group.'
                }
            ),
            field(
                'profile', 'string', nullable=False, metadata={
                    'profile': 'A link to the artist\'s main page or biography.'
                }
            ),
            field(
                'followers', 'uint32', nullable=False, metadata={
                    'followers': (
                        'The total count of users following the '
                        'artist on the platform.'
                    )
                }
            ),
            field(
                'images', list_(Images_v2().struct), metadata={
                    'images': (
                        'A list of cover art available in various '
                        'resolutions (small, medium, large).'
                    )
                }
            ),
            field(
                'genres', list_(Genre_v2().struct), metadata={
                    'genres': 'A list of musical styles associated with the artist.'
                }
            )
        ])
    )

@dataclass
class Track_v2:
    schema: Schema = dataclassfield(
        default_factory=lambda: schema([
            field(
                'trackid', binary(22), nullable=False, metadata={
                    'trackid': 'A unique alphanumeric identifier for the specific song.'
                }
            ),
            field(
                'name', 'string', nullable=False, metadata={
                    'name': 'The official title of the track.'
                }
            ),
            field(
                'album', Album_v2().struct, metadata={
                    'album': (
                        'Comprehensive details about the music collection containing this '
                        'track, including its title, artwork, and legal publishing information.'
                    )
                }
            ),
            field('artists', list_(Artist_v2().struct), metadata={'artists': ''}),
            field(
                'url', 'string', nullable=False, metadata={
                    'url': 'A direct link to stream or view the track on the platform.'
                }
            ),
            field(
                'duration_ms', 'uint32', nullable=False, metadata={
                    'duration_ms': 'The total length of the song measured in milliseconds.'
                }
            ),
            field(
                'popularity', 'uint8', nullable=False, metadata={
                    'popularity': (
                        'A score (usually 0-100) indicating how trending or widely '
                        'streamed the song is.'
                    )
                }
            ),
            field(
                'explicit', 'bool', nullable=False, metadata={
                    'explicit': (
                        'A true/false flag indicating if the lyrics '
                        'contain adult content.'
                    )
                }
            ),
            field(
                'track_number', 'uint8', nullable=False, metadata={
                    'track_number': 'The position of the song within the album\'s tracklist.'
                }
            ),
            field(
                'disc_number', 'uint8', nullable=False, metadata={
                    'disc_number': (
                        'The volume or disc index (usually "1" unless '
                        'it\'s a multi-disc set).'
                    )
                }
            ),
            field(
                'isrc', 'string', nullable=False, metadata={
                    'isrc': (
                        'The International Standard Recording Code, a unique '
                        '"serial number" for the specific sound recording.'
                    )
                }
            )
        ])
    )

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
    expiration_time: str = dataclassfield(default='')

@dataclass
class Arrow_Flight_RPC_Conn:
    client: _flight.FlightClient
    authenticate: _flight.FlightCallOptions
    descriptor: _flight.FlightDescriptor

@dataclass
class Arrow_Flight_RPC_Extras:
    command: str = dataclassfield(default='')
    path: str = dataclassfield(default='')

@dataclass
class Arrow_Flight_RPC:
    info: Arrow_Flight_RPC_Info
    conn: Arrow_Flight_RPC_Conn
    extras: Arrow_Flight_RPC_Extras

@dataclass
class Genre:
    name: str
    url: str

@dataclass
class Daylist:
    track: str
    date: str
    listen: int = dataclassfield(default=1)
    
@dataclass
class Event_Date:
    dateTime: str
    timeZone: str = dataclassfield(default=Use.timezone_default())

@dataclass
class Event:
    summary: str
    description: str
    colorId: str
    start: dict
    end: dict 
    visibility: str = dataclassfield(default="public")


class Make:

    @property
    def __classes(self):
        for classname in [
            classname for classname, classdesc in getmembers(
                modules[__name__], isclass
            ) if Use.path(__file__).name.strip('.py') in str(classdesc)
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
            for classes in Make().__classes:
                if list(classes.values())[0] == list(kwargs.keys()):
                    classname = ''.join(classes.keys())
                    break
        if (data := globals()[classname](**kwargs)):
            if 'Arrow_Flight' or 'Track_v2' in classname:
                return data
            return asdict(data)
        
        
        
