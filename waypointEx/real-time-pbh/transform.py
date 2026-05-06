from common.utilize import Use
from pyarrow import uint16, string
import pyarrow.feather as feather


csv_file = Use.read_csv(
    Use.path(
        (dir_files := Use.path(Use.this_path, join=['files'])), 
        join='bus-routes.csv'
    ), 
    ['Identificador', 'Linha', 'Itinerario', 'Categoria'], {
        'Identificador': string(), 'Linha': string(),
        'Itinerario': string(), 'Categoria': string()
    }
)

feather.write_feather(
    csv_file, (arrow_path := Use.path(dir_files, join='bus-routes.arrow')),
    compression='uncompressed'
)

print((file := feather.read_table(arrow_path)))
print(file.num_rows)