from asyncio import AbstractEventLoop, Event, get_running_loop, run, run_coroutine_threadsafe
from common.fabric import Make
from common.notific import Notific
from common.utilize import Use
from common.storage import Stor
from concurrent.futures import Future
from dbus import Array, Dictionary, SessionBus, String
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib
from spotifEx.spotify_for_developers import WebAPI
from threading import Lock, Thread


class init:

    _lock = Lock()

    @staticmethod
    def add_log_id(trackid: str):
        with init._lock:
            if Use.start_date != (new_date := Use.now(all=False)):
                Use.start_date, Use.log_id = new_date, set()
            if trackid not in Use.log_id:
                Use.log_id.add(trackid)
                with open(Use.walfile(id=True), 'a') as file:
                    file.write(trackid + '\n')
                Use.info(Use.log_id)
                return True

    @staticmethod
    def track(response: Future):
        if (error := (track := response.result()).get('error')):
            Use.info(error)
        Use.jsonific(data=track, jsonl=True)
 
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
                    if init.add_log_id((trackid := trackid.split('/')[-1])):
                        run_coroutine_threadsafe(
                            WebAPI.access(trackid), event_loop
                        ).add_done_callback(init.track)
                    else:
                        Use.jsonific(data={'trackid': trackid}, jsonl=True)
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

    # print(track)
    # print(Table.from_pylist([track], schema=Make.schema('Track_v2')))

    @staticmethod
    async def run():
        Use.info(Use.log_id)
        Thread(
            target=init.metadata, daemon=True,
            args=((event_loop := get_running_loop()),)
        ).start()

        await Event().wait()


if __name__ == '__main__':
    try:
        run(init.run())
    except KeyboardInterrupt:
        Use.info('Exit.')