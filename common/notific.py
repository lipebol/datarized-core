from .authentic import Auth
from .fabric import Make
from .utilize import Use
from subprocess import run, PIPE
from traceback import format_exc


class Notific:

    @staticmethod
    def exception(error: Exception):
        try:
            Notific.alert(
                title=(name := Use.variable('DATARIZED_CORE_NAME')),
                message=Notific.event(
                    summary=f"{name} ({type(error).__name__})",
                    description=format_exc(), colorId='11'
                ).get('kind')
            )
            Use.info(error)
        except Exception:
            Notific.alert(title='Notific', message=format_exc())
    
    @staticmethod
    def event(
        *, summary: str, description: str, colorId: str, 
        date = Make.data(dateTime=Use.now())
    ):
        return Auth.gcp_service(
            name='calendar', version='v3', _auth=Use.variable('NOTIFIC_AUTH'), 
            _scope=Use.variable('NOTIFIC_SCOPE')
        ).events().insert(
            calendarId=Use.decr(content=Use.variable('NOTIFIC_ID'), env=True),
            body=Make.data(
                summary=summary, description=description, 
                colorId=colorId, start=date, end=date
            )
        ).execute()

    @staticmethod
    def alert(*, title: str = 'WARNING!', message: str):
        if (load_alert := Use.variable('NOTIFIC_SEND')):
            return run(
                load_alert % (f'''"👉 {title} 👈\n\n""{message}"'''),
                shell=True, stdout=PIPE, text=True
            ).stdout.strip()
        raise Exception(load_alert)


    