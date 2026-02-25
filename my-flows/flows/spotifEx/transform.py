from common.httpEx import httpEx
from common.loadEx import load
from datetime import datetime, timedelta
from fsspec.core import url_to_fs
import pyarrow as arrow
import pyarrow.parquet as parquet


class Transform:
    
    @staticmethod
    def query(**kwargs):
        return load.string(
            kwargs, template="""
            query {
                spotifExDaylists(date: "$dates", lookup: true, arrow: true) {
                    ...on spotifExDaylists {
                        data {
                            track {
                                trackid
                                name
                                album {
                                    ...on spotifExAlbumFields {
                                        albumid
                                        name
                                        album_type
                                        release_date
                                        external_url
                                        total_tracks
                                        label
                                    }
                                }
                                url
                                duration_ms
                                popularity
                                explicit
                                track_number
                                disc_number
                                isrc
                            }
                            date
                            listen
                        }
                    }

                    ...on Arrow {
                        message
                        object
                        presigned
                    }
                    
                    ...on Errors {
                        error
                        message
                        status_code
                    }
                }
            }
            """
        )

    @staticmethod
    def request(**kwargs):
        return httpEx.graphql(
            url='http://host.containers.internal/api/v2/graphql', 
            query=Transform.query(**kwargs)
        )

    @staticmethod
    def data():
        # days = [(datetime.now()-timedelta(days=n)).strftime('%Y-%m-%d') for n in range(7)]
        # if (data := Transform.request(**{'dates': '|'.join(days)}).get('data')):
        fs_http, presigned = url_to_fs(
            Transform.request(**{'dates': '2026-*'}).get('presigned'), 
            **{'https': {'ssl': False}}
        )
        for field in (
            table := load.dataset(presigned, typefile='arrow', fs=fs_http).flatten()
        ).schema:
            if arrow.types.is_struct(field.type):
                struct, table = table.select([field.name]).flatten(), table.drop(field.name)
                for structfield in struct.schema:
                    table = table.append_column(structfield, struct.column(structfield.name))
        return parquet.write_table(table, load.path(join=['data-shared', 'daylists.parquet']))