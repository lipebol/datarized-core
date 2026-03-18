from .loadEx import load, system
from .httpEx import httpEx
from .mountEx import mount
from pyarrow import flight
from googleapiclient.discovery import build
from google.oauth2 import service_account

class Authentic:
    
    @staticmethod
    def GCPService(
        *, name: str, version: str, _auth: str | None = None, 
        _scope: str | None = None, _authkey: str | None = None,
    ) -> object:
        if _auth and _scope:
            _auth = service_account.Credentials.from_service_account_info(
                load.jsonEx(data=system.decr(variable=_auth), to_objectpy=True), 
                scopes=[system.decr(variable=_scope)]
            )
        elif _authkey:
            _authkey = system.decr(variable=_authkey)
        return build(
            name, version, developerKey=_authkey, 
            credentials=_auth, cache_discovery=False
        )

    @staticmethod
    def arrowflightrpc(uri: str, **kwargs):
        if (uri := load.uri(system.decr(value=uri))) and (
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
                        else (
                            command := load.string(
                                kwargs, template=load.variable('SELECT_ALL')
                            )
                        )
                    ), authenticate
                )
            ) and (
                mountinfo := mount.data(
                    schema=info.schema, rows=info.total_records,
                    size=info.total_bytes, ticket=flight.Ticket(command)
                )
            ):
                if info.endpoints:
                    for endpoint in info.endpoints:
                        mountinfo.ticket = endpoint.ticket
                        mountinfo.expiration_time = endpoint.expiration_time
                
                if kwargs.get('info'):
                    return mountinfo

                arrowflightrpcdata = mount.data(
                    info=mountinfo, conn=mount.data(
                        client=client, authenticate=authenticate, descriptor=descriptor
                    ), extras=mount.data(classname='Arrow_Flight_RPC_Extras')
                )

                if kwargs.get('insert_command'):
                    arrowflightrpcdata.extras.command = load.string(
                        {
                            **kwargs,
                            'cols': load.string((cols := info.schema.names), join=True),
                            'values': load.string(['?'] * len(cols), join=True),
                        }, template=load.variable('INSERT_ALL')
                    )
                elif kwargs.get('insert_path'):
                    arrowflightrpcdata.extras.path = load.string(
                        kwargs, template=load.variable('FOR_PATH')
                    )
                    
                return arrowflightrpcdata
        raise Exception('')