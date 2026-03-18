from datetime import datetime
from dotenv import load_dotenv
from inspect import getmodule
from json import dump, dumps, load, loads
from logging import basicConfig, info, INFO
from os import environ, getenv, path, remove
from pathlib import Path
import pyarrow as arrow
import pyarrow.dataset as arrow_dataset
from pytz import timezone
from string import Template
from subprocess import run, PIPE
from time import sleep
from zipfile import ZipFile


class Use:

    load_dotenv()

    basicConfig(
        format='%(asctime)s - %(levelname)s - %(message)s', 
        level=INFO, datefmt='%Y-%m-%d %H:%M:%S'
    )

    @staticmethod
    def quiet(func):
        def wrapper(*args, **kwargs):
            sleep(1)
            return func(*args, **kwargs)
        return wrapper

    @quiet
    @staticmethod
    def info(_info: str) -> str:
        return info(_info)

    @staticmethod
    def envs():
        try:
            for key, value in Use.jsonific(path=(tmpfile := Use.tmpfile(path='/tmp'))).items():
                if isinstance(value, str):
                    yield Use.variable(key, add=value)
        except Exception:
            remove(tmpfile)
            return False

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
    def stringific(values: dict | list, *, template: str | None = None, join: bool = False):
        if join and isinstance(values, list):
            return ', '.join(values)
        elif template and isinstance(values, dict):
            return Template(template).substitute(values)

    @staticmethod
    def jsonific(
        *, path: str | None = None, data: str | dict | None = None, 
        to_string: bool = False, to_objectpy: bool = False
    ):
        if not path and data:
            if to_string:
                data = dumps(data)
            if to_objectpy:
                data = loads(data)
            return data
        if path:
            with open(path, 'w' if data else 'r', encoding='utf-8') as jsonific:
                if not data:
                    return load(jsonific)
                dump(data, jsonific, ensure_ascii=False, indent=5)

    @staticmethod
    def unzip(zip_file: object, suffix=None) -> str:
        def extract(zip_obj: object, suffix: str, path: str):
            for file in zip_obj.namelist():
                if file.endswith(suffix):
                    yield zip_obj.extract(file, path)           
        with ZipFile(zip_file, 'r') as zip_obj:
            if suffix:
                Use.info("\n%s\n" % '\n'.join(list(extract(zip_obj, suffix, zip_file.parent))))
            return zip_obj.extractall(zip_file.parent)

    @staticmethod
    def read_csv(csv_file: str, fields: list, types: dict, sep=None) -> object:
        Use.info(f"Reading file... ({csv_file})")
        return arrow.csv.read_csv(
            csv_file, parse_options=arrow.csv.ParseOptions(delimiter=sep if sep else ';'),
            read_options=arrow.csv.ReadOptions(
                encoding='latin1', column_names=fields, skip_rows=1
            ), convert_options=arrow.csv.ConvertOptions(column_types=types)
        )

    @staticmethod
    def dataset(datafile, *, typefile: str, fs: object, types: list | None = None, batch: bool = False):
        Use.info(f"Reading file... ({datafile})")
        if (dataset := arrow_dataset.dataset(datafile, schema=types, format=typefile, filesystem=fs)):
            if batch:
                return
            return dataset.to_table() 

    @staticmethod
    def tmpfile(*, path: str, filename: str | None = None) -> str:
        return Use.path(path, join='tmp.json' if not filename else f'{filename}.json')

    @staticmethod
    def timezone_default(timezone: str | None = None) -> str:
        return 'America/Sao_Paulo' if not timezone else timezone

    @staticmethod
    def date(value: str | datetime, *, format: str = '%Y-%m-%dT%H:%M:%S.%f%z'):
        if isinstance(value, (str, datetime)):
            return datetime.strptime(
                value, format
            ) if isinstance(value, str) else value.strftime(format)

    @staticmethod
    def now(*, all: bool = True) -> str:
        if (now := datetime.now(tz=timezone(Use.timezone_default()))):
            return Use.date(now, format='%Y-%m-%d') if not all else now.isoformat()

    @staticmethod
    def encr(*, variable: str | None = None, value: str | None = None):
        if (load_encr := Use.variable('TX808FBP22QE2QTTK')):
            return run(
                load_encr % {
                    "arg": value or f"${variable}",
                    "tangserver": Use.variable('TANG_SERVER_IP') # set in ".env"
                }, shell=True, stdout=PIPE, text=True
            ).stdout.strip()
        raise Exception(load_encr)

    @staticmethod
    def decr(*, variable: str | None = None, value: str | None = None):
        if (load_decr := Use.variable('A7S6I002TMK6SUT5W')): # set in "/etc/environment"
            return run(
                load_decr % {"arg": value or f"${variable}"}, 
                shell=True, stdout=PIPE, text=True
            ).stdout.strip()
        raise Exception(load_decr)
    
    @staticmethod
    def __caller(value: object):
        return Use.path(path.dirname(getmodule(value).__file__)).name

    