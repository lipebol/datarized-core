from datetime import datetime
from dbus import Interface, PROPERTIES_IFACE, SessionBus
from dotenv import load_dotenv
from inspect import currentframe, getmodule
from glob import glob
import json
from logging import basicConfig, info, INFO
from os import environ, getenv, path, remove
from pathlib import Path
import platform
import pyarrow as arrow
from pytz import timezone
from string import Template
from subprocess import run, PIPE
from time import sleep
from urllib.parse import urlparse
from zipfile import ZipFile


class load:

    load_dotenv()

    basicConfig(
        format='%(asctime)s - %(levelname)s - %(message)s', 
        level=INFO, datefmt='%Y-%m-%d %H:%M:%S'
    )

    @staticmethod
    def widgex(caller=None):
        return load.__caller(currentframe().f_back if not caller else caller)

    @staticmethod
    def envs():
        try:
            for key, value in load.jsonEx(
                path=(tmpfile := load.tmpfile(path='/tmp'))
            ).items():
                if isinstance(value, str):
                    yield load.variable(key, add=value)
        except Exception:
            load.delete(tmpfile)
            return False

    @staticmethod
    def quiet(func):
        def wrapper(*args, **kwargs):
            sleep(1)
            return func(*args, **kwargs)
        return wrapper

    @staticmethod
    def path(
        path_: str | None = None, *,
        join: list | str | None = None,
        user: bool = False
    ) -> Path:
        path_ = Path(path_) if path_ else path.expanduser('~') if user else Path.cwd()
        if join:
            if isinstance(join, str):
                join = [join]
            return path_.joinpath(*join)
        return path_

    @staticmethod
    def checkpath(_path: str) -> bool:
        return path.exists(_path)

    @staticmethod
    def variable(var: str, *, load: bool = True, add: str | None = None) -> str:
        if add:
            environ[var] = add
        return getenv(var) if load else var

    @staticmethod
    def string(values: dict | list, *, template: str | None = None, join: bool = False):
        if join and isinstance(values, list):
            return ', '.join(values)
        elif template and isinstance(values, dict):
            return Template(template).substitute(values)

    @staticmethod
    def jsonEx(
        *, path: str | None = None, data: str | dict | None = None, 
        to_string: bool = False, to_objectpy: bool = False
    ):
        if not path and data:
            if to_string:
                data = json.dumps(data)
            if to_objectpy:
                data = json.loads(data)
            return data
        if path:
            with open(path, 'w' if data else 'r', encoding='utf-8') as _jsonEx:
                if not data:
                    return json.load(_jsonEx)
                json.dump(data, _jsonEx, ensure_ascii=False, indent=5)

    @staticmethod
    def __files(filetype: str, dirname: str):
        return glob(load.variable(filetype) % load.dirdownloads(dirname), recursive=True)
    
    @staticmethod
    def zip_files(with_path=True):
        __zip_files = load.__files(
            'ZIP_FILES', load.__caller(currentframe().f_back)
        )
        if not with_path:
            return [load.path(zip_file).name for zip_file in __zip_files]
        return __zip_files

    @staticmethod
    def csv_files():
        return load.__files('CSV_FILES', load.__caller(currentframe().f_back))

    @staticmethod
    def unzip(zip_file: object, suffix=None) -> str:
        def extract(zip_obj: object, suffix: str, path: str):
            for file in zip_obj.namelist():
                if file.endswith(suffix):
                    yield zip_obj.extract(file, path)           
        with ZipFile(zip_file, 'r') as zip_obj:
            if suffix:
                load.info(
                    "\n%s\n" % '\n'.join(
                        list(extract(zip_obj, suffix, zip_file.parent))
                    )
                )
            return zip_obj.extractall(zip_file.parent)

    @staticmethod
    def readcsv(csv_file: str, fields: list, types: dict, sep=None) -> object:
        load.info(f"Reading file... ({csv_file})")
        return arrow.csv.read_csv(
            csv_file, parse_options=arrow.csv.ParseOptions(delimiter=sep if sep else ';'),
            read_options=arrow.csv.ReadOptions(
                encoding='latin1', column_names=fields, skip_rows=1
            ), convert_options=arrow.csv.ConvertOptions(column_types=types)
        )

    @staticmethod
    def dataset(
        datafile, *, typefile: str, fs: object, 
        types: list | None = None, batch: bool = False
    ):
        load.info(f"Reading file... ({datafile})")
        if (
            dataset := arrow.dataset.dataset(
                datafile, schema=types, format=typefile, filesystem=fs
            )
        ):
            if batch:
                return
            return dataset.to_table() 

    @staticmethod
    def tmpfile(*, path: str, filename: str | None = None) -> str:
        return load.path(path, join='tmp.json' if not filename else f'{filename}.json')

    @staticmethod
    def delete(file: str):
        return remove(file)

    @staticmethod
    def timezone_default(timezone: str | None = None) -> str:
        return 'America/Sao_Paulo' if not timezone else timezone

    @staticmethod
    def now(*, all: bool = True) -> str:
        if (now := datetime.now(tz=timezone(load.timezone_default()))):
            return load.date(now, format='%Y-%m-%d') if not all else now.isoformat()
    
    @staticmethod
    def date(value: str | datetime, *, format: str = '%Y-%m-%dT%H:%M:%S.%f%z'):
        if isinstance(value, (str, datetime)):
            return datetime.strptime(
                value, format
            ) if isinstance(value, str) else value.strftime(format)
   
    @quiet
    @staticmethod
    def info(_info: str) -> str:
        return info(_info)

    @staticmethod
    def uri(value: str):
        return urlparse(value)

    @staticmethod
    def __caller(value: object):
        return load.path(path.dirname(getmodule(value).__file__)).name


class system:

    @staticmethod
    def shell(command: str):
        return run(command, shell=True, stdout=PIPE, text=True).stdout.strip()
    
    @staticmethod
    def dbus(
        name: str | None = None, objectpath: str | None = None, 
        interface: str | None = None, propertie: str | None = None, 
        *, service: str | None = None
    ) -> dict | None:
        try:
            if service:
                name, objectpath, interface, propertie = (
                    load.variable(f'{service.upper()}_DBUS_{var}')
                    for var in ['NAME','OBJECTPATH','INTERFACE','PROPERTIE']
                )
            return load.jsonEx(
                data=Interface(
                    SessionBus().get_object(name, objectpath), PROPERTIES_IFACE
                ).Get(interface, propertie), to_string=True, to_objectpy=True
            )
        except Exception as error:
            load.info(error)

    @staticmethod
    def screen(window_sizes: list) -> object:
        for screen_size, window_size in zip(
            [
                int(size.split()[1]) if "\n" in size else int(size) for size in [
                    system.shell(command) for command in load.variable(
                        f'REPORTIUM_{system._os().upper()}_SCREEN'
                    ).split(';')
                ]
            ], window_sizes):
                yield int(screen_size * window_size)
                yield (screen_size - int(screen_size * window_size)) // 2

    @staticmethod
    def encr(*, variable: str | None = None, value: str | None = None):
        if (load_encr := load.variable('TX808FBP22QE2QTTK')):
            return system.shell(
                load_encr % {
                    "arg": value or f"${variable}",
                    "tangserver": load.variable('TANGSERVERIP') # set in ".env"
                }
            )
        raise Exception(load_encr)

    @staticmethod
    def decr(*, variable: str | None = None, value: str | None = None):
        if (load_decr := load.variable('A7S6I002TMK6SUT5W')): # set in "/etc/environment"
            return system.shell(load_decr % {"arg": value or f"${variable}"})
        raise Exception(load_decr)

    @staticmethod
    def _os():
        return platform.system()

    @staticmethod
    def notifysend(*, title: str = 'WARNING!', message: str):
        if (notify := load.variable('NOTIFY_SEND')):
            return system.shell(notify % (f'''"👉 {title} 👈\n\n""{message}"'''))
        raise Exception(notify)