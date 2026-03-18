from .utilize import Use
from .fabric import Make
from googleapiclient.discovery import build
from google.oauth2 import service_account
from pyarrow import flight
from urllib.parse import urlparse

class Auth:
    
    @staticmethod
    def gcp_service(
        *, name: str, version: str, _auth: str | None = None, 
        _scope: str | None = None, _authkey: str | None = None,
    ) -> object:
        if _auth and _scope:
            _auth = service_account.Credentials.from_service_account_info(
                Use.jsonific(data=Use.decr(variable=_auth), to_objectpy=True), 
                scopes=[Use.decr(variable=_scope)]
            )
        elif _authkey:
            _authkey = Use.decr(variable=_authkey)
        return build(name, version, developerKey=_authkey, credentials=_auth, cache_discovery=False)

    @staticmethod
    def arrow_flight_rpc(uri: str, **kwargs):
        if (uri := urlparse(Use.decr(value=uri))) and (
            client := flight.FlightClient(f"{uri.scheme}://{uri.hostname}:{uri.port}")
        ) and (
            authenticate := flight.FlightCallOptions(
                headers=[client.authenticate_basic_token(uri.username,uri.password)]
            )
        ) and (descriptor := flight.FlightDescriptor):
            if (
                info := client.get_flight_info(
                    descriptor.for_command(
                        command if (command := kwargs.get('query'))
                        else (command := Use.stringific(kwargs, template=Use.variable('SELECT_ALL')))
                    ), authenticate
                )
            ) and (
                make_info := Make.data(
                    schema=info.schema, rows=info.total_records,
                    size=info.total_bytes, ticket=flight.Ticket(command)
                )
            ):
                if info.endpoints:
                    for endpoint in info.endpoints:
                        make_info.ticket = endpoint.ticket
                        make_info.expiration_time = endpoint.expiration_time
                
                if kwargs.get('info'):
                    return make_info

                arrow_flight_rpc_data = Make.data(
                    info=make_info, conn=Make.data(
                        client=client, authenticate=authenticate, descriptor=descriptor
                    ), extras=Make.data(classname='Arrow_Flight_RPC_Extras')
                )

                if kwargs.get('insert_command'):
                    arrow_flight_rpc_data.extras.command = Use.stringific(
                        {
                            **kwargs,
                            'cols': Use.stringific((cols := info.schema.names), join=True),
                            'values': Use.stringific(['?'] * len(cols), join=True),
                        }, template=Use.variable('INSERT_ALL')
                    )
                elif kwargs.get('insert_path'):
                    arrow_flight_rpc_data.extras.path = Use.stringific(
                        kwargs, template=Use.variable('FOR_PATH')
                    )
                    
                return arrow_flight_rpc_data
        raise Exception('')