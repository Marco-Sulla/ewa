import sqlalchemy.engine
import lib.msutils as msutils
import configparser
from pathlib import Path
import os
import argparse
import configparser

try:
    app_dir = Path(__file__).resolve().parent
except NameError:
    app_dir = Path(".")


app_descr = "Java code generator"
help_config = "Set the config file to be read"

cmd_parser = argparse.ArgumentParser(description=app_descr)
cmd_parser.add_argument("--config", required=True, help=help_config)

cmd_args = cmd_parser.parse_args()
cmd_dict = vars(cmd_args)


config_path_tpm = cmd_dict["config"]
config_path = msutils.toAbsPath(config_path_tpm, app_dir)
config = configparser.ConfigParser()
config.read(str(config_path))

class_name = config.get("default", "class_name") # TODO support multiple
table_name = config.get("default", "table_name").upper()
ids = config.get("default", "ids").upper()
tid = ids # TODO support multiple
integer_instead_of_short = bool(int(config.get("default", "integer_instead_of_short")))
bigdecimal_instead_of_double = bool(int(config.get("default", "bigdecimal_instead_of_double")))
biginteger_instead_of_long = bool(int(config.get("default", "biginteger_instead_of_long")))

dtype = config.get("database", "type")
user = config.get("database", "user")
password = config.get("database", "password")
host = config.get("database", "host")
port = int(config.get("database", "port"))
db_name = config.get("database", "name")

pack_model = config.get("packages", "model")
pack_repo = config.get("packages", "repository")
pack_service = config.get("packages", "service")

def convertMsSqlToJavaType(
    sql_type, 
    prec, 
    radix, 
    scale, 
    use_bigdecimal_instead_of_double, 
    use_biginteger_instead_of_long
):
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
    elif sql_type == "datetime2":
        return "Date"
    elif sql_type == "varchar":
        return "String"
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

db_str = msutils.dbString(dtype, user, password, host, port, db_name)

engine = sqlalchemy.engine.create_engine(db_str, echo=False)

get_columns_data_sql_mssql = """SELECT 
    column_name, 
    data_type, 
    numeric_precision, 
    numeric_precision_radix,
    numeric_scale
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = N'{}'"""

rows = engine.execute(get_columns_data_sql_mssql.format(table_name))

fields = ""
methods = ""
bigdecimal = False
biginteger = False
col_types = {}
import_date_eff = ""

for row in rows:
    col = row[0].upper()
    ctype = row[1]
    prec = row[2]
    radix = row[3]
    scale = row[4]
    jtype = convertMsSqlToJavaType(
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

res += class_start.format(imports=imports, class_name=class_name, pack_model=pack_model) + "\n"
res += fields + "\n\n" + methods.rstrip() + "\n" + class_end

data_dir = app_dir / "data" / class_name
model_dir = data_dir / pack_model.replace(".", "/")

msutils.mkdirP(str(model_dir))

model_path = model_dir / (class_name + ".java")

with open(str(model_path), mode="w+") as f:
    f.write(res)




repo = """package {pack_repo};

{imports}

import java.util.List;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Repository;
import org.sql2o.Connection;
import org.sql2o.Query;
import org.sql2o.Sql2o;

import {pack_model}.{name};

@Repository
public class {name}RepositoryImpl implements {name}Repository {{
{indent}private final Logger logger = LoggerFactory.getLogger(this.getClass());
{indent}
{indent}private final String selectBase = (
{indent}{indent}"select " + 
{select_fields}
{indent});
{indent}
{indent}@Autowired
{indent}private Sql2o sql2o;
{indent}
{indent}@Override
{indent}public {name} getBy{methid}({idtype} {varid}) {{
{indent}{indent}logger.debug("{name}Repository.getBy{methid}(): " + {varid});
{indent}{indent}
{indent}{indent}String sql = selectBase + "from {table_name} {initial} where {tid} = :{varid}";
{indent}{indent}Query query = null;
{indent}{indent}
{indent}{indent}try (Connection con = sql2o.open()) {{
{indent}{indent}{indent}query = con.createQuery(sql);
{indent}{indent}{indent}query.addParameter("{varid}", {varid});
{indent}{indent}{indent}return query.executeAndFetchFirst({name}.class);
{indent}{indent}}}
{indent}{indent}finally {{
{indent}{indent}{indent}if (query != null) {{
{indent}{indent}{indent}{indent}query.close();
{indent}{indent}{indent}}}
{indent}{indent}}}
{indent}}}
{indent}
{indent}@Override
{indent}public List<{name}> getAll() {{
{indent}{indent}logger.debug("{name}Repository.getAll()");
{indent}{indent}
{indent}{indent}String sql = selectBase + "from {table_name} {initial} ";
{indent}{indent}Query query = null;
{indent}{indent}
{indent}{indent}try (Connection con = sql2o.open()) {{
{indent}{indent}{indent}query = con.createQuery(sql);
{indent}{indent}{indent}return query.executeAndFetch({name}.class);
{indent}{indent}}}
{indent}{indent}finally {{
{indent}{indent}{indent}if (query != null) {{
{indent}{indent}{indent}{indent}query.close();
{indent}{indent}{indent}}}
{indent}{indent}}}
{indent}}}
{indent}
{indent}@Override
{indent}public Long insert({name} {varname}) {{
{indent}{indent}logger.debug("{name}Repository.insert()");
{indent}{indent}String sql = (
{indent}{indent}{indent}"insert into {table_name} ( " + 
{insert_fields}
{indent}{indent}{indent}") " + 
{indent}{indent}{indent}"values (" +
{insert_vars}
{indent}{indent}{indent}")"
{indent}{indent});
{indent}{indent}
{indent}{indent}Query query = null;
{indent}{indent}
{indent}{indent}try (Connection con = sql2o.beginTransaction()) {{
{indent}{indent}{indent}query = con.createQuery(sql);
{insert_params}
{indent}{indent}{indent}BigDecimal res = (BigDecimal) query.executeUpdate().getKey();
{indent}{indent}{indent}con.commit();
{indent}{indent}{indent}return res.longValue();
{indent}{indent}}}
{indent}{indent}finally {{
{indent}{indent}{indent}if (query != null) {{
{indent}{indent}{indent}{indent}query.close();
{indent}{indent}{indent}}}
{indent}{indent}}}
{indent}}}
{indent}
{indent}@Override
{indent}public void update({name} {varname}) {{
{indent}{indent}logger.debug("{name}Repository.update()");
{indent}{indent}String sql = (
{indent}{indent}{indent}"update {table_name} set " + 
{update_fields}
{indent}{indent}{indent}"where {tid} = :{varid} " 
{indent}{indent});
{indent}{indent}
{indent}{indent}Query query = null;
{indent}{indent}
{indent}{indent}try (Connection con = sql2o.beginTransaction()) {{
{indent}{indent}{indent}query = con.createQuery(sql);
{update_params}
{indent}{indent}{indent}query.executeUpdate();
{indent}{indent}{indent}con.commit();
{indent}{indent}}}
{indent}{indent}finally {{
{indent}{indent}{indent}if (query != null) {{
{indent}{indent}{indent}{indent}query.close();
{indent}{indent}{indent}}}
{indent}{indent}}}
{indent}}}
{indent}
{indent}@Override
{indent}public Long save({name} {varname}) {{
{indent}{indent}{name} {varname}2 = this.getBy{methid}({varname}.get{methid}());
{indent}{indent}
{indent}{indent}if ({varname}2 == null) {{
{indent}{indent}{indent}return this.insert({varname});
{indent}{indent}}}
{indent}{indent}else {{
{indent}{indent}{indent}this.update({varname});
{indent}{indent}{indent}
{indent}{indent}{indent}return {varname}2.get{methid}();
{indent}{indent}}}
{indent}}}
{indent}
{indent}@Override
{indent}public void delete({idtype} {varid}) {{
{indent}{indent}logger.debug("{name}Repository.delete() {varid}: " + {varid});
{indent}{indent}String sql = (
{indent}{indent}{indent}"delete from {table_name} " + 
{indent}{indent}{indent}"where {tid} = :{varid} " 
{indent}{indent});
{indent}{indent}
{indent}{indent}Query query = null;
{indent}{indent}
{indent}{indent}try (Connection con = sql2o.beginTransaction()) {{
{indent}{indent}{indent}query = con.createQuery(sql);
{indent}{indent}{indent}query.addParameter("{varid}", {varid});
{indent}{indent}{indent}query.executeUpdate();
{indent}{indent}{indent}con.commit();
{indent}{indent}}}
{indent}{indent}finally {{
{indent}{indent}{indent}if (query != null) {{
{indent}{indent}{indent}{indent}query.close();
{indent}{indent}{indent}}}
{indent}{indent}}}
{indent}}}
}}

"""

varname = class_name[0].lower() + class_name[1:]
initial = varname[0]
varid = tid.lower()
methid = varid[0].upper() + varid[1:]
idtype = col_types[tid]
imports = "import java.math.BigDecimal;"

import_date_eff = ""

if idtype == "Date":
    import_date_eff = import_date + "\n"

select_fields = ""
insert_fields = ""
insert_vars = ""
insert_params = ""
update_fields = ""

for col in col_types:
    colname = col.lower()
    methcol = colname[0].upper() + colname[1:]
    
    select_fields += indent + indent + indent + '"{}.{}, " + \n'.format(initial, col)
    insert_fields += indent + indent + indent + indent + '"{}, " + \n'.format(col)
    insert_vars += indent + indent + indent + indent + '":{}, " + \n'.format(col.lower())
    
    insert_params += (
        indent + indent + indent + 
        'query.addParameter("{colname}", {varname}.get{methcol}());\n'.format(
            colname = colname,
            varname = varname,
            methcol = methcol
        )
    )
    
    update_fields += (
        indent + indent + indent + indent + 
        '"{col} = :{colname}, " +\n'.format(col=col, colname=colname)
    )

select_fields = select_fields[:-7] + ' "'
insert_fields = insert_fields[:-7] + ' " + '
insert_vars = insert_vars[:-7] + ' " + '
update_fields = update_fields[:-6] + ' " + '


repo_res = repo.format(
    indent = indent, 
    imports = imports + import_date_eff, 
    name = class_name, 
    methid = methid, 
    idtype = idtype,
    varid = varid,
    table_name = table_name,
    tid = tid,
    varname = varname,
    select_fields = select_fields,
    insert_fields = insert_fields,
    insert_vars = insert_vars,
    insert_params = insert_params,
    update_params = insert_params,
    update_fields = update_fields,
    initial = initial,
    pack_model = pack_model,
    pack_repo = pack_repo
)

repo_dir = data_dir / pack_repo.replace(".", "/")
msutils.mkdirP(str(repo_dir))
repo_path = repo_dir / (class_name + "RepositoryImpl.java")

with open(str(repo_path), mode="w+") as f:
    f.write(repo_res)


repoint = """package {pack_repo};

{imports}

import java.util.List;

import {pack_model}.{class_name};

public interface {class_name}Repository {{

{indent}{class_name} getBy{methid}({idtype} {varid});
{indent}
{indent}Long insert({class_name} {varname});
{indent}
{indent}void update({class_name} {varname});
{indent}
{indent}Long save({class_name} {varname});
{indent}
{indent}List<{class_name}> getAll();
{indent}
{indent}void delete({idtype} {varid});
}}

"""

repoint_res = repoint.format(
    imports = import_date_eff,
    class_name = class_name,
    varname = varname,
    methid = methid,
    varid = varid,
    indent = indent,
    idtype = idtype,
    pack_repo = pack_repo,
    pack_model = pack_model
)

repoint_path = repo_dir / (class_name + "Repository.java")

with open(str(repoint_path), mode="w+") as f:
    f.write(repoint_res)


service = """package {pack_service};

{imports}

import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import {pack_model}.{class_name};
import {pack_repo}.{class_name}Repository;


@Service
public class {class_name}ServiceImpl implements {class_name}Service {{
{indent}@Autowired
{indent}private {class_name}Repository {varname}Repository;
{indent}
{indent}@Override
{indent}public List<{class_name}> getAll() {{
{indent}{indent}return {varname}Repository.getAll();
{indent}}}
{indent}
{indent}@Override
{indent}public {class_name} getBy{methid}({idtype} {varid}) {{
{indent}{indent}return {varname}Repository.getBy{methid}({varid});
{indent}}}
{indent}
{indent}@Override
{indent}public Long insert({class_name} {varname}) {{
{indent}{indent}return {varname}Repository.insert({varname});
{indent}}}
{indent}
{indent}@Override
{indent}public void update({class_name} {varname}) {{
{indent}{indent}{varname}Repository.update({varname});
{indent}}}
{indent}
{indent}@Override
{indent}public Long save({class_name} {varname}) {{
{indent}{indent}return {varname}Repository.save({varname});
{indent}}}
{indent}
{indent}@Override
{indent}public void delete({idtype} {varid}) {{
{indent}{indent}{varname}Repository.delete({varid});
{indent}}}
}}

"""

service_res = service.format(
    imports = import_date_eff,
    class_name = class_name,
    varname = varname,
    methid = methid,
    varid = varid,
    indent = indent,
    idtype = idtype,
    pack_model = pack_model,
    pack_repo = pack_repo,
    pack_service = pack_service
)

service_dir = data_dir / pack_service.replace(".", "/")
msutils.mkdirP(str(service_dir))
service_path = service_dir / (class_name + "ServiceImpl.java")

with open(str(service_path), mode="w+") as f:
    f.write(service_res)


serviceint = """package {pack_service};

{imports}

import java.util.List;

import {pack_model}.{class_name};

public interface {class_name}Service {{
{indent}
{indent}{class_name} getBy{methid}({idtype} {varid});
{indent}
{indent}Long insert({class_name} {varname});
{indent}
{indent}void update({class_name} {varname});
{indent}
{indent}Long save({class_name} {varname});
{indent}
{indent}List<{class_name}> getAll();
{indent}
{indent}void delete({idtype} {varid});
}}

"""

serviceint_res = serviceint.format(
    imports = import_date_eff,
    class_name = class_name,
    varname = varname,
    methid = methid,
    varid = varid,
    indent = indent,
    idtype = idtype,
    pack_service = pack_service,
    pack_model = pack_model
)

serviceint_path = service_dir / (class_name + "Service.java")

with open(str(serviceint_path), mode="w+") as f:
    f.write(serviceint_res)


print("Files saved in " + str(data_dir))
print(
    "!!!IMPORTANT!!! Please check the insert and update methods in repo, " + 
    "in particular for id as parameter"
)

