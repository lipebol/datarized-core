from common.databases import Config

Config.envs()

from common.utilize import Use
from spotifEx.spotify_for_developers import WebAPI

Use.variable('SPOTIFY_WEB_API_QUERY', add=WebAPI.get_query('spotify-web-api'))
Use.variable('DATARIZED_CORE_NAME', add='spotifEx')
Use.variable('DATARIZED_CORE_VERSION', add='v2')