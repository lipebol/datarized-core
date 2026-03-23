from aiohttp import ClientSession, ClientTimeout
from common.utilize import Use
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport

class WebAPI:

    @staticmethod
    def access(func):
        async def wrapper(trackid: str):
            async with Client(
                transport=AIOHTTPTransport(
                    url='http://localhost/api/v2/graphql/', 
                    headers={
                        'Content-Type': 'application/json', 
                        'AuthExternal': await WebAPI.token()
                    }, client_session_args={'timeout': ClientTimeout(total=300)}
                )
            ) as session:
                track = await session.execute(
                    gql(WebAPI.query(**{'arg': trackid.split('/')[-1]}))
                )
            if not (track := track.get('SpotifyWebAPI')):
                raise Exception('There was probably an error during the track search.')
            return func(track)
        return wrapper

    @staticmethod
    async def token():
        if not (
            spotify_web_api_object := Use.jsonific(
                data=Use.variable('SPOTIFY_WEB_API_OBJECT'), to_objectpy=True
            )
        ):
            raise Exception('Error in SPOTIFY_WEB_API_OBJECT.')
        if not (spotify_web_api_token := spotify_web_api_object.get('token')) or (
            Use.date(Use.now()) - Use.date(spotify_web_api_object.get('created_at'))
        ).total_seconds() >= 3600:
            async with ClientSession(timeout=ClientTimeout(total=60)) as session:
                async with session.post(
                    spotify_web_api_object.get('get_token'), data={
                        **(spotify_web_api_params := spotify_web_api_object.get('params')), 
                        "client_id": Use.decr(value=spotify_web_api_params.get('client_id')),
                        "client_secret": Use.decr(value=spotify_web_api_params.get('client_secret'))
                    }
                ) as response:
                    spotify_web_api_token = await response.json()
            if not (spotify_web_api_token := spotify_web_api_token.get('access_token')):
                raise Exception('There was probably an error while generating the token.')
            tmpfile_data = Use.jsonific(path=(tmpfile := Use.tmpfile(path='/tmp')))
            tmpfile_data['SPOTIFY_WEB_API_OBJECT'] = Use.jsonific(
                data={
                    **spotify_web_api_object, 'created_at': Use.now(),
                    'token': (spotify_web_api_token := Use.encr(value=spotify_web_api_token))
                }, to_string=True
            )
            Use.jsonific(path=tmpfile, data=tmpfile_data)
            Use.envs()
        return spotify_web_api_token

    @staticmethod
    def query(**kwargs):
        return Use.stringific(
            kwargs, template="""
            query {
                SpotifyWebAPI(trackid: "$arg") {
                    ...on spotifExTrackId { id }
                    ...on spotifExTrackFields {
                        trackid
                        name
                        album {
                            ...on spotifExAlbumId { id }
                            ...on spotifExAlbumFields {
                                albumid
                                name
                                album_type
                                release_date
                                external_url
                                images {
                                    url
                                    width
                                    height
                                }
                                total_tracks
                                copyrights {
                                    text
                                    type
                                }
                                label
                            }
                        }
                        artists {
                            ...on spotifExArtistId { id }
                            ...on spotifExArtistFields {
                                artistid
                                name
                                profile
                                followers
                                images {
                                    url
                                    width
                                    height
                                }
                                genres {
                                    name
                                    about
                                }
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

                    ...on Errors {
                        error
                        message
                        status_code
                    }
                }
            }
        """
        )
