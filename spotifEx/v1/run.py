from asyncio import run
from bson.objectid import ObjectId
from dbus import Interface, PROPERTIES_IFACE, SessionBus
from common.databases import MongoDB
from common.fabric import Make
from common.notific import Notific
from common.utilize import Use
from pyarrow import Table, array
from spotifEx.spotify_for_developers import WebAPI


class init:

    Use.variable('DATARIZED_CORE_NAME', add='spotifEx')
 
    @staticmethod
    def metadata() -> dict:
        try:
            dbus = Interface(
                SessionBus().get_object(
                    'org.mpris.MediaPlayer2.spotify', '/org/mpris/MediaPlayer2'
                ), PROPERTIES_IFACE
            ).Get('org.mpris.MediaPlayer2.Player', 'Metadata')
            if (dbus := Use.jsonific(data=dbus, to_string=True, to_objectpy=True)):
                return dict((key.split(':')[1], value) for key, value in dbus.items())
        except Exception as error:
            Use.info(error)

    @staticmethod
    def genres(genre: dict, collection='genres') -> str:
        if isinstance(genre, dict):
            return find[0].get('_id') if (
                find := MongoDB.select(collection, filter=genre, fields={'_id': 1})
            ) else MongoDB.insert(collection, data=genre)

    @staticmethod
    def artists(artists: list) -> object:
        for artist in artists:
            if (genres := artist.get('genres')):
                artist['genres'] = list(map(init.genres, genres))
            yield MongoDB.insert('artists', data=artist) if not (
                id := artist.get('id')) else ObjectId(id)
                
    @staticmethod
    def markets(available_markets: list) -> object:
        ISO_3166_1 = MongoDB.select('ISO_3166-1', database='common', _id=True)
        for join_type in ['right outer','left anti']:
            yield ISO_3166_1.join(
                Table.from_arrays([array(available_markets)], 
                names=['code']), keys='code', join_type=join_type
            ).select([0]).drop_null().to_pydict().get('_id')
    
    @staticmethod
    def album(album: dict) -> object:
        if (markets := album.get('available_markets')):
            album['available_markets'], album['no_available_markets'] = tuple(
                init.markets(album.get('available_markets'))
            )
        return MongoDB.insert('albums', data=album) if not (
            id := album.get('id')) else ObjectId(id)
            
    @staticmethod
    def daylist(track: str | dict, collection='daylists') -> str | dict:
        if isinstance(track, dict):
            if (track := track.get('id')):
                if (
                    find := MongoDB.select(
                        collection, fields={'listen': 1, '_id': 0}, 
                        filter=(
                            daylistfilter := {
                                'date': Use.now(all=False), 'track': track
                            }
                        )
                    )
                ):
                    return MongoDB.update(
                        collection, filter=daylistfilter, 
                        update={'listen': find[0].get('listen')+1}
                    )
        return MongoDB.insert(
            collection, data=Make.data(track=track, date=Use.now(all=False))
        )

    @WebAPI.access
    @staticmethod
    def spotifEx(track: dict):
        if not (error := track.get('error')):
            if not track.get('id'):
                track['artists'] = list(init.artists(track.get('artists')))
                track['album'] = init.album(track.get('album'))
                track = str(MongoDB.insert('tracks', data=track))
            return init.daylist(track)
        Use.info(error)

    @staticmethod
    async def run(trackid: str):
        if MongoDB.setconfig():
            if (metadata := init.metadata()):
                if (newtrackid := metadata.get('trackid')) != trackid:
                    if '/com/spotify/ad/' not in newtrackid:
                        Use.info(await init.spotifEx(newtrackid))
                        return newtrackid
                return trackid
            return 'Offline'

if __name__ == '__main__':
    try:
        trackid = None
        while (trackid := run(init.run(trackid))):
            Use.info(f'v1 ({trackid})')
    except KeyboardInterrupt:
        Use.info('Exit.')