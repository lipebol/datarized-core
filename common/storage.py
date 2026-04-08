from .authentic import Auth
from .notific import Notific
from .utilize import Use
import adbc_driver_postgresql.dbapi
import pyarrow.dataset as ArrowDataset
from pyarrow.fs import FileSelector, S3FileSystem
from pyarrow import Table
from pymongo import MongoClient


class ClickHouse:

    @staticmethod
    def setconfig(database: str | None = None):
        Config.storage('CLICKHOUSE_DB', database)
        return Config.envs()

    @staticmethod
    def getdbname(database: str | None) -> str:
        if (database := database or Use.variable('CLICKHOUSE_DB')):
            return database
        raise Exception('The database was not declared.')

    @staticmethod
    def __connect(database: str | None, **kwargs):
        if kwargs.get('query') and kwargs.get('table'):
            raise Exception('Choose one of the two methods: "query" or "table".')
        elif kwargs.get('table'):
            kwargs['default'] = ClickHouse.getdbname(database) ### <-- to env 'SELECT_ALL'
        return Auth.arrow_flight_rpc(Use.variable('CLICKHOUSE_URI'), **kwargs)
        
    @staticmethod
    def select(*, database: str | None = None, **kwargs):
        if kwargs.get('query') or kwargs.get('table'):
            if (flight := ClickHouse.__connect(database, **kwargs)):
                if not flight.info.rows:
                    return flight.info.schema.empty_table()
                return flight.conn.client.do_get(
                    flight.info.ticket, flight.conn.authenticate
                ).read_all()
        raise Exception('The "query" or "table" was not declared.')

    @staticmethod
    def insert(*, database: str | None = None, **kwargs):
        if (table := kwargs.get('table')):
            config = {'insert_path': True, **kwargs}
            if (flight := ClickHouse.__connect(database, **config)):
                if (schema := kwargs.get('use_schema')):
                    flight.info.schema = schema
                writer, _ = flight.conn.client.do_put(
                    flight.conn.descriptor.for_path(flight.extras.path), 
                    flight.info.schema, flight.conn.authenticate
                )
                return writer
        raise Exception('The "table" was not declared.')

    @staticmethod
    def info(*, database: str | None = None, **kwargs):
        if kwargs.get('query') or kwargs.get('table'):
            config = {'info': True, **kwargs}
            return ClickHouse.__connect(database, **config)
        raise Exception('The "query" or "table" was not declared.')


class PostgreSQL:

    @staticmethod
    def setconfig(database: str | None = None):
        Config.storage('POSTGRESQL_DB', database)
        return Config.envs()

    @staticmethod
    def getdbname(database: str | None) -> str:
        if (database := database or Use.variable('POSTGRESQL_DB')):
            return database
        raise Exception('The database was not declared.')

    @staticmethod
    def __connect(database: str | None):
        return adbc_driver_postgresql.dbapi.connect(
            Use.decr(content='postgresql-uri.jwe')
            .replace('postgres', PostgreSQL.getdbname(database)), autocommit=True
        ).cursor()

    @staticmethod
    def select(*, database: str | None = None, **kwargs):
        if (schema := kwargs.get('schema')) and kwargs.get('table') or kwargs.get('query'):
            with PostgreSQL.__connect(database) as conn:
                if (query := kwargs.get('query')):
                  conn.execute(query)
                else:
                    conn.execute(
                        Use.stringific(
                            {'default': schema, **kwargs}, 
                            template=Use.variable('SELECT_ALL')
                        )
                    )
                return conn.fetch_arrow_table()
        raise Exception('The "schema" and "table" or "query" was not declared.')

    @staticmethod
    def insert(*, database: str | None = None, **kwargs):
        if (data := kwargs.get('data')) and (
            schemadb := kwargs.get('schemadb')
        ) and (table := kwargs.get('table')):
            if not isinstance(data, Table):
                data, rows = data.to_batches(), data.count_rows()
            else:
                rows = data.num_rows
            with PostgreSQL.__connect(database) as conn:
                conn.adbc_ingest(
                    db_schema_name=schemadb, table_name=table, data=data, mode='append'
                )
            load.info(f"Inserted {rows} rows in {schemadb}.{table}")
            return
        raise Exception('The "data" and "schemadb" and "table" was not declared.')

    @staticmethod
    def columns(*, database: str | None = None, **kwargs) -> list:
        if (schema := kwargs.get('schema')) and kwargs.get('table'):
            with PostgreSQL.__connect(database) as conn:
                conn.adbc_execute_schema(
                    Use.stringific(
                        {'default': schema, **kwargs},
                        template=Use.variable('SELECT_LIMIT')
                    )
                )
            return 
        raise Exception('The "schema" and "table" was not declared.')

    @staticmethod
    def sizedb(target: str, *, database: str | None = None):
        if len((target := target.lower().split())) == 2:
            with PostgreSQL.__connect(database) as conn:
                conn.execute(Use.variable('SIZEDB') % PostgreSQL.getdbname(database))
                if (sizedb := "".join(conn.fetchone()).lower().split()):
                    Use.info(sizedb)
                    if target[1] == sizedb[1] and int(target[0]) <= int(sizedb[0]):
                        raise Exception('The specified target was hit.')
                return True
        raise Exception('Please specify the desired limit in the format: <size> <unit>')


class MongoDB:

    @staticmethod
    def setconfig():
        Config.storage('MONGODB_DB', Use.variable('DATARIZED_CORE_NAME'))
        return Config.envs()

    @staticmethod
    def getdbname(database: str | None) -> str:
        if (database := database or Use.variable('MONGODB_DB')):
            return database
        raise Exception('The database was not declared.')

    @staticmethod
    def connect(database: str, collection: str):
        return MongoClient(Use.decr(content='mongodb-uri.jwe')).get_database(
            MongoDB.getdbname(database)
        ).get_collection(collection)

    @staticmethod
    def select(
        collection: str, *, database: str | None = None, 
        filter: dict = {}, fields: dict = {}, _id: bool = False
    ) -> list:
        _db = MongoDB.connect(database, collection)
        if not _id:
            fields['_id'] = 0
        return list(_db.find(filter, fields))

    @staticmethod
    def update(collection: str, *, database: str | None = None, filter: dict, update: dict):
        return MongoDB.connect(database, collection).update_many(filter, { '$set' : update})

    @staticmethod
    def insert(collection: str, *, database: str | None = None, data: dict, many: bool = False):
        if not many:
            return MongoDB.connect(database, collection).insert_one(data).inserted_id


class Stor:

    @staticmethod
    def setconfig():
        Config.storage('STOR_BUCKET', Use.variable('DATARIZED_CORE_NAME').lower())
        return Config.envs()

    @staticmethod
    def getbucketname(bucket: str | None) -> str:
        if (bucket := bucket or f'{Use.variable('STOR_BUCKET')}/'):
            return bucket
        raise Exception('The bucket was not declared.')

    @staticmethod
    def connect():
        endpoint, access_key, secret_key = Use.decr(content='s3.jwe').split(' ')
        return S3FileSystem(
            access_key=access_key, secret_key=secret_key, endpoint_override=endpoint
        )

    @staticmethod
    def list_objects(bucket: str | None = None):
        return Stor.connect().get_file_info(
            FileSelector(Stor.getbucketname(bucket), recursive=True)
        )

    @staticmethod
    def insert(
        data: Table, *, bucket: str | None = None,
        typefile: str = 'parquet',
        partition: list | None = None
    ):
        try:
            ArrowDataset.write_dataset(
                data, Stor.getbucketname(bucket), format=typefile,
                partitioning=partition, filesystem=Stor.connect(),
                existing_data_behavior='delete_matching'
            )
            Use.info('Saved Successfully!')
            Use.info(f'List Objects: {Stor.list_objects()}')
        except Exception as error:
            Notific.exception(error)
    

class Config:

    @staticmethod
    def storage(env: str, storage: str | None) -> list:
        if storage:
            return Use.variable(env, add=storage)

    @staticmethod
    def envs():
        if Use.checkpath(tmpfile := Use.tmpfile(path='/tmp')):
            if not (envs := list(Use.envs())):
                if Use.checkpath(tmpfile):
                    raise Exception(error)
            else:
                return envs
        if (dataenv := MongoDB.select('_envs', database='common')):
            Use.jsonific(path=tmpfile, data=dataenv[0])
            return list(Use.envs())
        raise Exception('Error load envs.')