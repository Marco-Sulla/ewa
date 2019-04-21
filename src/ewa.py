import sqlalchemy.engine
import mylib.msutils as msutils
from pathlib import Path
import os
import argparse
import configparser
import sys

VERSION = "1.5.0"
__version__ = VERSION

try:
    app_dir = Path(__file__).resolve().parent
except NameError:
    app_dir = Path(".")


app_descr = "Java code generator"
help_config = "Set the config file to be read"
help_version = "Print the version and exit"

cmd_parser = argparse.ArgumentParser(description=app_descr)
cmd_parser.add_argument("--config", required=True, help=help_config)
cmd_parser.add_argument("--version", action="store_true", help=help_version)

cmd_args = cmd_parser.parse_args()
cmd_dict = vars(cmd_args)

if cmd_dict.get("version"):
    print(VERSION)
    sys.exit(0)

config_path_tpm = cmd_dict["config"]
config_path = msutils.toAbsPath(config_path_tpm, app_dir)
config = configparser.ConfigParser()
config.read(str(config_path))

class_name = config.get("default", "class_name") # TODO support multiple
aggregator_class = "{class_name}Aggregator".format(class_name=class_name)
aggregator_var = aggregator_class[0].lower() + aggregator_class[1:]
table_name = config.get("default", "table_name").upper()
ids = config.get("default", "ids").upper().split(",")
select_methods_prefix = config.get("default", "select_methods_prefix")

if not select_methods_prefix:
    select_methods_prefix = "get"
else:
    select_methods_prefix = select_methods_prefix.lower()

for i in range(len(ids)):
    ids[i] = ids[i].strip()

multiple_ids = False

if len(ids) > 1:
    multiple_ids = True

integer_instead_of_short = bool(int(config.get("default", "integer_instead_of_short")))
bigdecimal_instead_of_double = bool(int(config.get("default", "bigdecimal_instead_of_double")))
bigdecimal_instead_of_long = bool(int(config.get("default", "bigdecimal_instead_of_long")))

dtype = config.get("database", "type")
user = config.get("database", "user")
password = config.get("database", "password")
host = config.get("database", "host")
port = int(config.get("database", "port"))
db_name = config.get("database", "name")
service_name_str = config.get("database", "service_name")

if service_name_str == "0":
    service_name = False
elif service_name_str == "1":
    service_name = True
else:
    raise ValueError("Invalid value for service name: " + service_name_str)

pack_model = config.get("packages", "model")
pack_aggregator = config.get("packages", "aggregator")
pack_repo = config.get("packages", "repository")
pack_service = config.get("packages", "service")
pack_utility = config.get("packages", "utility")

data_dir = app_dir / "data" / class_name

def writeToFile(pack, filename, content):
    dir = data_dir / pack.replace(".", "/")
    msutils.mkdirP(str(dir))
    path = dir / filename

    with open(str(path), mode="w+") as f:
        f.write(content)


        
model_start = (
"""package {pack_model};
{imports}
public class {class_name} {{"""
)

model_end = "}\n"
indent = "    "
field = "{indent}private {type} {name};"
getter = (
"""{indent}public {type} get{methname}() {{
{indent}{indent}return this.{name};
{indent}}}"""
)

setter = (
"""{indent}public void set{methname}({type} {name}) {{
{indent}{indent}this.{name} = {name};
{indent}}}"""
)

import_date = "import java.util.Date;"

db_str = msutils.dbString(dtype, user, password, host, port, db_name, service_name)

engine = sqlalchemy.engine.create_engine(db_str, echo=False)

if dtype == "mssql":
    import db.mssql as db
elif dtype == "oracle":
    import db.oracle as db
else:
    raise Exception("Unsupported database: " + dtype)

converter = db.convertToJavaType
get_columns_data_sql = db.get_columns_data_sql

rows = engine.execute(get_columns_data_sql.format(table_name))

fields = ""
methods = ""
bigdecimal = False
col_types = {}
import_date_eff = ""

rows = list(rows)

rows_clone = rows[:]
i = 0

for row in rows_clone:
    col_id = row[5]
    
    if col_id is None:
        rows.remove(row)
        i -= 1
    
    i += 1

for row in rows:
    col = row[0].upper()
    ctype = row[1]
    prec = row[2]
    radix = row[3]
    scale = row[4]
    
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
    
    if jtype == "BigDecimal":
        bigdecimal = True
    
    if jtype == "Date":
        import_date_eff = import_date + "\n"
    
    name = col.lower()
    methname = col.capitalize()
    col_types[col] = jtype
    fields += field.format(type=jtype, name=name, indent=indent) + "\n"
    methods += (
        getter.format(
            type = jtype, 
            methname = methname, 
            name = name, 
            select_methods_prefix = select_methods_prefix,
            indent = indent,
        ) + "\n\n" +
         
        setter.format(type=jtype, methname=methname, name=name, indent=indent) + "\n\n"
    )

model = ""
imports = ""

if bigdecimal:
    imports += "import java.math.BigDecimal;\n"

imports += import_date_eff

if imports:
    imports = "\n" + imports + "\n"

model += model_start.format(imports=imports, class_name=class_name, pack_model=pack_model) + "\n"
model += fields + "\n\n" + methods.rstrip() + "\n" + model_end

writeToFile(pack_model, class_name + ".java", model)

if multiple_ids:
    methid = "Ids"
else:
    methid = ids[0][0].upper() + ids[0][1:].lower()

varname = class_name[0].lower() + class_name[1:]
initial = varname[0]

if not multiple_ids:
    id_col_type = col_types[ids[0]]


repo_tpl = (
"""package {pack_repo};
import java.math.BigDecimal;
import java.util.List;
import java.util.stream.Collectors;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Repository;
import org.sql2o.Connection;
import org.sql2o.Query;
import org.sql2o.Sql2o;

import {pack_model}.{class_name};
import {pack_utility}.Sql2oUtility;

@Repository
public class {class_name}RepositoryImpl implements {class_name}Repository {{
{indent}private final Logger logger = LoggerFactory.getLogger(this.getClass());
{indent}
{indent}@Autowired
{indent}private Sql2o sql2o;
{indent}
{indent}private String getSelectBase(List<String> fields_to_ignore) {{
{select_fields}
{indent}{indent}return res;
{indent}}};
{indent}
{indent}@Override
{indent}public {class_name} {select_methods_prefix}By{methid}({idsfirm}, List<String> fields_to_ignore, Connection con) {{
{indent}{indent}logger.debug("DB>> {select_methods_prefix}By{methid}() - {idslog});
{indent}{indent}
{indent}{indent}String sql = "select " + this.getSelectBase(fields_to_ignore) + "from {table_name} {initial} ";
{idswhere}
{indent}{indent}
{indent}{indent}{class_name} res;
{indent}{indent}
{indent}{indent}try (Query query = con.createQuery(sql)) {{
{idsparams}
{indent}{indent}{indent}res = query.executeAndFetchFirst({class_name}.class);
{indent}{indent}}}
{indent}{indent}
{indent}{indent}logger.debug("<< DB getBy{methid}() - END");
{indent}{indent}return res;
{indent}}}
{indent}
{indent}@Override
{indent}public {class_name} {select_methods_prefix}By{methid}({idsfirm}, Connection con) {{
{indent}{indent}return {select_methods_prefix}By{methid}({idslist}, null, con);
{indent}}}
{indent}
{indent}@Override
{indent}public {class_name} {select_methods_prefix}By{methid}({idsfirm}, List<String> fields_to_ignore) {{
{indent}{indent}try (Connection con = sql2o.open()) {{
{indent}{indent}{indent}return this.{select_methods_prefix}By{methid}({idslist}, fields_to_ignore, con);
{indent}{indent}}}
{indent}}}
{indent}
{indent}@Override
{indent}public {class_name} {select_methods_prefix}By{methid}({idsfirm}) {{
{indent}{indent}return this.{select_methods_prefix}By{methid}({idslist}, (List<String>) null);
{indent}}}
{indent}
{indent}@Override
{indent}public List<{class_name}> {select_methods_prefix}All(List<String> fields_to_ignore, Connection con) {{
{indent}{indent}logger.debug("DB>> {select_methods_prefix}All()");
{indent}{indent}
{indent}{indent}String sql = "select " + this.getSelectBase(fields_to_ignore) + "from {table_name} {initial} ";
{indent}{indent}
{indent}{indent}List<{class_name}> res;
{indent}{indent}
{indent}{indent}try (Query query = con.createQuery(sql)) {{
{indent}{indent}{indent}res = query.executeAndFetch({class_name}.class);
{indent}{indent}}}
{indent}{indent}
{indent}{indent}logger.debug("<< DB {select_methods_prefix}All() - END");
{indent}{indent}return res;
{indent}}}
{indent}
{indent}@Override
{indent}public List<{class_name}> {select_methods_prefix}All(Connection con) {{
{indent}{indent}return {select_methods_prefix}All(null, con);
{indent}}}
{indent}
{indent}@Override
{indent}public List<{class_name}> {select_methods_prefix}All(List<String> fields_to_ignore) {{
{indent}{indent}try (Connection con = sql2o.open()) {{
{indent}{indent}{indent}return this.{select_methods_prefix}All(fields_to_ignore, con);
{indent}{indent}}}
{indent}}}
{indent}
{indent}@Override
{indent}public List<{class_name}> {select_methods_prefix}All() {{
{indent}{indent}return {select_methods_prefix}All((List<String>) null);
{indent}}}
{indent}
{indent}@Override
{indent}public List<{class_name}> {select_methods_prefix}ByModel({class_name} {varname}, List<String> fields_to_ignore, Connection con) {{
{indent}{indent}logger.debug("DB>> {select_methods_prefix}ByModel()");
{indent}{indent}
{indent}{indent}String sql = "select " + this.getSelectBase(fields_to_ignore) + "from {table_name} {initial} ";
{indent}{indent}sql += "where ";
{indent}{indent}
{bymodel_where}
{indent}{indent}sql = sql.substring(0, sql.length() - 4);
{indent}{indent}
{indent}{indent}List<{class_name}> res;
{indent}{indent}
{indent}{indent}try (Query query = con.createQuery(sql)) {{
{bymodel_params}
{indent}{indent}{indent}res = query.executeAndFetch({class_name}.class);
{indent}{indent}}}
{indent}{indent}
{indent}{indent}logger.debug("<< DB {select_methods_prefix}ByModel() - END");
{indent}{indent}return res;
{indent}}}
{indent}
{indent}@Override
{indent}public List<{class_name}> {select_methods_prefix}ByModel({class_name} {varname}, Connection con) {{
{indent}{indent}return {select_methods_prefix}ByModel({varname}, null, con);
{indent}}}
{indent}
{indent}@Override
{indent}public List<{class_name}> {select_methods_prefix}ByModel({class_name} {varname}, List<String> fields_to_ignore) {{
{indent}{indent}try (Connection con = sql2o.open()) {{
{indent}{indent}{indent}return this.{select_methods_prefix}ByModel({varname}, fields_to_ignore, con);
{indent}{indent}}}
{indent}}}
{indent}
{indent}@Override
{indent}public List<{class_name}> {select_methods_prefix}ByModel({class_name} {varname}) {{
{indent}{indent}return {select_methods_prefix}ByModel({varname}, (List<String>) null);
{indent}}}
{indent}
{indent}@Override
{indent}public {class_name} insert({class_name} {varname}, Connection con) {{
{indent}{indent}logger.info("DB>> insert()");
{indent}{indent}
{indent}{indent}String sql = (
{indent}{indent}{indent}"insert into {table_name} ( " + 
{insert_fields}
{indent}{indent}{indent}") " + 
{indent}{indent}{indent}"values (" +
{insert_vars}
{indent}{indent}{indent}")"
{indent}{indent});
{indent}{indent}
{indent}{indent}Object key;
{indent}{indent}
{indent}{indent}try (Query query = con.createQuery(sql, true)) {{
{insert_params}
{indent}{indent}{indent}key = query.executeUpdate().getKey();
{indent}{indent}}}
{indent}{indent}
{idkey}
{indent}{indent}logger.info("<< DB insert() - END");
{indent}{indent}return {varname};
{indent}}}
{indent}
{indent}@Override
{indent}public {class_name} insert({class_name} {varname}) {{
{indent}{indent}try (Connection con = sql2o.beginTransaction()) {{
{indent}{indent}{indent}{varname} = this.insert({varname}, con);
{indent}{indent}{indent}con.commit();
{indent}{indent}{indent}return {varname};
{indent}{indent}}}
{indent}}}
{indent}
{update}
{indent}@Override
{indent}public {class_name} save({class_name} {varname}, Connection con) {{
{idsinit}
{indent}{indent}{class_name} {varname}2 = this.{select_methods_prefix}By{methid}({idslist}, null, con);
{indent}{indent}
{indent}{indent}if ({varname}2 == null) {{
{indent}{indent}{indent}return this.insert({varname}, con);
{indent}{indent}}}
{indent}{indent}else {{
{save}
{indent}{indent}}}
{indent}}}
{indent}
{indent}@Override
{indent}public {class_name} save({class_name} {varname}) {{
{indent}{indent}try (Connection con = sql2o.beginTransaction()) {{
{indent}{indent}{indent}{class_name} res = this.save({varname}, con);
{indent}{indent}{indent}con.commit();
{indent}{indent}{indent}return res;
{indent}{indent}}}
{indent}}}
{indent}
{indent}@Override
{indent}public void delete({idsfirm}, Connection con) {{
{indent}{indent}logger.info("DB>> delete() - {idslog});
{indent}{indent}
{indent}{indent}String sql = "delete from {table_name} ";
{idswhere}
{indent}{indent}
{indent}{indent}try (Query query = con.createQuery(sql)) {{
{idsparams}
{indent}{indent}{indent}query.executeUpdate();
{indent}{indent}}}
{indent}{indent}
{indent}{indent}logger.info("<< DB delete() - END");
{indent}}}
{indent}
{indent}@Override
{indent}public void delete({idsfirm}) {{
{indent}{indent}try (Connection con = sql2o.beginTransaction()) {{
{indent}{indent}{indent}this.delete({idslist}, con);
{indent}{indent}{indent}con.commit();
{indent}{indent}}}
{indent}}}
{indent}
{indent}@Override
{indent}public void deleteByModel({class_name} {varname}, Connection con) {{
{indent}{indent}logger.info("DB>> deleteByModel()");
{indent}{indent}
{indent}{indent}String sql = "delete from {table_name} ";
{indent}{indent}sql += "where ";
{indent}{indent}
{bymodel_where}
{indent}{indent}sql = sql.substring(0, sql.length() - 4);
{indent}{indent}
{indent}{indent}try (Query query = con.createQuery(sql)) {{
{bymodel_params}
{indent}{indent}{indent}query.executeUpdate();
{indent}{indent}}}
{indent}{indent}
{indent}{indent}logger.info("<< DB deleteByModel() - END");
{indent}}}
{indent}
{indent}@Override
{indent}public void deleteByModel({class_name} {varname}) {{
{indent}{indent}try (Connection con = sql2o.beginTransaction()) {{
{indent}{indent}{indent}this.deleteByModel({varname}, con);
{indent}{indent}{indent}con.commit();
{indent}{indent}}}
{indent}}}
}}
"""
)

save_tpl = (
"""{indent}{indent}{indent}return this.update({varname}, false, con);
{indent}{indent}{indent}"""
)

idkey = "";

if not multiple_ids:
    idkey_mssql_tpl = "{indent}{indent}Object res = key;"

    idkey_oracle_tpl = """{indent}{indent}Object res = Sql2oUtility.getInsertedId("{table_name}", "{id0}", con, key);"""

    if dtype == "mssql":
        idkey = idkey_mssql_tpl.format(indent=indent)
    elif dtype == "oracle":
        idkey = idkey_oracle_tpl.format(
            indent = indent, 
            id0 = ids[0], 
            table_name = table_name
        )

    idkey_end_tpl = (
"""
{indent}{indent}
{indent}{indent}Object res_true;
{indent}{indent}Class<?> klass = {id_col_type}.class;
{indent}{indent}
{indent}{indent}if (res != null && (klass == Long.class || klass == BigDecimal.class)) {{
{indent}{indent}{indent}res_true = ((BigDecimal) res).longValue();
{indent}{indent}}}
{indent}{indent}else {{
{indent}{indent}{indent}res_true = res;
{indent}{indent}}}
{indent}{indent}
{indent}{indent}{varname}.set{methid}(({id_col_type}) res_true);"""
)

    idkey_end = idkey_end_tpl.format(
        indent = indent, 
        methid = methid, 
        varname = varname,
        id_col_type = id_col_type
    )
    
    idkey += idkey_end

update_tpl = (
"""{indent}@Override
{indent}public {class_name} update({class_name} {varname}, boolean exclude_nulls, Connection con) {{
{indent}{indent}logger.info("DB>> update() - {idslog_update});
{indent}{indent}
{indent}{indent}String sql = "update {table_name} set ";
{indent}{indent}
{update_fields}
{indent}{indent}sql = sql.substring(0, sql.length() - 2) + " ";
{idswhere}
{indent}{indent}
{indent}{indent}try (Query query = con.createQuery(sql)) {{
{update_params}
{indent}{indent}{indent}query.executeUpdate();
{indent}{indent}}}
{indent}{indent}
{indent}{indent}logger.info("<< DB update() - END");
{indent}{indent}return {varname};
{indent}}}
{indent}
{indent}@Override
{indent}public {class_name} update({class_name} {varname}, boolean exclude_nulls) {{
{indent}{indent}try (Connection con = sql2o.beginTransaction()) {{
{indent}{indent}{indent}{varname} = this.update({varname}, exclude_nulls, con);
{indent}{indent}{indent}con.commit();
{indent}{indent}{indent}return {varname};
{indent}{indent}}}
{indent}}}
{indent}"""
)



idsfirm = ""
idslog = ""
idslog_update = ""
idswhere = '{indent}{indent}sql += "where "; \n'.format(indent=indent)
idsinit = ""
idsparams = ""
idslist = ""
idshasdate = False

for id in ids:
    col_type = col_types[id]
    varid = id.lower()
    methid = id[0] + id[1:].lower()
    
    if col_type == "Date":
        idshasdate = True
    
    idsfirm += "{} {}, ".format(col_type, id.lower())
    idslog += '{varid}: " + {varid} + "'.format(varid=varid)
    
    idslog_update += '{varid}: " + {varname}.get{methid}() + "'.format(
        varid = varid, 
        varname = varname, 
        methid = methid, 
    )
    
    idswhere += '{indent}{indent}sql += "{id} = :{varid} and "; \n'.format(
        indent = indent, 
        id = id, 
        varid = varid
    )
    
    idsinit += '{indent}{indent}{col_type} {varid} = {varname}.get{methid}();\n'.format(
        indent = indent, 
        col_type = col_type,
        varid = varid,
        varname = varname,
        methid = methid,
        select_methods_prefix = select_methods_prefix,
    )
    
    idsparams += '{indent}{indent}{indent}query.addParameter("{varid}", {varid});\n'.format(
        indent = indent, 
        varid = id.lower(),
    )
    
    idslist += "{}, ".format(varid)

idsfirm = idsfirm[:-2]
idslog = idslog[:-4]
idslog_update = idslog_update[:-4]
idswhere = idswhere[:-8] + '";'
idslist = idslist[:-2]    


select_fields_tpl = '{indent}{indent}String res = "";'

select_fields_tpl += (
"""
{indent}{indent}
{indent}{indent}fields_to_ignore = fields_to_ignore
{indent}{indent}{indent}.stream()
{indent}{indent}{indent}.map(field -> field.toUpperCase())
{indent}{indent}{indent}.collect(Collectors.toList());
{indent}{indent}
"""
)
        
select_fields = select_fields_tpl.format(indent=indent)


insert_fields = ""
insert_vars = ""
insert_params = ""
update_params_tpl = ""
bymodel_params_tpl = ""
update_fields_tpl = ""
bymodel_where_tpl = ""

noupdate = True


    
insert_params = '{indent}{indent}{indent}query.bind({varname});\n'.format(
    varname = varname,
    indent = indent
)

for i, col in enumerate(col_types):
    colname = col.lower()
    methcol = colname[0].upper() + colname[1:]
    
    select_field_tpl = '{indent}{indent}if (fields_to_ignore != null && ! fields_to_ignore.contains("{col}")) {{\n'
    select_field_tpl += '{indent}{indent}{indent}res += "{initial}.{col}, ";\n'
    
    select_field_tpl += '{indent}{indent}}}\n{indent}{indent}\n'
    select_field = select_field_tpl.format(indent=indent, initial=initial, col=col)
    select_fields += select_field
    
    insert_fields += '{indent}{indent}{indent}{indent}"{col}, " + \n'.format(col=col, indent=indent)
    insert_vars += '{indent}{indent}{indent}{indent}":{col}, " + \n'.format(col=col.lower(), indent=indent)
    
    update_params_tpl += (
"""{indent}{indent}{indent}if (! exclude_nulls || {varname}.get{methcol}() != null) {{
{indent}{indent}{indent}{indent}query.addParameter("{colname}", {varname}.get{methcol}());
{indent}{indent}{indent}}}
{indent}{indent}{indent}
"""
)

    update_params = update_params_tpl.format(
        colname = colname,
        varname = varname,
        methcol = methcol,
        indent = indent,
        select_methods_prefix = select_methods_prefix,
    )
    
    bymodel_params_tpl += (
"""{indent}{indent}{indent}if ({varname}.get{methcol}() != null) {{
{indent}{indent}{indent}{indent}query.addParameter("{colname}", {varname}.get{methcol}());
{indent}{indent}{indent}}}
{indent}{indent}{indent}
"""
)
    bymodel_params = bymodel_params_tpl.format(
        colname = colname,
        varname = varname,
        methcol = methcol,
        indent = indent,
        select_methods_prefix = select_methods_prefix,
    )
    
    noupdate = False

    bymodel_where_tpl += (
"""{indent}{indent}if ({varname}.get{methcol}() != null) {{ 
{indent}{indent}{indent} sql += "{col} = :{colname} and ";
{indent}{indent}}}
{indent}{indent}
"""
)

    bymodel_where = bymodel_where_tpl.format(
        col = col, 
        colname = colname, 
        indent = indent, 
        varname = varname, 
        methcol = methcol,
        select_methods_prefix = select_methods_prefix,
    )
    
    if col not in ids:
        noupdate = False
        
        update_fields_tpl += (
"""{indent}{indent}if (! exclude_nulls || {varname}.get{methcol}() != null) {{ 
{indent}{indent}{indent} sql += "{col} = :{colname}, ";
{indent}{indent}}}
{indent}{indent}
"""
)

        update_fields = update_fields_tpl.format(
            col = col, 
            colname = colname, 
            indent = indent, 
            varname = varname, 
            methcol = methcol,
            select_methods_prefix = select_methods_prefix,
        )

select_fields_end_tpl = (
"""{indent}{indent}res = res.substring(0, res.length() - 2);
{indent}{indent}"""
)

select_fields_end = select_fields_end_tpl.format(indent = indent)
select_fields += select_fields_end

insert_fields = insert_fields[:-7] + ' " + '
insert_vars = insert_vars[:-7] + ' " + '
bymodel_params = bymodel_params[:-1]
bymodel_where = bymodel_where[:-1]
update_fields = update_fields[:-1]


if noupdate:
    update = ""
    save_tpl = "{indent}{indent}{indent}return null;"
    save = save_tpl.format(indent=indent)
else:
    update = update_tpl.format(
        indent = indent, 
        idswhere = idswhere, 
        class_name = class_name, 
        table_name = table_name, 
        update_fields = update_fields, 
        varname = varname, 
        update_params = update_params,
        idslog_update = idslog_update, 
    )
    
    save = save_tpl.format(
        indent = indent, 
        varname = varname
    )

repo = repo_tpl.format(
    indent = indent, 
    class_name = class_name, 
    methid = methid, 
    idsfirm = idsfirm,
    idslog = idslog, 
    idswhere = idswhere, 
    idsparams = idsparams, 
    idsinit = idsinit,
    idslist = idslist, 
    table_name = table_name,
    varname = varname,
    select_fields = select_fields,
    insert_fields = insert_fields,
    insert_vars = insert_vars,
    insert_params = insert_params,
    bymodel_params = bymodel_params,
    bymodel_where = bymodel_where,
    initial = initial,
    pack_model = pack_model,
    pack_utility = pack_utility,
    pack_repo = pack_repo,
    update = update,
    save = save,
    idkey = idkey,
    select_methods_prefix = select_methods_prefix,
)
    
writeToFile(pack_repo, class_name + "RepositoryImpl.java", repo)


repoint_tpl = (
"""package {pack_repo};
{imports}
import java.util.List;

import org.sql2o.Connection;

import {pack_model}.{class_name};

public interface {class_name}Repository {{
{indent}{class_name} {select_methods_prefix}By{methid}({idsfirm}, List<String> fields_to_ignore, Connection con);
{indent}
{indent}{class_name} {select_methods_prefix}By{methid}({idsfirm}, Connection con);
{indent}
{indent}{class_name} {select_methods_prefix}By{methid}({idsfirm}, List<String> fields_to_ignore);
{indent}
{indent}{class_name} {select_methods_prefix}By{methid}({idsfirm});
{indent}
{indent}{class_name} insert({class_name} {varname}, Connection con);
{indent}
{indent}{class_name} insert({class_name} {varname});
{update}
{indent}
{indent}{class_name} save({class_name} {varname}, Connection con);
{indent}
{indent}{class_name} save({class_name} {varname});
{indent}
{indent}List<{class_name}> {select_methods_prefix}All(List<String> fields_to_ignore, Connection con);
{indent}
{indent}List<{class_name}> {select_methods_prefix}All(Connection con);
{indent}
{indent}List<{class_name}> {select_methods_prefix}All(List<String> fields_to_ignore);
{indent}
{indent}List<{class_name}> {select_methods_prefix}All();
{indent}
{indent}List<{class_name}> {select_methods_prefix}ByModel({class_name} {varname}, List<String> fields_to_ignore, Connection con);
{indent}
{indent}List<{class_name}> {select_methods_prefix}ByModel({class_name} {varname}, Connection con);
{indent}
{indent}List<{class_name}> {select_methods_prefix}ByModel({class_name} {varname}, List<String> fields_to_ignore);
{indent}
{indent}List<{class_name}> {select_methods_prefix}ByModel({class_name} {varname});
{indent}
{indent}void delete({idsfirm}, Connection con);
{indent}
{indent}void delete({idsfirm});
{indent}
{indent}void deleteByModel({class_name} {varname}, Connection con);
{indent}
{indent}void deleteByModel({class_name} {varname});
}}
"""
)

update_tpl = (
"""{indent}
{indent}{class_name} update({class_name} {varname}, boolean exclude_nulls, Connection con);
{indent}
{indent}{class_name} update({class_name} {varname}, boolean exclude_nulls);"""
)

if noupdate:
    update = ""
else:
    update = update_tpl.format(indent=indent, class_name=class_name, varname=varname)

imports = ""

if import_date_eff:
    imports = "\n" + import_date_eff + "\n"

repoint = repoint_tpl.format(
    imports = imports,
    class_name = class_name,
    varname = varname,
    methid = methid,
    indent = indent,
    idsfirm = idsfirm,
    pack_repo = pack_repo,
    pack_model = pack_model,
    update = update,
    select_methods_prefix = select_methods_prefix,
)

writeToFile(pack_repo, class_name + "Repository.java", repoint)


service_tpl = (
"""package {pack_service};
{imports}
import java.util.ArrayList;
import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.sql2o.Connection;

import {pack_aggregator}.{aggregator_class};
import {pack_model}.{class_name};
import {pack_repo}.{class_name}Repository;


@Service
public class {class_name}ServiceImpl implements {class_name}Service {{
{indent}@Autowired
{indent}private {class_name}Repository {varname}Repository;
{indent}
{indent}private {aggregator_class} enrich({class_name} {varname}) {{
{indent}{indent}{aggregator_class} {aggregator_var} = null;
{indent}{indent}
{indent}{indent}if ({varname} != null) {{
{indent}{indent}{indent}{aggregator_var} = new {aggregator_class}();
{indent}{indent}{indent}
{indent}{indent}{indent}{aggregator_var}.set{class_name}({varname});
{indent}{indent}}}
{indent}{indent}
{indent}{indent}return {aggregator_var};
{indent}}}
{indent}
{indent}private List<{aggregator_class}> enrich(List<{class_name}> {varname}s) {{
{indent}{indent}List<{aggregator_class}> {aggregator_var}s = new ArrayList<>();
{indent}{indent}
{indent}{indent}if ({varname}s != null) {{
{indent}{indent}{indent}for ({class_name} {varname}: {varname}s) {{
{indent}{indent}{indent}{indent}{aggregator_var}s.add(this.enrich({varname}));
{indent}{indent}{indent}}}
{indent}{indent}}}
{indent}{indent}
{indent}{indent} return {aggregator_var}s;
{indent}}}
{indent}
{indent}@Override
{indent}public List<{aggregator_class}> {select_methods_prefix}All(List<String> fields_to_ignore, Connection con) {{
{indent}{indent}List<{class_name}> {varname}s = {varname}Repository.{select_methods_prefix}All(fields_to_ignore, con);
{indent}{indent}
{indent}{indent}return this.enrich({varname}s);
{indent}}}
{indent}
{indent}@Override
{indent}public List<{aggregator_class}> {select_methods_prefix}All(Connection con) {{
{indent}{indent}List<{class_name}> {varname}s = {varname}Repository.{select_methods_prefix}All(con);
{indent}{indent}
{indent}{indent}return this.enrich({varname}s);
{indent}}}
{indent}
{indent}@Override
{indent}public List<{aggregator_class}> {select_methods_prefix}All(List<String> fields_to_ignore) {{
{indent}{indent}List<{class_name}> {varname}s = {varname}Repository.{select_methods_prefix}All(fields_to_ignore);
{indent}{indent}
{indent}{indent}return this.enrich({varname}s);
{indent}}}
{indent}
{indent}@Override
{indent}public List<{aggregator_class}> {select_methods_prefix}All() {{
{indent}{indent}List<{class_name}> {varname}s = {varname}Repository.{select_methods_prefix}All();
{indent}{indent}
{indent}{indent}return this.enrich({varname}s);
{indent}}}
{indent}
{indent}@Override
{indent}public List<{aggregator_class}> {select_methods_prefix}ByModel({class_name} {varname}, List<String> fields_to_ignore, Connection con) {{
{indent}{indent}List<{class_name}> {varname}s = {varname}Repository.{select_methods_prefix}ByModel({varname}, fields_to_ignore, con);
{indent}{indent}
{indent}{indent}return this.enrich({varname}s);
{indent}}}
{indent}
{indent}@Override
{indent}public List<{aggregator_class}> {select_methods_prefix}ByModel({class_name} {varname}, Connection con) {{
{indent}{indent}List<{class_name}> {varname}s = {varname}Repository.{select_methods_prefix}ByModel({varname}, con);
{indent}{indent}
{indent}{indent}return this.enrich({varname}s);
{indent}}}
{indent}
{indent}@Override
{indent}public List<{aggregator_class}> {select_methods_prefix}ByModel({class_name} {varname}, List<String> fields_to_ignore) {{
{indent}{indent}List<{class_name}> {varname}s = {varname}Repository.{select_methods_prefix}ByModel({varname}, fields_to_ignore);
{indent}{indent}
{indent}{indent}return this.enrich({varname}s);
{indent}}}
{indent}
{indent}@Override
{indent}public List<{aggregator_class}> {select_methods_prefix}ByModel({class_name} {varname}) {{
{indent}{indent}List<{class_name}> {varname}s = {varname}Repository.{select_methods_prefix}ByModel({varname});
{indent}{indent}
{indent}{indent}return this.enrich({varname}s);
{indent}}}
{indent}
{indent}@Override
{indent}public {aggregator_class} {select_methods_prefix}By{methid}({idsfirm}, List<String> fields_to_ignore, Connection con) {{
{indent}{indent}{class_name} {varname} = {varname}Repository.{select_methods_prefix}By{methid}({idslist}, fields_to_ignore, con);
{indent}{indent}
{indent}{indent}return this.enrich({varname});
{indent}}}
{indent}
{indent}@Override
{indent}public {aggregator_class} {select_methods_prefix}By{methid}({idsfirm}, Connection con) {{
{indent}{indent}{class_name} {varname} = {varname}Repository.{select_methods_prefix}By{methid}({idslist}, con);
{indent}{indent}
{indent}{indent}return this.enrich({varname});
{indent}}}
{indent}
{indent}@Override
{indent}public {aggregator_class} {select_methods_prefix}By{methid}({idsfirm}, List<String> fields_to_ignore) {{
{indent}{indent}{class_name} {varname} = {varname}Repository.{select_methods_prefix}By{methid}({idslist}, fields_to_ignore);
{indent}{indent}
{indent}{indent}return this.enrich({varname});
{indent}}}
{indent}
{indent}@Override
{indent}public {aggregator_class} {select_methods_prefix}By{methid}({idsfirm}) {{
{indent}{indent}{class_name} {varname} = {varname}Repository.{select_methods_prefix}By{methid}({idslist});
{indent}{indent}
{indent}{indent}return this.enrich({varname});
{indent}}}
{indent}
{indent}@Override
{indent}public {class_name} insert({class_name} {varname}, Connection con) {{
{indent}{indent}return {varname}Repository.insert({varname}, con);
{indent}}}
{indent}
{indent}@Override
{indent}public {class_name} insert({class_name} {varname}) {{
{indent}{indent}return {varname}Repository.insert({varname});
{indent}}}
{update}
{indent}
{indent}@Override
{indent}public {class_name} save({class_name} {varname}, Connection con) {{
{indent}{indent}return {varname}Repository.save({varname}, con);
{indent}}}
{indent}
{indent}@Override
{indent}public {class_name} save({class_name} {varname}) {{
{indent}{indent}return {varname}Repository.save({varname});
{indent}}}
{indent}
{indent}@Override
{indent}public void delete({idsfirm}, Connection con) {{
{indent}{indent}{varname}Repository.delete({idslist}, con);
{indent}}}
{indent}
{indent}@Override
{indent}public void delete({idsfirm}) {{
{indent}{indent}{varname}Repository.delete({idslist});
{indent}}}
{indent}
{indent}@Override
{indent}public void deleteByModel({class_name} {varname}, Connection con) {{
{indent}{indent}{varname}Repository.deleteByModel({varname}, con);
{indent}}}
{indent}
{indent}@Override
{indent}public void deleteByModel({class_name} {varname}) {{
{indent}{indent}{varname}Repository.deleteByModel({varname});
{indent}}}
}}
"""
)

update_tpl = (
"""{indent}
{indent}@Override
{indent}public {class_name} update({class_name} {varname}, boolean exclude_nulls, Connection con) {{
{indent}{indent}return {varname}Repository.update({varname}, exclude_nulls, con);
{indent}}}
{indent}
{indent}@Override
{indent}public {class_name} update({class_name} {varname}, boolean exclude_nulls) {{
{indent}{indent}return {varname}Repository.update({varname}, exclude_nulls);
{indent}}}"""
)

if noupdate:
    update = ""
else:
    update = update_tpl.format(indent=indent, class_name=class_name, varname=varname)

service = service_tpl.format(
    imports = imports,
    class_name = class_name,
    varname = varname,
    idsfirm = idsfirm,
    idslist = idslist,
    methid = methid,
    indent = indent,
    pack_model = pack_model,
    pack_repo = pack_repo,
    pack_service = pack_service,
    update = update,
    select_methods_prefix = select_methods_prefix,
    aggregator_class = aggregator_class, 
    aggregator_var = aggregator_var, 
    pack_aggregator = pack_aggregator, 
)

writeToFile(pack_service, class_name + "ServiceImpl.java", service)

serviceint_tpl = (
"""package {pack_service};
{imports}
import java.util.List;

import org.sql2o.Connection;

import {pack_aggregator}.{aggregator_class};
import {pack_model}.{class_name};

public interface {class_name}Service {{
{indent}{aggregator_class} {select_methods_prefix}By{methid}({idsfirm}, List<String> fields_to_ignore, Connection con);
{indent}
{indent}{aggregator_class} {select_methods_prefix}By{methid}({idsfirm}, Connection con);
{indent}
{indent}{aggregator_class} {select_methods_prefix}By{methid}({idsfirm}, List<String> fields_to_ignore);
{indent}
{indent}{aggregator_class} {select_methods_prefix}By{methid}({idsfirm});
{indent}
{indent}{class_name} insert({class_name} {varname}, Connection con);
{indent}
{indent}{class_name} insert({class_name} {varname});
{update}
{indent}
{indent}{class_name} save({class_name} {varname}, Connection con);
{indent}
{indent}{class_name} save({class_name} {varname});
{indent}
{indent}List<{aggregator_class}> {select_methods_prefix}All(List<String> fields_to_ignore, Connection con);
{indent}
{indent}List<{aggregator_class}> {select_methods_prefix}All(Connection con);
{indent}
{indent}List<{aggregator_class}> {select_methods_prefix}All(List<String> fields_to_ignore);
{indent}
{indent}List<{aggregator_class}> {select_methods_prefix}All();
{indent}
{indent}List<{aggregator_class}> {select_methods_prefix}ByModel({class_name} {varname}, List<String> fields_to_ignore, Connection con);
{indent}
{indent}List<{aggregator_class}> {select_methods_prefix}ByModel({class_name} {varname}, Connection con);
{indent}
{indent}List<{aggregator_class}> {select_methods_prefix}ByModel({class_name} {varname}, List<String> fields_to_ignore);
{indent}
{indent}List<{aggregator_class}> {select_methods_prefix}ByModel({class_name} {varname});
{indent}
{indent}void delete({idsfirm}, Connection con);
{indent}
{indent}void delete({idsfirm});
{indent}
{indent}void deleteByModel({class_name} {varname}, Connection con);
{indent}
{indent}void deleteByModel({class_name} {varname});
}}
"""
)

update_tpl = (
"""{indent}
{indent}{class_name} update({class_name} {varname}, boolean exclude_nulls, Connection con);
{indent}
{indent}{class_name} update({class_name} {varname}, boolean exclude_nulls);"""
)

if noupdate:
    update = ""
else:
    update = update_tpl.format(indent=indent, class_name=class_name, varname=varname)


serviceint = serviceint_tpl.format(
    imports = imports,
    class_name = class_name,
    varname = varname,
    methid = methid,
    idsfirm = idsfirm,
    indent = indent,
    pack_service = pack_service,
    pack_model = pack_model,
    update = update,
    select_methods_prefix = select_methods_prefix,
    aggregator_class = aggregator_class, 
    pack_aggregator = pack_aggregator, 
)

writeToFile(pack_service, class_name + "Service.java", serviceint)

aggregator_tpl = (
"""package {pack_aggregator};

import {pack_model}.{class_name};

public class {class_name}Aggregator {{
{indent}private {class_name} {varname};
{indent}
{indent}public {class_name} get{class_name}() {{
{indent}{indent}return this.{varname};
{indent}}}
{indent}
{indent}public void set{class_name}({class_name} {varname}) {{
{indent}{indent}this.{varname} = {varname};
{indent}}}
}}
"""
)

aggregator = aggregator_tpl.format(
    pack_aggregator = pack_aggregator, 
    pack_model = pack_model, 
    class_name = class_name, 
    varname = varname,
    indent = indent,  
)

writeToFile(pack_aggregator, class_name + "Aggregator.java", aggregator)


sql2outility_tpl = (
"""package {pack_utility};

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import org.sql2o.Connection;
import org.sql2o.Query;

@Component
public class Sql2oUtility {{
{indent}public static Object getInsertedId(
{indent}{indent}String table, 
{indent}{indent}String idfield, 
{indent}{indent}Connection con, 
{indent}{indent}Object key
{indent}) {{
{indent}{indent}try (Query queryid = con.createQuery("SELECT " + idfield + " FROM " + table + " WHERE rowid  = :key")) {{
{indent}{indent}{indent}queryid.addParameter("key", key);
{indent}{indent}{indent}Object obj = queryid.executeAndFetchFirst(Object.class);
{indent}{indent}{indent}return obj;
{indent}{indent}}}  
{indent}}}
}}
"""
)

sql2outility = sql2outility_tpl.format(pack_utility=pack_utility, indent=indent)

writeToFile(pack_utility, "Sql2oUtility.java", sql2outility)

print("Files saved in " + str(data_dir))
print(
"""

!!!IMPORTANT!!! 

* Please check the insert and update methods in repo, in particular for""" + 
"""autoincrement columns as parameter that does not accept value in insert.

* Remove also in update fields that should never be updated, like createdby or createdon.

* If you want, you can also add a toString() to models and enrich the logging of""" + 
"""getByModel, deleteByModel and insert
"""
)

