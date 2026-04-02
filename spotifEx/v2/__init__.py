from common.storage import Stor
from common.utilize import Use
from spotifEx.spotify_for_developers import WebAPI

Use.variable('DATARIZED_CORE_NAME', add='spotifEx')
Use.variable('DATARIZED_CORE_VERSION', add='v2')
setattr(Use, 'spotify_web_api', WebAPI.get_query('spotify-web-api'))
setattr(Use, 'start_date', Use.now(all=False))
setattr(Use, 'log_id', set())

if Use.checkpath((log_id := Use.walfile(id=True))):
    with open(log_id, 'r') as walfile:
        for id in walfile:
            Use.log_id.add(id.strip())

Stor.setconfig()