import sqlalchemy.engine
import mylib.msutils as msutils
from pathlib import Path
import os
import argparse
import configparser
import re
import sys

VERSION = "3.0.0"

try:
    app_dir = Path(__file__).resolve().parent
except NameError:
    app_dir = Path(".")


app_descr = "Java code generator"
help_config = "Set the config file to be read"
help_version = "Print the version and exit"

java_integer_types = ("BigDecimal", "BigInteger", "Long", "Short")

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
table_name = config.get("default", "table_name").upper()
ids = config.get("default", "ids").upper().split(",")

for i in range(len(ids)):
    ids[i] = ids[i].strip()

multiple_ids = False

if len(ids) > 1:
    multiple_ids = True

integer_instead_of_short = bool(int(config.get("default", "integer_instead_of_short")))
bigdecimal_instead_of_double = bool(int(config.get("default", "bigdecimal_instead_of_double")))
biginteger_instead_of_long = bool(int(config.get("default", "biginteger_instead_of_long")))

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
pack_repo = config.get("packages", "repository")
pack_service = config.get("packages", "service")
pack_utility = config.get("packages", "utility")

re_ts = re.compile("timestamp\(\d+\)")

def convertMsSqlToJavaType(
    sql_type, 
    prec, 
    radix, 
    scale, 
    use_bigdecimal_instead_of_double, 
    use_biginteger_instead_of_long
):
    sql_type = sql_type.lower()

    if prec is None:
        prec = 0

    if scale is None:
        scale = 0
    
    if sql_type == "numeric":
        if scale == 0:
            maxn = radix**(prec - scale)
            
            if maxn < 2**16:
                if integer_instead_of_short:
                    return "Integer"
                else:
                    return "Short"
            elif maxn < 2**32:
                return "Integer"
            elif maxn < 2**64:
                return "Long"
            else:
                if use_biginteger_instead_of_long:
                    return "BigInteger"
                else:
                    return "Long"
        else:
            if use_bigdecimal_instead_of_double:
                return "BigDecimal"
            else:
                return "Double"
        return "Long"
    elif sql_type == "int":
        return "Integer"
    elif sql_type == "datetime2":
        return "Date"
    elif sql_type == "timestamp":
        return "Date"
    elif sql_type == "varchar":
        return "String"
    elif sql_type == "char":
        return "String"
    else:
        raise Exception("Unsupported type: {}".format(sql_type))

def convertOracleToJavaType(
    sql_type, 
    prec, 
    radix, 
    scale, 
    use_bigdecimal_instead_of_double, 
    use_biginteger_instead_of_long
):

    if prec is None:
        prec = 0

    if scale is None:
        scale = 0
    
    sql_type = sql_type.lower()
    
    if sql_type == "number":
        
        if scale == 0:
            maxn = radix**(prec - scale)
            if maxn < 2**16:
                if integer_instead_of_short:
                    return "Integer"
                else:
                    return "Short"
            elif maxn < 2**32:
                return "Integer"
            elif maxn < 2**64:
                return "Long"
            else:
                if use_biginteger_instead_of_long:
                    return "BigInteger"
                else:
                    return "Long"
        else:
            if use_bigdecimal_instead_of_double:
                return "BigDecimal"
            else:
                return "Double"
        return "Long"
    elif re_ts.match(sql_type):
        return "Date"
    elif sql_type in ("varchar", "varchar2", "char"):
        return "String"
    elif sql_type == "date":
        return "Date"
    else:
        raise Exception("Unsupported type: {}".format(sql_type))

        
class_start = """package {pack_model};
{imports}
public class {class_name} {{"""

class_end = "}"
indent = "    "
field = indent + "private {type} {name};"
getter = (
    indent + "public {type} get{methname}() {{\n" + 
    indent + indent + "return {name};\n" + 
    indent + "}}"
)
setter = (
    indent + "public void set{methname}({type} {name}) {{\n" + 
    indent + indent + "this.{name} = {name};\n" + 
    indent + "}}"
)
import_date = "import java.util.Date;"

db_str = msutils.dbString(dtype, user, password, host, port, db_name, service_name)

engine = sqlalchemy.engine.create_engine(db_str, echo=False)

get_columns_data_sql_mssql = """
SELECT 
    column_name, 
    data_type, 
    numeric_precision, 
    numeric_precision_radix,
    numeric_scale,
    1
FROM INFORMATION_SCHEMA.COLUMNS
WHERE upper(TABLE_NAME) = N'{}'
ORDER BY column_name ASC
"""

get_columns_data_sql_oracle = """
SELECT 
    column_name, 
    data_type, 
    data_precision, 
    data_length, 
    data_scale,
    column_id
FROM ALL_TAB_COLS 
WHERE UPPER(table_name) = '{}' 
ORDER BY column_name ASC
"""

if dtype == "mssql":
    converter = convertMsSqlToJavaType
    get_columns_data_sql = get_columns_data_sql_mssql
elif dtype == "oracle":
    converter = convertOracleToJavaType
    get_columns_data_sql = get_columns_data_sql_oracle
else:
    raise Exception("Unsupported database: " + dtype)

rows = engine.execute(get_columns_data_sql.format(table_name))

fields = ""
methods = ""
bigdecimal = False
biginteger = False
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
        bigdecimal_instead_of_double, 
        biginteger_instead_of_long
    )
    
    if jtype == "BigDecimal":
        bigdecimal = True
    
    if jtype == "BigInteger":
        biginteger = True
    
    if jtype == "Date":
        import_date_eff = import_date + "\n"
    
    name = col.lower()
    methname = col.capitalize()
    col_types[col] = jtype
    fields += field.format(type=jtype, name=name) + "\n"
    methods += (
        getter.format(type=jtype, methname=methname, name=name) + "\n\n" + 
        setter.format(type=jtype, methname=methname, name=name) + "\n\n"
    )

res = ""
imports = ""

if bigdecimal:
    imports += "import java.math.BigDecimal;\n"

if biginteger:
    imports += "import java.math.BigInteger;\n"

imports += import_date_eff

if imports:
    imports = "\n" + imports + "\n"

res += class_start.format(imports=imports, class_name=class_name, pack_model=pack_model) + "\n"
res += fields + "\n\n" + methods.rstrip() + "\n" + class_end


if multiple_ids:
    methid = "Ids"
else:
    methid = ids[0][0].upper() + ids[0][1:].lower()

varname = class_name[0].lower() + class_name[1:]
initial = varname[0]
if not multiple_ids:
    id_col_type = col_types[ids[0]]


data_dir = app_dir / "data" / class_name
model_dir = data_dir / pack_model.replace(".", "/")

msutils.mkdirP(str(model_dir))

model_path = model_dir / (class_name + ".java")

with open(str(model_path), mode="w+") as f:
    f.write(res)




repo = """package {pack_repo};
{imports}
import java.util.List;
import java.util.stream.Collectors;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Repository;
import org.sql2o.Connection;
import org.sql2o.Query;
import org.sql2o.Sql2o;
import org.sql2o.Sql2oException;

import {pack_model}.{name};
import {pack_utility}.Sql2oUtility;

@Repository
public class {name}RepositoryImpl implements {name}Repository {{
{indent}private final Logger logger = LoggerFactory.getLogger(this.getClass());
{indent}
{indent}@Autowired
{indent}private Sql2o sql2o;
{indent}
{indent}private String getSelectBase(List<String> fields_to_ignore) {{
{select_fields}{indent}{indent}return res;
{indent}}};
{indent}
{indent}@Override
{indent}public {name} getBy{methid}({idsfirm}, List<String> fields_to_ignore, Query query, Connection con) {{
{indent}{indent}logger.debug("{name}Repository.getBy{methid}(): {idslog});
{indent}{indent}
{indent}{indent}String sql = "select " + this.getSelectBase(fields_to_ignore) + "from {table_name} {initial} ";
{idswhere}
{indent}{indent}
{indent}{indent}try {{
{indent}{indent}{indent}Sql2oUtility.setSqlToQuery(query, sql);
{indent}{indent}}}
{indent}{indent}catch (
{indent}{indent}{indent}NoSuchFieldException | 
{indent}{indent}{indent}IllegalArgumentException | 
{indent}{indent}{indent}IllegalAccessException e
{indent}{indent}) {{
{indent}{indent}{indent}throw new Sql2oException("Unable to set sql to query");
{indent}{indent}}}
{indent}{indent}
{idsparams}
{indent}{indent}{name} res = query.executeAndFetchFirst({name}.class);
{indent}{indent}return res;
{indent}}}
{indent}
{indent}@Override
{indent}public {name} getBy{methid}({idsfirm}, List<String> fields_to_ignore) {{
{indent}{indent}try (Connection con = sql2o.open(); Query query = con.createQuery("")) {{
{indent}{indent}{indent}return this.getBy{methid}({idslist}, fields_to_ignore, query, con);
{indent}{indent}}}
{indent}}}
{indent}
{indent}@Override
{indent}public List<{name}> getAll(List<String> fields_to_ignore, Query query, Connection con) {{
{indent}{indent}logger.debug("{name}Repository.getAll()");
{indent}{indent}
{indent}{indent}String sql = "select " + this.getSelectBase(fields_to_ignore) + "from {table_name} {initial} ";
{indent}{indent}
{indent}{indent}try {{
{indent}{indent}{indent}Sql2oUtility.setSqlToQuery(query, sql);
{indent}{indent}}}
{indent}{indent}catch (
{indent}{indent}{indent}NoSuchFieldException | 
{indent}{indent}{indent}IllegalArgumentException | 
{indent}{indent}{indent}IllegalAccessException e
{indent}{indent}) {{
{indent}{indent}{indent}throw new Sql2oException("Unable to set sql to query");
{indent}{indent}}}
{indent}{indent}
{indent}{indent}List<{name}> res = query.executeAndFetch({name}.class);
{indent}{indent}return res;
{indent}}}
{indent}
{indent}@Override
{indent}public List<{name}> getAll(List<String> fields_to_ignore) {{
{indent}{indent}try (Connection con = sql2o.open(); Query query = con.createQuery("")) {{
{indent}{indent}{indent}return this.getAll(fields_to_ignore, query, con);
{indent}{indent}}}
{indent}}}
{indent}
{indent}@Override
{indent}public List<{name}> getByModel({name} {varname}, List<String> fields_to_ignore, Query query, Connection con) {{
{indent}{indent}logger.debug("{name}Repository.getByModel()");
{indent}{indent}
{indent}{indent}String sql = "select " + this.getSelectBase(fields_to_ignore) + "from {table_name} {initial} ";
{indent}{indent}sql += "where ";
{indent}{indent}
{bymodel_where}{indent}{indent}sql = sql.substring(0, sql.length() - 4);
{indent}{indent}
{indent}{indent}try {{
{indent}{indent}{indent}Sql2oUtility.setSqlToQuery(query, sql);
{indent}{indent}}}
{indent}{indent}catch (
{indent}{indent}{indent}NoSuchFieldException | 
{indent}{indent}{indent}IllegalArgumentException | 
{indent}{indent}{indent}IllegalAccessException e
{indent}{indent}) {{
{indent}{indent}{indent}throw new Sql2oException("Unable to set sql to query");
{indent}{indent}}}
{indent}{indent}
{bymodel_params}{indent}{indent}List<{name}> res = query.executeAndFetch({name}.class);
{indent}{indent}return res;
{indent}}}
{indent}
{indent}@Override
{indent}public List<{name}> getByModel({name} {varname}, List<String> fields_to_ignore) {{
{indent}{indent}try (Connection con = sql2o.open(); Query query = con.createQuery("")) {{
{indent}{indent}{indent}return this.getByModel({varname}, fields_to_ignore, query, con);
{indent}{indent}}}
{indent}}}
{indent}
{indent}@Override
{indent}public {name} insert({name} {varname}, Query query, Connection con) {{
{indent}{indent}logger.debug("{name}Repository.insert()");
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
{indent}{indent}try {{
{indent}{indent}{indent}Sql2oUtility.setSqlToQuery(query, sql);
{indent}{indent}}}
{indent}{indent}catch (
{indent}{indent}{indent}NoSuchFieldException | 
{indent}{indent}{indent}IllegalArgumentException | 
{indent}{indent}{indent}IllegalAccessException e
{indent}{indent}) {{
{indent}{indent}{indent}throw new Sql2oException("Unable to set sql to query");
{indent}{indent}}}
{indent}{indent}
{insert_params}
{indent}{indent}Object key = query.executeUpdate().getKey();
{indent}{indent}
{idkey}
{indent}{indent}
{indent}{indent}return {varname};
{indent}}}
{indent}
{indent}@Override
{indent}public {name} insert({name} {varname}) {{
{indent}{indent}try (Connection con = sql2o.beginTransaction(); Query query = con.createQuery("", true)) {{
{indent}{indent}{indent}{varname} = this.insert({varname}, query, con);
{indent}{indent}{indent}con.commit();
{indent}{indent}{indent}return {varname};
{indent}{indent}}}
{indent}}}
{indent}
{update}
{indent}@Override
{indent}public {name} save({name} {varname}, Query query, Connection con) {{
{idsinit}
{indent}{indent}{name} {varname}2 = this.getBy{methid}({idslist}, null, query, con);
{indent}{indent}
{indent}{indent}if ({varname}2 == null) {{
{indent}{indent}{indent}return this.insert({varname}, query, con);
{indent}{indent}}}
{indent}{indent}else {{
{save}
{indent}{indent}}}
{indent}}}
{indent}
{indent}@Override
{indent}public {name} save({name} {varname}) {{
{indent}{indent}try (Connection con = sql2o.beginTransaction(); Query query = con.createQuery("", true)) {{
{indent}{indent}{indent}{name} res = this.save({varname}, query, con);
{indent}{indent}{indent}con.commit();
{indent}{indent}{indent}return res;
{indent}{indent}}}
{indent}}}
{indent}
{indent}@Override
{indent}public void delete({idsfirm}, Query query, Connection con) {{
{indent}{indent}logger.debug("{name}Repository.delete() : {idslog});
{indent}{indent}
{indent}{indent}String sql = "delete from {table_name} ";
{idswhere}
{indent}{indent}
{indent}{indent}try {{
{indent}{indent}{indent}Sql2oUtility.setSqlToQuery(query, sql);
{indent}{indent}}}
{indent}{indent}catch (
{indent}{indent}{indent}NoSuchFieldException | 
{indent}{indent}{indent}IllegalArgumentException | 
{indent}{indent}{indent}IllegalAccessException e
{indent}{indent}) {{
{indent}{indent}{indent}throw new Sql2oException("Unable to set sql to query");
{indent}{indent}}}
{indent}{indent}
{idsparams}
{indent}{indent}query.executeUpdate();
{indent}}}
{indent}
{indent}@Override
{indent}public void delete({idsfirm}) {{
{indent}{indent}try (Connection con = sql2o.beginTransaction(); Query query = con.createQuery("")) {{
{indent}{indent}{indent}this.delete({idslist}, query, con);
{indent}{indent}{indent}con.commit();
{indent}{indent}}}
{indent}}}
{indent}
{indent}@Override
{indent}public void deleteByModel({name} {varname}, Query query, Connection con) {{
{indent}{indent}logger.debug("{name}Repository.deleteByModel()");
{indent}{indent}
{indent}{indent}String sql = "delete from {table_name} ";
{indent}{indent}sql += "where ";
{indent}{indent}
{bymodel_where}{indent}{indent}sql = sql.substring(0, sql.length() - 4);
{indent}{indent}
{indent}{indent}try {{
{indent}{indent}{indent}Sql2oUtility.setSqlToQuery(query, sql);
{indent}{indent}}}
{indent}{indent}catch (
{indent}{indent}{indent}NoSuchFieldException | 
{indent}{indent}{indent}IllegalArgumentException | 
{indent}{indent}{indent}IllegalAccessException e
{indent}{indent}) {{
{indent}{indent}{indent}throw new Sql2oException("Unable to set sql to query");
{indent}{indent}}}
{indent}{indent}
{bymodel_params}{indent}{indent}query.executeUpdate();
{indent}}}
{indent}
{indent}@Override
{indent}public void deleteByModel({name} {varname}) {{
{indent}{indent}try (Connection con = sql2o.beginTransaction(); Query query = con.createQuery("")) {{
{indent}{indent}{indent}this.deleteByModel({varname}, query, con);
{indent}{indent}{indent}con.commit();
{indent}{indent}}}
{indent}}}
}}

"""

save_tpl = """{indent}{indent}{indent}return this.update({varname}, false, query, con);
{indent}{indent}{indent}"""

idkey = "";

if not multiple_ids:
    idkey_mssql_tpl = "{indent}{indent}Object res = key;"

    idkey_oracle_tpl = """{indent}{indent}String sqlId = "SELECT {id0} FROM {table_name} WHERE rowid  = :key";
    {indent}{indent}Query queryid = con.createQuery(sqlId);
    {indent}{indent}queryid.addParameter("key", key);
    {indent}{indent}Object res = queryid.executeAndFetchFirst(Long.class);
    {indent}{indent}queryid.close();"""

    if dtype == "mssql":
        idkey = idkey_mssql_tpl.format(indent=indent)
    elif dtype == "oracle":
        idkey = idkey_oracle_tpl.format(
            indent = indent, 
            id0 = ids[0], 
            table_name = table_name
        )

    idkey_end_tpl = """
{indent}{indent}
{indent}{indent}Object res_true;
{indent}{indent}
{indent}{indent}if (res != null && res instanceof BigDecimal) {{
{indent}{indent}{indent}res_true = ((BigDecimal) res).longValue();
{indent}{indent}}}
{indent}{indent}else {{
{indent}{indent}{indent}res_true = res;
{indent}{indent}}}
{indent}{indent}
{indent}{indent}{varname}.set{methid}(({id_col_type}) res_true);"""

    idkey_end = idkey_end_tpl.format(
        indent = indent, 
        methid = methid, 
        varname = varname,
        id_col_type = id_col_type
    )
    
    idkey += idkey_end

update_tpl = """{indent}@Override
{indent}public {name} update({name} {varname}, boolean exclude_nulls, Query query, Connection con) {{
{indent}{indent}logger.debug("{name}Repository.update()");
{indent}{indent}
{indent}{indent}String sql = "update {table_name} set ";
{indent}{indent}
{update_fields}{indent}{indent}sql = sql.substring(0, sql.length() - 2) + " ";
{idswhere}
{indent}{indent}
{indent}{indent}try {{
{indent}{indent}{indent}Sql2oUtility.setSqlToQuery(query, sql);
{indent}{indent}}}
{indent}{indent}catch (
{indent}{indent}{indent}NoSuchFieldException | 
{indent}{indent}{indent}IllegalArgumentException | 
{indent}{indent}{indent}IllegalAccessException e
{indent}{indent}) {{
{indent}{indent}{indent}throw new Sql2oException("Unable to set sql to query");
{indent}{indent}}}
{indent}{indent}
{update_params}{indent}{indent}query.executeUpdate();
{indent}{indent}return {varname};
{indent}}}
{indent}
{indent}@Override
{indent}public {name} update({name} {varname}, boolean exclude_nulls) {{
{indent}{indent}try (Connection con = sql2o.beginTransaction(); Query query = con.createQuery("")) {{
{indent}{indent}{indent}{varname} = this.update({varname}, exclude_nulls, query, con);
{indent}{indent}{indent}con.commit();
{indent}{indent}{indent}return {varname};
{indent}{indent}}}
{indent}}}
{indent}"""



idsfirm = ""
idslog = ""
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
        methid = methid
    )
    
    idsparams += '{indent}{indent}query.addParameter("{varid}", {varid});\n'.format(indent=indent, varid=id.lower())
    
    idslist += "{}, ".format(varid)

idsfirm = idsfirm[:-2]
idslog = idslog[:-4]
idswhere = idswhere[:-8] + '";'
idslist = idslist[:-2]


imports = "import java.math.BigDecimal;\n"

import_date_eff = ""


if idshasdate:
    import_date_eff = import_date + "\n"
    imports += import_date_eff

if imports:
    imports = "\n" + imports
    


select_fields_tpl = '{indent}{indent}String res = "";'
select_fields_tpl += (
"""
{indent}{indent}
{indent}{indent}fields_to_ignore = fields_to_ignore
{indent}{indent}{indent}.stream()
{indent}{indent}{indent}.map(field -> field.toUpperCase())
{indent}{indent}{indent}.collect(Collectors.toList());
{indent}{indent}
""")
        
select_fields = select_fields_tpl.format(indent=indent)


insert_fields = ""
insert_vars = ""
insert_params = ""
update_params = ""
bymodel_params = ""
update_fields = ""
bymodel_where = ""

noupdate = True

last_col_i = len(col_types) - 1
last_col = False


    
insert_params = '{indent}{indent}query.bind({varname});\n'.format(
    varname = varname,
    indent = indent
)

for i, col in enumerate(col_types):
    if i == last_col_i:
        last_col = True
    else:
        last_col = False
    
    colname = col.lower()
    methcol = colname[0].upper() + colname[1:]
    
    select_field_tpl = '{indent}{indent}if (fields_to_ignore != null && ! fields_to_ignore.contains("{col}")) {{\n'
    select_field_tpl += '{indent}{indent}{indent}res += "{initial}.{col}, ";\n'
    
    select_field_tpl += '{indent}{indent}}}\n{indent}{indent}\n'
    select_field = select_field_tpl.format(indent=indent, initial=initial, col=col)
    select_fields += select_field
    
    insert_fields += indent + indent + indent + indent + '"{}, " + \n'.format(col)
    insert_vars += indent + indent + indent + indent + '":{}, " + \n'.format(col.lower())
    
    update_params += '''{indent}{indent}if (! exclude_nulls || {varname}.get{methcol}() != null) {{
{indent}{indent}{indent}query.addParameter("{colname}", {varname}.get{methcol}());
{indent}{indent}}}
{indent}{indent}
'''.format(
        colname = colname,
        varname = varname,
        methcol = methcol,
        indent = indent
    )
    
    bymodel_params += '''{indent}{indent}if ({varname}.get{methcol}() != null) {{
{indent}{indent}{indent}query.addParameter("{colname}", {varname}.get{methcol}());
{indent}{indent}}}
{indent}{indent}
'''.format(
        colname = colname,
        varname = varname,
        methcol = methcol,
        indent = indent
    )
    
    noupdate = False

    bymodel_where += '''{indent}{indent}if ({varname}.get{methcol}() != null) {{ 
{indent}{indent}{indent} sql += "{col} = :{colname} and ";
{indent}{indent}}}
{indent}{indent}
'''.format(
    col=col, 
    colname=colname, 
    indent=indent, 
    varname=varname, 
    methcol=methcol
)
    
    if col not in ids:
        noupdate = False
        
        update_fields += '''{indent}{indent}if (! exclude_nulls || {varname}.get{methcol}() != null) {{ 
{indent}{indent}{indent} sql += "{col} = :{colname}, ";
{indent}{indent}}}
{indent}{indent}
'''.format(
    col=col, 
    colname=colname, 
    indent=indent, 
    varname=varname, 
    methcol=methcol
)

select_fields += """{indent}{indent}res = res.substring(0, res.length() - 2);
{indent}{indent}\n""".format(indent = indent)
insert_fields = insert_fields[:-7] + ' " + '
insert_vars = insert_vars[:-7] + ' " + '


if noupdate:
    update = ""
    save_tpl = "{indent}{indent}{indent}return null;"
    save = save_tpl.format(
        indent = indent
    )
else:
    update = update_tpl.format(
        indent = indent, 
        idswhere = idswhere, 
        name = class_name, 
        table_name = table_name, 
        update_fields = update_fields, 
        varname = varname, 
        update_params = update_params
    )
    
    save = save_tpl.format(
        indent = indent, 
        varname = varname
    )

repo_res = repo.format(
    indent = indent, 
    imports = imports, 
    name = class_name, 
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
    update_params = update_params,
    bymodel_params = bymodel_params,
    update_fields = update_fields,
    bymodel_where = bymodel_where,
    initial = initial,
    pack_model = pack_model,
    pack_utility = pack_utility,
    pack_repo = pack_repo,
    update = update,
    save = save,
    idkey = idkey,
)

repo_dir = data_dir / pack_repo.replace(".", "/")
msutils.mkdirP(str(repo_dir))
repo_path = repo_dir / (class_name + "RepositoryImpl.java")

with open(str(repo_path), mode="w+") as f:
    f.write(repo_res)


repoint = """package {pack_repo};
{imports}
import java.util.List;

import org.sql2o.Connection;
import org.sql2o.Query;

import {pack_model}.{class_name};

public interface {class_name}Repository {{
{indent}{class_name} getBy{methid}({idsfirm}, List<String> fields_to_ignore, Query query, Connection con);
{indent}
{indent}{class_name} getBy{methid}({idsfirm}, List<String> fields_to_ignore);
{indent}
{indent}{class_name} insert({class_name} {varname}, Query query, Connection con);
{indent}
{indent}{class_name} insert({class_name} {varname});
{update}
{indent}
{indent}{class_name} save({class_name} {varname}, Query query, Connection con);
{indent}
{indent}{class_name} save({class_name} {varname});
{indent}
{indent}List<{class_name}> getAll(List<String> fields_to_ignore, Query query, Connection con);
{indent}
{indent}List<{class_name}> getAll(List<String> fields_to_ignore);
{indent}
{indent}List<{class_name}> getByModel({class_name} {varname}, List<String> fields_to_ignore, Query query, Connection con);
{indent}
{indent}List<{class_name}> getByModel({class_name} {varname}, List<String> fields_to_ignore);
{indent}
{indent}void delete({idsfirm}, Query query, Connection con);
{indent}
{indent}void delete({idsfirm});
{indent}
{indent}void deleteByModel({class_name} {varname}, Query query, Connection con);
{indent}
{indent}void deleteByModel({class_name} {varname});
}}

"""

update_tpl = """{indent}
{indent}{class_name} update({class_name} {varname}, boolean exclude_nulls, Query query, Connection con);
{indent}
{indent}{class_name} update({class_name} {varname}, boolean exclude_nulls);"""

if noupdate:
    update = ""
else:
    update = update_tpl.format(indent=indent, class_name=class_name, varname=varname)

imports = ""

if import_date_eff:
    imports = "\n" + import_date_eff + "\n"

repoint_res = repoint.format(
    imports = imports,
    class_name = class_name,
    varname = varname,
    methid = methid,
    indent = indent,
    idsfirm = idsfirm,
    pack_repo = pack_repo,
    pack_model = pack_model,
    update = update
)

repoint_path = repo_dir / (class_name + "Repository.java")

with open(str(repoint_path), mode="w+") as f:
    f.write(repoint_res)


service = """package {pack_service};
{imports}
import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.sql2o.Connection;
import org.sql2o.Query;

import {pack_model}.{class_name};
import {pack_repo}.{class_name}Repository;


@Service
public class {class_name}ServiceImpl implements {class_name}Service {{
{indent}@Autowired
{indent}private {class_name}Repository {varname}Repository;
{indent}
{indent}private void enrich({class_name} {varname}) {{
{indent}{indent}if ({varname} != null) {{
{indent}{indent}{indent} // TODO add implementation
{indent}{indent}}}
{indent}}}
{indent}
{indent}private void enrich(List<{class_name}> {varname}s) {{
{indent}{indent}if ({varname}s != null) {{
{indent}{indent}{indent}for ({class_name} {varname}: {varname}s) {{
{indent}{indent}{indent}{indent}this.enrich({varname});
{indent}{indent}{indent}}}
{indent}{indent}}}
{indent}}}
{indent}
{indent}@Override
{indent}public List<{class_name}> getAll(List<String> fields_to_ignore, Query query, Connection con) {{
{indent}{indent}List<{class_name}> {varname}s = {varname}Repository.getAll(fields_to_ignore, query, con);
{indent}{indent}
{indent}{indent}this.enrich({varname}s);
{indent}{indent}
{indent}{indent}return {varname}s;
{indent}}}
{indent}
{indent}@Override
{indent}public List<{class_name}> getAll(List<String> fields_to_ignore) {{
{indent}{indent}List<{class_name}> {varname}s = {varname}Repository.getAll(fields_to_ignore);
{indent}{indent}
{indent}{indent}this.enrich({varname}s);
{indent}{indent}
{indent}{indent}return {varname}s;
{indent}}}
{indent}
{indent}@Override
{indent}public List<{class_name}> getByModel({class_name} {varname}, List<String> fields_to_ignore, Query query, Connection con) {{
{indent}{indent}List<{class_name}> {varname}s = {varname}Repository.getByModel({varname}, fields_to_ignore, query, con);
{indent}{indent}
{indent}{indent}this.enrich({varname}s);
{indent}{indent}
{indent}{indent}return {varname}s;
{indent}}}
{indent}
{indent}@Override
{indent}public List<{class_name}> getByModel({class_name} {varname}, List<String> fields_to_ignore) {{
{indent}{indent}List<{class_name}> {varname}s = {varname}Repository.getByModel({varname}, fields_to_ignore);
{indent}{indent}
{indent}{indent}this.enrich({varname}s);
{indent}{indent}
{indent}{indent}return {varname}s;
{indent}}}
{indent}
{indent}@Override
{indent}public {class_name} getBy{methid}({idsfirm}, List<String> fields_to_ignore, Query query, Connection con) {{
{indent}{indent}{class_name} {varname} = {varname}Repository.getBy{methid}({idslist}, fields_to_ignore, query, con);
{indent}{indent}
{indent}{indent}this.enrich({varname});
{indent}{indent}
{indent}{indent}return {varname};
{indent}}}
{indent}
{indent}@Override
{indent}public {class_name} getBy{methid}({idsfirm}, List<String> fields_to_ignore) {{
{indent}{indent}{class_name} {varname} = {varname}Repository.getBy{methid}({idslist}, fields_to_ignore);
{indent}{indent}
{indent}{indent}this.enrich({varname});
{indent}{indent}
{indent}{indent}return {varname};
{indent}}}
{indent}
{indent}@Override
{indent}public {class_name} insert({class_name} {varname}, Query query, Connection con) {{
{indent}{indent}return {varname}Repository.insert({varname}, query, con);
{indent}}}
{indent}
{indent}@Override
{indent}public {class_name} insert({class_name} {varname}) {{
{indent}{indent}return {varname}Repository.insert({varname});
{indent}}}
{update}
{indent}
{indent}@Override
{indent}public {class_name} save({class_name} {varname}, Query query, Connection con) {{
{indent}{indent}return {varname}Repository.save({varname}, query, con);
{indent}}}
{indent}
{indent}@Override
{indent}public {class_name} save({class_name} {varname}) {{
{indent}{indent}return {varname}Repository.save({varname});
{indent}}}
{indent}
{indent}@Override
{indent}public void delete({idsfirm}, Query query, Connection con) {{
{indent}{indent}{varname}Repository.delete({idslist}, query, con);
{indent}}}
{indent}
{indent}@Override
{indent}public void delete({idsfirm}) {{
{indent}{indent}{varname}Repository.delete({idslist});
{indent}}}
{indent}
{indent}@Override
{indent}public void deleteByModel({class_name} {varname}, Query query, Connection con) {{
{indent}{indent}{varname}Repository.deleteByModel({varname}, query, con);
{indent}}}
{indent}
{indent}@Override
{indent}public void deleteByModel({class_name} {varname}) {{
{indent}{indent}{varname}Repository.deleteByModel({varname});
{indent}}}
}}

"""

update_tpl = """
{indent}
{indent}@Override
{indent}public {class_name} update({class_name} {varname}, boolean exclude_nulls, Query query, Connection con) {{
{indent}{indent}return {varname}Repository.update({varname}, exclude_nulls, query, con);
{indent}}}
{indent}
{indent}@Override
{indent}public {class_name} update({class_name} {varname}, boolean exclude_nulls) {{
{indent}{indent}return {varname}Repository.update({varname}, exclude_nulls);
{indent}}}"""

if noupdate:
    update = ""
else:
    update = update_tpl.format(indent=indent, class_name=class_name, varname=varname)

service_res = service.format(
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
    update = update
)

service_dir = data_dir / pack_service.replace(".", "/")
msutils.mkdirP(str(service_dir))
service_path = service_dir / (class_name + "ServiceImpl.java")

with open(str(service_path), mode="w+") as f:
    f.write(service_res)


serviceint = """package {pack_service};
{imports}
import java.util.List;

import org.sql2o.Connection;
import org.sql2o.Query;

import {pack_model}.{class_name};

public interface {class_name}Service {{
{indent}{class_name} getBy{methid}({idsfirm}, List<String> fields_to_ignore, Query query, Connection con);
{indent}
{indent}{class_name} getBy{methid}({idsfirm}, List<String> fields_to_ignore);
{indent}
{indent}{class_name} insert({class_name} {varname}, Query query, Connection con);
{indent}
{indent}{class_name} insert({class_name} {varname});
{update}
{indent}
{indent}{class_name} save({class_name} {varname}, Query query, Connection con);
{indent}
{indent}{class_name} save({class_name} {varname});
{indent}
{indent}List<{class_name}> getAll(List<String> fields_to_ignore, Query query, Connection con);
{indent}
{indent}List<{class_name}> getAll(List<String> fields_to_ignore);
{indent}
{indent}List<{class_name}> getByModel({class_name} {varname}, List<String> fields_to_ignore, Query query, Connection con);
{indent}
{indent}List<{class_name}> getByModel({class_name} {varname}, List<String> fields_to_ignore);
{indent}
{indent}void delete({idsfirm}, Query query, Connection con);
{indent}
{indent}void delete({idsfirm});
{indent}
{indent}void deleteByModel({class_name} {varname}, Query query, Connection con);
{indent}
{indent}void deleteByModel({class_name} {varname});
}}

"""

update_tpl = """{indent}
{indent}{class_name} update({class_name} {varname}, boolean exclude_nulls, Query query, Connection con);
{indent}
{indent}{class_name} update({class_name} {varname}, boolean exclude_nulls);"""

if noupdate:
    update = ""
else:
    update = update_tpl.format(indent=indent, class_name=class_name, varname=varname)


serviceint_res = serviceint.format(
    imports = imports,
    class_name = class_name,
    varname = varname,
    methid = methid,
    idsfirm = idsfirm,
    indent = indent,
    pack_service = pack_service,
    pack_model = pack_model,
    update = update
)

serviceint_path = service_dir / (class_name + "Service.java")

with open(str(serviceint_path), mode="w+") as f:
    f.write(serviceint_res)


print("Files saved in " + str(data_dir))
print(
"""

!!!IMPORTANT!!! 

* Please check the insert and update methods in repo, in particular for""" + 
"""autoincrement columns as parameter that does not accept value in insert.

* Remove also in update fields that should never be updated, like createdby or createdon.
"""
)

