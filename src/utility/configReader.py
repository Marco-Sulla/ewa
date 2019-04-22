import argparse
import sys

app_descr = "Generator of Model, Repository and Service for Spring Boot + sql2o"
help_config = "Set the config file to be read"
help_version = "Print the version and exit"

version_flag = "--version"

cmd_parser = argparse.ArgumentParser(description=app_descr)
cmd_parser.add_argument("--config", required=version_flag not in sys.argv, help=help_config)
cmd_parser.add_argument(version_flag, action="store_true", help=help_version)
