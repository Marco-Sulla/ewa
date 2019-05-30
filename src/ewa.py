from utility.version import VERSION
from utility.configReader import cmd_parser
from pathlib import Path
from utility.config import Config

__version__ = VERSION

try:
    app_dir = Path(__file__).resolve().parent
except NameError:
    app_dir = Path(".")

cmd_args = cmd_parser.parse_args()

config = Config(cmd_args, app_dir)


def main():
    import importlib
    
    codefile_package = "codefile"
    codefile_interface_name = "CodeFileInterface"
    codefile_dir = app_dir / codefile_package
    
    for codefile_file in codefile_dir.glob("*.py"):
        codefile_name = codefile_file.stem
            
        if codefile_name == "__init__":
            continue
        
        module = importlib.import_module("." + codefile_name, package=codefile_package)
        module.write(config)
    
    print("\nFiles saved in " + str(config.data_dir))
    print(
"""
###########################################################
# !!!!!!!!!!!!!!!!!!!!!! IMPORTANT !!!!!!!!!!!!!!!!!!!!!! #
# * Insert in your `application.properties` the type of   #
#   DB under the property `datasource.type`. Supported DB #
#   types are listed in `config_example.ini`, under       #
#   [database] section, over `type` property.             #
#                                                         #
# * Please check the insert and update methods in repo,   #
#   in particular for autoincrement columns as parameter  #
#   that does not accept value in insert.                 #
#                                                         #
# * Remove also in update fields that should never be     #
#   updated, like createdby or createdon.                 #
#                                                         #
# * If you want, you can also add a toString() to models  #
#   and enrich the logging of {}ByModel, deleteByModel    #
#   and insert.                                           #
###########################################################
""".format(config.select_methods_prefix)
    )


if __name__ == "__main__":
    main()
