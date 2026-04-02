from common.storage import Stor
from common.utilize import Use
from fsspec.implementations.http import HTTPFileSystem

Use.variable('DATARIZED_CORE_NAME', add='spotifEx')
Use.variable('DATARIZED_CORE_VERSION', add='v2')

with HTTPFileSystem().open(
    (
        'https://raw.githubusercontent.com/lipebol/datarized-core/'
        'refs/heads/main/spotifEx/querys/spotify-web-api'
    ), 'rb'
) as content:
    setattr(Use, 'spotify_web_api', content.read().decode())

setattr(Use, 'start_date', Use.now(all=False))
setattr(Use, 'log_id', set())

if Use.checkpath((log_id := Use.walfile(id=True))):
    with open(log_id, 'r') as walfile:
        for id in walfile:
            Use.log_id.add(id.strip())

Stor.setconfig()