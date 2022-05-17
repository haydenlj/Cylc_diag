import gnssro_plots as gp
import click


@click.command()
@click.option('--filename', required=True, help='Path to data ex. gfs.jedi_gdas_009.diag.PT6H.gnssrobndnbam.2020-12-14T21_00_00Z.PT6H.nc4')
@click.option('--platform', required=True, help='ex. amsua_n19')
@click.option('--date', required=True, help='Must be in TZ format ex. 2020-12-14T21:00:00Z')
@click.option('--image_path', required=True, help='ex. /Users/eric2/path/for/images')
@click.option('--var_colmin', required=False, help='Min value for color map on obs and hofx plots')
@click.option('--var_colmax', required=False, help='Max value for color map on obs and hofx plots')
@click.option('--omb_colmin', required=False, help='Min value for color map on omb plots', default=-5)
@click.option('--omb_colmax', required=False, help='Max value for color map on omb plots', default=5)
def map_from_ioda(filename, platform, date, 
                  image_path, var_colmin, var_colmax, omb_colmin, omb_colmax):
    diag = gp.Diagnostic(filename, platform, date)

    gp.ScatterMap(diag, image_path, var_colmin, var_colmax)

#   gp.VerticalProfile(diag, 'obs', image_path)

#   gp.VerticalProfile(diag, 'hofx', image_path)

#   gp.VerticalProfile(diag, 'omb', image_path)


if __name__ == '__main__':
    map_from_ioda()
