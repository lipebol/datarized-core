from common.utilize import Use

Use.variable('DATARIZED_CORE_NAME', add='real-time-pbh')
Use.variable('DATARIZED_CORE_VERSION', add='v1')

setattr(Use, 'this_path', Use.path(Use.path(), join=['waypointEx','real-time-pbh']))