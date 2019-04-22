import argparse

app_descr = "Java code generator"
help_config = "Set the config file to be read"
help_version = "Print the version and exit"

cmd_parser = argparse.ArgumentParser(description=app_descr)
cmd_parser.add_argument("--config", required=True, help=help_config)
cmd_parser.add_argument("--version", action="store_true", help=help_version)
