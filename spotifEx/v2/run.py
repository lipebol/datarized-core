from asyncio import (
    AbstractEventLoop, get_running_loop,
    run, run_coroutine_threadsafe, sleep
)
from common.fabric import Make
from common.notific import Notific
from common.utilize import Use
from common.storage import Stor
from concurrent.futures import Future, ProcessPoolExecutor
from datetime import timedelta
from dbus import Array, Dictionary, SessionBus, String
from dbus.mainloop.glib import DBusGMainLoop
from glob import glob
from gi.repository import GLib
from os import remove
from spotifEx.spotify_for_developers import WebAPI
from threading import Lock, Thread


class init:

    _lock = Lock()

    @staticmethod
    def metadata(event_loop: AbstractEventLoop):
        def handler_function(
            interface: String, 
            changed_properties: Dictionary, 
            invalidated_properties: Array
        ):
            changed_properties = Use.jsonific(
                data=changed_properties, to_string=True, to_objectpy=True
            )
            if not changed_properties.get('PlaybackStatus'):
                if not (metadata := changed_properties.get('Metadata')):
                    raise Exception('There was probably an error connecting to DBUS.')
                elif '/com/spotify/ad/' not in (trackid := metadata.get('mpris:trackid')):
                    setattr(
                        Use, 'wal_data', Make.data(
                            created_date=str((now := Use.date(Use.now())).date()),
                            created_time=str(now.hour)
                        )
                    )
                    if init.add_log_id((trackid := trackid.split('/')[-1])):
                        run_coroutine_threadsafe(
                            WebAPI.access(trackid), event_loop
                        ).add_done_callback(init.track)
                    else:
                        Use.wal_data['track'] = {'trackid': trackid}
                        Use.jsonific(data=Use.wal_data, jsonl=True)
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
    def add_log_id(trackid: str):
        with init._lock:
            if Use.start_date != (new_date := Use.now(all=False)):
                remove(Use.walfile(id=True))
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
            Notific.exception(error)
            return
        Use.wal_data['track'] = track
        Use.jsonific(data=Use.wal_data, jsonl=True)

    @staticmethod
    def _spotifEx():
        try:
            wals = set(glob(f'{(wal_current := Use.walfile()).parent}/*'))
            wals.discard(str(wal_current))
            if wals:
                for wal in wals:
                    daylist = (
                        tmp_table := Use.jsonific(path=wal, jsonl=True).flatten()
                    ).drop_null().append_column(
                        'track.listen', [
                            tmp_table.group_by('track.trackid')
                            .aggregate([([], 'count_all')])
                            .column('count_all')
                        ]
                    ).cast(target_schema=Use.arrow_schema)
                    Stor.insert(daylist, partition=['created_date', 'created_time'])
                    remove(wal)
        except Exception as error:
            Notific.exception(error)

    @staticmethod
    async def spotifEx(
        executor: ProcessPoolExecutor,
        event_loop: AbstractEventLoop
    ):
        while True:
            try:
                await event_loop.run_in_executor(executor, init._spotifEx)

                target_time = (
                    now := Use.date(Use.now())
                ).replace(hour=0, minute=5, second=0, microsecond=0)

                if now >= target_time:
                    target_time += timedelta(days=1)

                timer_message = {
                    'h': int(
                        (timer := (target_time - now).total_seconds())//3600
                    ), 'm': f'{int((timer%3600)//60):02d}'
                }

                Use.info(
                    Use.stringific(
                        timer_message, template=Use.variable('TIMER_MESSAGE')
                    )
                )

                await sleep(timer)
            except Exception as error:
                Notific.exception(error)
                await sleep(300)

    @staticmethod
    async def run():

        Use.info(Use.log_id)

        Thread(
            target=init.metadata, daemon=True,
            args=((event_loop := get_running_loop()),)
        ).start()

        with ProcessPoolExecutor(max_workers=1) as executor:
            await init.spotifEx(executor, event_loop)


if __name__ == '__main__':
    try:
        run(init.run())
    except KeyboardInterrupt:
        Use.info('Exit.')