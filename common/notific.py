from .authEx import auth
from .loadEx import load, system
from .mountEx import mount
from inspect import currentframe
from traceback import format_exc


class Notific:

    @staticmethod
    def exception(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as error:
                try:
                    if (widgEx := load.widgex(currentframe().f_back)):
                        system.notifysend(
                            title=widgEx, message=notific.event(
                                summary=f"{widgEx} ({type(error).__name__})", 
                                description=format_exc(), colorId='11'
                            ).get('kind')
                        )
                except Exception as error:
                    system.notifysend(title=widgEx, message=format_exc())
        return wrapper
    
    @staticmethod
    def event(
        *, summary: str, description: str, colorId: str, 
        date = mount.data(dateTime=load.now())
    ):
        return auth.googleservice(
            name='calendar', version='v3', 
            _auth=load.variable('NOTIFIC_AUTH'), 
            _scope=load.variable('NOTIFIC_SCOPE')
        ).events().insert(
            calendarId=system.decr(variable=load.variable('NOTIFIC_ID')), 
            body=mount.data(
                summary=summary, description=description, 
                colorId=colorId, start=date, end=date
            )
        ).execute()


    