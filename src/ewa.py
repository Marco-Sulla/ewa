from utility.version import VERSION
from utility.configReader import cmd_parser
from pathlib import Path
from utility.config import Config

from codefile import (
    model, 
    repository, 
    repository_interface, 
    service,
    service_interface, 
    aggregator, 
    sql2outility, 
)

__version__ = VERSION

try:
    app_dir = Path(__file__).resolve().parent
except NameError:
    app_dir = Path(".")

cmd_args = cmd_parser.parse_args()

config = Config(cmd_args, app_dir)


def main():
    model.write(config)
    repository.write(config)
    repository_interface.write(config)
    service.write(config)
    service_interface.write(config)
    aggregator.write(config)
    sql2outility.write(config)
    
    print("\nFiles saved in " + str(config.data_dir))
    print(
"""
!!!IMPORTANT!!! 
* Please check the insert and update methods in repo, in particular for """ + 
"""autoincrement columns as parameter that does not accept value in insert.
* Remove also in update fields that should never be updated, like createdby or createdon.
* If you want, you can also add a toString() to models and enrich the logging of """ + 
"""{}ByModel, deleteByModel and insert
""".format(config.select_methods_prefix)
    )


if __name__ == "__main__":
    main()
