from common.utilize import Use
from pyarrow import uint16, string
import pyarrow.feather as feather


csv_file = Use.read_csv(
    Use.path(
        (dir_files := Use.path(Use.this_path, join=['files'])), 
        join='sup-bus-routes-conversion.csv'
    ), 
    ['id', 'bus_id', 'bus_line', 'bus_route'], {
        'id': uint16(), 'bus_id': string(), 
        'bus_line': string(), 'bus_route': string()
    }
).drop('id')

feather.write_feather(
    csv_file, (
        arrow_path := Use.path(
            dir_files, join='sup-bus-routes-conversion.arrow'
        )
    ), compression='uncompressed'
)


print(feather.read_table(arrow_path).num_rows)