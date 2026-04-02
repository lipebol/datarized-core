from common.storage import Stor
from common.utilize import Use
from spotifEx.spotify_for_developers import WebAPI

Use.variable('SPOTIFY_WEB_API_QUERY', add=WebAPI.get_query('spotify-web-api'))
Use.variable('DATARIZED_CORE_NAME', add='spotifEx')
Use.variable('DATARIZED_CORE_VERSION', add='v2')

Stor.setconfig()

if Use.checkpath((log_id := Use.walfile(id=True))):
    with open(Use.walfile(id=True), 'r') as file:
        setattr(Use, 'log_id', set(line.strip() for line in file))
else:
    setattr(Use, 'log_id', set())

Use.info(Use.log_id)