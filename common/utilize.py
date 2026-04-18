from datetime import datetime
from inspect import getmodule
from json import dump, dumps, load, loads
from logging import basicConfig, info, INFO
from os import environ, fsync, getenv, path, remove
from pathlib import Path, PosixPath
import pyarrow as Arrow
from pyarrow import json
import pyarrow.dataset as ArrowDataset
from pytz import timezone
from string import Template
from subprocess import run, PIPE
from time import sleep
from zipfile import ZipFile


class Use:

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
        return info(
            (
                f'{Use.variable('DATARIZED_CORE_NAME')}'
                f' {Use.variable('DATARIZED_CORE_VERSION')}:'
                f' {_info} '
            )
        )

    @staticmethod
    def envs():
        try:
            for key, value in Use.jsonific(path=(tmpfile := Use.tmpfile(path='/tmp'))).items():
                if isinstance(value, str):
                    yield Use.variable(key, add=value)
        except Exception as error:
            Use.info(error)
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
        to_string: bool = False, to_objectpy: bool = False,
        jsonl: bool = False
    ):
        if jsonl:
            if path:
                return json.read_json(path)
            elif data:
                with open(Use.walfile(), 'a', encoding='utf-8') as jsonific:
                    jsonific.write(dumps(data, ensure_ascii=False) + '\n')
                    jsonific.flush()
                    fsync(jsonific.fileno())
        elif path:
            with open(path, 'w' if data else 'r', encoding='utf-8') as jsonific:
                if not data:
                    return load(jsonific)
                dump(data, jsonific, ensure_ascii=False, indent=5)
        elif data:
            if to_string:
                data = dumps(data)
            if to_objectpy:
                data = loads(data)
            return data

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
    def read_csv(csv_file: str, fields: list, types: dict, sep=None) -> Arrow.Table:
        Use.info(f"Reading file... ({csv_file})")
        return Arrow.csv.read_csv(
            csv_file, parse_options=Arrow.csv.ParseOptions(delimiter=sep if sep else ';'),
            read_options=Arrow.csv.ReadOptions(
                encoding='latin1', column_names=fields, skip_rows=1
            ), convert_options=Arrow.csv.ConvertOptions(column_types=types)
        )

    @staticmethod
    def dataset(
        datafile, *, typefile: str, fs: object,
        types: list | None = None, batch: bool = False
    ) -> Arrow.dataset.Dataset:
        Use.info(f"Reading file... ({datafile})")
        if (
            dataset := ArrowDataset.dataset(
                datafile, schema=types, format=typefile, filesystem=fs
            )
        ):
            if batch:
                return
            return dataset.to_table() 

    @staticmethod
    def tmpfile(*, path: str, filename: str | None = None) -> PosixPath:
        return Use.path(path, join='tmp.json' if not filename else f'{filename}.json')

    @staticmethod
    def walfile(*, id: bool = False) -> PosixPath:
        return Use.path(
            Use.path(), join=[
                'common', '.wal', Use.variable('DATARIZED_CORE_NAME'),
                '.log_data' if not id else '.log_id', f'{Use.start_date}'
            ]
        )

    @staticmethod
    def timezone_default(timezone: str | None = None) -> str:
        return 'America/Sao_Paulo' if not timezone else timezone

    @staticmethod
    def date(
        value: datetime | str, *, format: str = '%Y-%m-%dT%H:%M:%S.%f%z'
    ) -> datetime | str:
        if isinstance(value, (datetime, str)):
            return datetime.strptime(
                value, format
            ) if isinstance(value, str) else value.strftime(format)

    @staticmethod
    def now(*, all: bool = True) -> str:
        if (now := datetime.now(tz=timezone(Use.timezone_default()))):
            return Use.date(now, format='%Y-%m-%d') if not all else now.isoformat()

    @staticmethod
    def encr(*, content: str, env: bool = False) -> str:
        if (load_encr := Use.variable('TX808FBP22QE2QTTK')):
            return run(
                load_encr % {
                    'arg': content if not env else f'${content}',
                    'tangserver': Use.variable('FJH14E77TT22C4U4X')
                }, shell=True, stdout=PIPE, text=True
            ).stdout.strip()
        raise Exception(load_encr)

    @staticmethod
    def decr(*, content: str, env: bool = False) -> str:
        content = Use.stringific(
            {'arg': content if not env else f"${content}"},
            template=(
                'clevis-decrypt-tang < '
                f'{Use.path()}/common/'
                '.dbsecrets/$arg'
            ) if content.endswith('.jwe') else 'echo $arg | clevis-decrypt-tang'
        )
        return run(content, shell=True, stdout=PIPE, text=True).stdout.strip()
    
    @staticmethod
    def __caller(value: object):
        return Use.path(path.dirname(getmodule(value).__file__)).name