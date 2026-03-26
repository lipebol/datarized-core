from asyncio import AbstractEventLoop, get_running_loop, run, run_coroutine_threadsafe
from common.notific import Notific
from common.utilize import Use
from concurrent.futures import Future
from dbus import Array, Dictionary, SessionBus, String
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib
from spotifEx.spotify_for_developers import WebAPI
from threading import Thread


class init:
 
    @staticmethod
    def metadata(event_loop: AbstractEventLoop):
        def handler_function(
            interface: String, 
            changed_properties: Dictionary, 
            invalidated_properties: Array
        ):
            if not 'PlaybackStatus' in str(changed_properties):
                if not (
                    metadata := Use.jsonific(
                        data=changed_properties, to_string=True, 
                        to_objectpy=True
                    ).get('Metadata')
                ):
                    raise Exception('There was probably an error connecting to DBUS.')
                if '/com/spotify/ad/' not in (trackid := metadata.get('mpris:trackid')):
                    run_coroutine_threadsafe(
                        WebAPI.access(trackid), event_loop
                    ).add_done_callback(init.spotifEx)
        try:
            DBusGMainLoop(set_as_default=True)
            SessionBus().add_signal_receiver(
                handler_function, signal_name='PropertiesChanged', 
                dbus_interface='org.freedesktop.DBus.Properties',
                bus_name='org.mpris.MediaPlayer2.spotify',
                path='/org/mpris/MediaPlayer2'
            )
            GLib.MainLoop().run()
        except Exception as error:
            Use.info(error)

    @staticmethod
    def spotifEx(track: Future):
        if not (error := (track := track.result()).get('error')):
            print(track)
            return 
            # if not track.get('id'):
            #     track['artists'] = list(init.artists(track.get('artists')))
            #     track['album'] = init.album(track.get('album'))
            #     track = str(MongoDB.insert('tracks', data=track))
            # return init.daylist(track)
        Use.info(error)

    @staticmethod
    async def run():
        Thread(
            target=init.metadata, daemon=True,
            args=((event_loop := get_running_loop()),)
        ).start()

        await event_loop.create_future()


if __name__ == '__main__':
    try:
        run(init.run())
    except KeyboardInterrupt:
        Use.info('Exit.')