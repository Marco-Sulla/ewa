import sys
from builtins import print

from mylib import msutils
import configparser
from .version import VERSION
import sqlalchemy
from pathlib import Path
import re


class Config:
    def __init__(self, cmd_args, app_dir):
    
        cmd_dict = vars(cmd_args)
        
        if cmd_dict.get("version"):
            print(VERSION)
            sys.exit(0)

        config_path = Path(cmd_dict["config"])
        config = configparser.ConfigParser()
        config.read(str(config_path.absolute()))
    
        class_name = config.get("default", "class_name")  # TODO  support multiple
        self._class_name = class_name
        aggregator_class = "{class_name}Aggregator".format(class_name=class_name)
        self._aggregator_class = aggregator_class
        aggregator_var = aggregator_class[0].lower() + aggregator_class[1:]
        self._aggregator_var = aggregator_var
        table_name = config.get("default", "table_name").upper()
        self._table_name = table_name
        ids = config.get("default", "ids").upper().split(",")
        
        indent_str = config.get("default", "delimiter")
        
        if not re.match(r"^\d[st]$", indent_str):
            err_tpl = "Bad `delimiter` value `{val}` in [default] section of {ini}"
            print(err_tpl.format(ini=config_path.name, val=indent_str), file=sys.stderr)
            sys.exit(1)
        
        indent_num = int(indent_str[0])
        indent_type = indent_str[1]
        
        if indent_type == "s":
            indent_single = " "
        else:
            indent_single = "	"
        
        indent = indent_single * indent_num
        self._indent = indent
        
        select_methods_prefix = config.get("default", "select_methods_prefix")
    
        if not select_methods_prefix:
            select_methods_prefix = "get"
        else:
            select_methods_prefix = select_methods_prefix.lower()
    
        self._select_methods_prefix = select_methods_prefix
    
        for i in range(len(ids)):
            ids[i] = ids[i].strip()
    
        self._ids = ids
    
        multiple_ids = False
    
        if len(ids) > 1:
            multiple_ids = True
    
        self._multiple_ids = multiple_ids
    
        integer_instead_of_short = bool(int(config.get("default", "integer_instead_of_short")))
        self._integer_instead_of_short = integer_instead_of_short
        bigdecimal_instead_of_double = bool(int(config.get("default", "bigdecimal_instead_of_double")))
        self._bigdecimal_instead_of_double = bigdecimal_instead_of_double
        bigdecimal_instead_of_long = bool(int(config.get("default", "bigdecimal_instead_of_long")))
        self._bigdecimal_instead_of_long = bigdecimal_instead_of_long
    
        dtype = config.get("database", "type")
        self._dtype = dtype
        user = config.get("database", "user")
        self._user = user
        password = config.get("database", "password")
        self._password = password
        host = config.get("database", "host")
        self._host = host
        port = int(config.get("database", "port"))
        self._port = port
        db_name = config.get("database", "name")
        self._db_name = db_name
        service_name_str = config.get("database", "service_name")
    
        if service_name_str == "0":
            service_name = False
        elif service_name_str == "1":
            service_name = True
        else:
            raise ValueError("Invalid value for service name: " + service_name_str)
    
        self._service_name = service_name
    
        pack_model = config.get("packages", "model")
        self._pack_model = pack_model
        pack_aggregator = config.get("packages", "aggregator")
        self._pack_aggregator = pack_aggregator
        pack_repo = config.get("packages", "repository")
        self._pack_repo = pack_repo
        pack_service = config.get("packages", "service")
        self._pack_service = pack_service
        pack_utility = config.get("packages", "utility")
        self._pack_utility = pack_utility
    
        data_dir = app_dir / "data" / class_name
        self._data_dir = data_dir
    
        db_str = msutils.dbString(dtype, user, password, host, port, db_name, service_name)
    
        engine = sqlalchemy.engine.create_engine(db_str, echo=False)
    
        if dtype == "mssql":
            from db.MssqlUtility import MssqlUtility as dbUtility
        elif dtype == "oracle":
            from db.OracleUtility import OracleUtility as dbUtility
        else:
            raise Exception("Unsupported database: " + dtype)
    
        converter = dbUtility.convertToJavaType
        get_columns_data_sql = dbUtility.get_columns_data_sql
    
        rows = engine.execute(get_columns_data_sql.format(table_name))
    
        rows = list(rows)
    
        rows_clone = rows[:]
        i = 0
    
        for row in rows_clone:
            col_id = row[5]
        
            if col_id is None:
                rows.remove(row)
                i -= 1
        
            i += 1
    
        self._rows = rows
    
        col_types = {}
        import_date_eff = ""
        import_date = "import java.util.Date;"
        noupdate = True
        
        for row in rows:
            col = row[0].upper()
            ctype = row[1]
            prec = row[2]
            radix = row[3]
            scale = row[4]
            col_id = row[5]
        
            if col_id is None:
                continue
        
            jtype = converter(
                ctype,
                prec,
                radix,
                scale,
                integer_instead_of_short,
                bigdecimal_instead_of_double,
                bigdecimal_instead_of_long
            )
        
            if jtype == "Date":
                import_date_eff = import_date + "\n"
        
            col_types[col] = jtype
            
            if col not in ids:
                noupdate = False
    
        self._col_types = col_types
        self._import_date_eff = import_date_eff
        self._noupdate = noupdate
        
        if multiple_ids:
            methid = "Ids"
        else:
            methid = ids[0][0].upper() + ids[0][1:].lower()
    
        self._methid = methid
    
        varname = class_name[0].lower() + class_name[1:]
        self._varname = varname
        initial = varname[0]
        self._initial = initial
    
        id_col_type = None
    
        if not multiple_ids:
            id_col_type = col_types[ids[0]]
    
        self._id_col_type = id_col_type
    
        idsfirm = ""
        idslist = ""
    
        for id in ids:
            col_type = col_types[id]
            varid = id.lower()
        
            idsfirm += "{} {}, ".format(col_type, id.lower())
            idslist += "{}, ".format(varid)
    
        idsfirm = idsfirm[:-2]
        self._idsfirm = idsfirm
        idslist = idslist[:-2]
        self._idslist = idslist
        
        site = "https://marcosulla.github.io/ewa/"
        self._site = site
        
        self._firm = (
"""/**
 * This file was firstly auto-generated by EWA: 
 * {site}
 */""".format(site=site)
        )
        
        self._firm_donottouch = (
"""/**
 * !!! DO NOT EDIT THIS FILE !!!
 * This file is auto-generated by EWA: 
 * {site}
 */""".format(site=site)
        )
    
    @property
    def class_name(self):
        return self._class_name

    @property
    def aggregator_class(self):
        return self._aggregator_class

    @property
    def aggregator_var(self):
        return self._aggregator_var

    @property
    def table_name(self):
        return self._table_name

    @property
    def ids(self):
        return self._ids

    @property
    def select_methods_prefix(self):
        return self._select_methods_prefix

    @property
    def multiple_ids(self):
        return self._multiple_ids

    @property
    def integer_instead_of_short(self):
        return self._integer_instead_of_short

    @property
    def bigdecimal_instead_of_double(self):
        return self._bigdecimal_instead_of_double

    @property
    def bigdecimal_instead_of_long(self):
        return self._bigdecimal_instead_of_long

    @property
    def dtype(self):
        return self._dtype

    @property
    def user(self):
        return self._user

    @property
    def password(self):
        return self._password

    @property
    def host(self):
        return self._host

    @property
    def port(self):
        return self._port

    @property
    def db_name(self):
        return self._db_name

    @property
    def service_name(self):
        return self._service_name

    @property
    def pack_model(self):
        return self._pack_model

    @property
    def pack_aggregator(self):
        return self._pack_aggregator

    @property
    def pack_repo(self):
        return self._pack_repo

    @property
    def pack_service(self):
        return self._pack_service

    @property
    def pack_utility(self):
        return self._pack_utility

    @property
    def data_dir(self):
        return self._data_dir

    @property
    def rows(self):
        return self._rows

    @property
    def col_types(self):
        return self._col_types

    @property
    def import_date_eff(self):
        return self._import_date_eff

    @property
    def methid(self):
        return self._methid

    @property
    def varname(self):
        return self._varname

    @property
    def initial(self):
        return self._initial

    @property
    def id_col_type(self):
        return self._id_col_type

    @property
    def idsfirm(self):
        return self._idsfirm

    @property
    def idslist(self):
        return self._idslist

    @property
    def indent(self):
        return self._indent

    @property
    def noupdate(self):
        return self._noupdate
    
    @property
    def firm(self):
        return self._firm
    
    @property
    def firm_donottouch(self):
        return self._firm_donottouch

    @property
    def indent(self):
        return self._indent

    @property
    def site(self):
        return self._site
