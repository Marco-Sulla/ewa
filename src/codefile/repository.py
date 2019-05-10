import utility.util as util

repo_tpl = (
"""{firm}

package {pack_repo};

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
{indent}private final static Logger logger = LoggerFactory.getLogger({class_name}Repository.class);
{indent}
{indent}@Autowired
{indent}private Sql2o sql2o;
{indent}
{indent}private static String getSelectBase(List<String> fields_to_ignore) {{
{select_fields}
{indent}{indent}return res;
{indent}}}
{indent}
{indent}@Override
{indent}public {class_name} {select_methods_prefix}By{methid}({idsfirm}, List<String> fields_to_ignore, Connection con) {{
{indent}{indent}logger.debug("DB>> {select_methods_prefix}By{methid}() - {idslog});
{indent}{indent}
{indent}{indent}String sql = "select " + {class_name}RepositoryImpl.getSelectBase(fields_to_ignore) + "from {table_name} {initial} ";
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
{indent}{indent}String sql = "select " + {class_name}RepositoryImpl.getSelectBase(fields_to_ignore) + "from {table_name} {initial} ";
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
{indent}{indent}String sql = "select " + {class_name}RepositoryImpl.getSelectBase(fields_to_ignore) + "from {table_name} {initial} ";
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
{save}
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

save_update_tpl = """{indent}{indent}return this.update({varname}, false, con);"""

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

idkey_mssql_tpl = "{indent}{indent}Object res = key;"

idkey_oracle_tpl = """{indent}{indent}Object res = Sql2oUtility.getInsertedId("{table_name}", "{id0}", con, key, {id_col_type}.class);"""

select_fields_tpl = (
"""{indent}{indent}String res = "";
{indent}{indent}
{indent}{indent}fields_to_ignore = fields_to_ignore
{indent}{indent}{indent}.stream()
{indent}{indent}{indent}.map(field -> field.toUpperCase())
{indent}{indent}{indent}.collect(Collectors.toList());
{indent}{indent}
"""
)

select_field_col_tpl = (
"""{indent}{indent}if (fields_to_ignore != null && ! fields_to_ignore.contains("{col}")) {{
{indent}{indent}{indent}res += "{initial}.{col}, ";
{indent}{indent}}}
{indent}{indent}
"""
)

update_params_col_tpl = (
"""{indent}{indent}{indent}if (! exclude_nulls || {varname}.get{methcol}() != null) {{
{indent}{indent}{indent}{indent}query.addParameter("{colname}", {varname}.get{methcol}());
{indent}{indent}{indent}}}
{indent}{indent}{indent}
"""
)

bymodel_params_col_tpl = (
"""{indent}{indent}{indent}if ({varname}.get{methcol}() != null) {{
{indent}{indent}{indent}{indent}query.addParameter("{colname}", {varname}.get{methcol}());
{indent}{indent}{indent}}}
{indent}{indent}{indent}
"""
)

bymodel_where_col_tpl = (
"""{indent}{indent}if ({varname}.get{methcol}() != null) {{ 
{indent}{indent}{indent} sql += "{col} = :{colname} and ";
{indent}{indent}}}
{indent}{indent}
"""
)

update_fields_col_tpl = (
"""{indent}{indent}if (! exclude_nulls || {varname}.get{methcol}() != null) {{ 
{indent}{indent}{indent} sql += "{col} = :{colname}, ";
{indent}{indent}}}
{indent}{indent}
"""
)

select_fields_end_tpl = (
"""{indent}{indent}res = res.substring(0, res.length() - 2);
{indent}{indent}"""
)

save_update_null_tpl = "{indent}{indent}return null;"
idslog_col_tpl = '{varid}: " + {varid} + "'
idslog_update_col_tpl = '{varid}: " + {varname}.get{methid}() + "'
idswhere_col_tpl = '{indent}{indent}sql += "{id} = :{varid} and "; \n'
idsinit_col_tpl = '{indent}{indent}{col_type} {varid} = {varname}.get{methid}();\n'
idsparams_col_tpl = '{indent}{indent}{indent}query.addParameter("{varid}", {varid});\n'
insert_params_tpl = '{indent}{indent}{indent}query.bind({varname});\n'
insert_fields_col_tpl = '{indent}{indent}{indent}{indent}"{col}, " + \n'
insert_vars_col_tpl = '{indent}{indent}{indent}{indent}":{col}, " + \n'
idswhere_init_tpl = '{indent}{indent}sql += "where "; \n'


def write(config):
    idkey = ""
    
    if not config.multiple_ids:
        if config.dtype == "mssql":
            idkey = idkey_mssql_tpl.format(indent=config.indent)
        elif config.dtype == "oracle":
            idkey = idkey_oracle_tpl.format(
                indent=config.indent,
                id0=config.ids[0],
                table_name=config.table_name,
                id_col_type=config.id_col_type,
            )
        
        idkey_end = idkey_end_tpl.format(
            indent=config.indent,
            methid=config.methid,
            varname=config.varname,
            id_col_type=config.id_col_type
        )
        
        idkey += idkey_end
    
    idslog = ""
    idslog_update = ""
    idswhere = idswhere_init_tpl.format(indent=config.indent)
    idsinit = ""
    idsparams = ""
    
    for id in config.ids:
        col_type = config.col_types[id]
        varid = id.lower()
        methid = id[0] + id[1:].lower()

        idslog += idslog_col_tpl.format(varid=varid)
        
        idslog_update += idslog_update_col_tpl.format(
            varid=varid,
            varname=config.varname,
            methid=methid,
        )
        
        idswhere += idswhere_col_tpl.format(
            indent=config.indent,
            id=id,
            varid=varid
        )
        
        idsinit += idsinit_col_tpl.format(
            indent=config.indent,
            col_type=col_type,
            varid=varid,
            varname=config.varname,
            methid=methid,
            select_methods_prefix=config.select_methods_prefix,
        )
        
        idsparams += idsparams_col_tpl.format(
            indent=config.indent,
            varid=id.lower(),
        )

    idslog = idslog[:-4]
    idslog_update = idslog_update[:-4]
    idswhere = idswhere[:-8] + '";'
    
    select_fields = select_fields_tpl.format(indent=config.indent)
    
    update_params = ""
    bymodel_params = ""
    update_fields = ""
    bymodel_where = ""
    select_field_body = ""
    insert_fields = ""
    insert_vars = ""
    
    insert_params = insert_params_tpl.format(
        varname=config.varname,
        indent=config.indent
    )
    
    for i, col in enumerate(config.col_types):
        colname = col.lower()
        methcol = colname[0].upper() + colname[1:]

        select_field_body += select_field_col_tpl.format(
            indent=config.indent,
            initial=config.initial,
            col=col,
        )

        insert_fields += insert_fields_col_tpl.format(col=col, indent=config.indent)
        insert_vars += insert_vars_col_tpl.format(col=col.lower(), indent=config.indent)
        
        update_params += update_params_col_tpl.format(
            colname=colname,
            varname=config.varname,
            methcol=methcol,
            indent=config.indent,
            select_methods_prefix=config.select_methods_prefix,
        )
        
        bymodel_params += bymodel_params_col_tpl.format(
            colname=colname,
            varname=config.varname,
            methcol=methcol,
            indent=config.indent,
            select_methods_prefix=config.select_methods_prefix,
        )
        
        bymodel_where += bymodel_where_col_tpl.format(
            col=col,
            colname=colname,
            indent=config.indent,
            varname=config.varname,
            methcol=methcol,
            select_methods_prefix=config.select_methods_prefix,
        )
        
        if col not in config.ids:
            update_fields += update_fields_col_tpl.format(
                col=col,
                colname=colname,
                indent=config.indent,
                varname=config.varname,
                methcol=methcol,
                select_methods_prefix=config.select_methods_prefix,
            )
    
    select_fields += select_field_body
    select_fields_end = select_fields_end_tpl.format(indent=config.indent)
    select_fields += select_fields_end
    
    insert_fields = insert_fields[:-7] + ' " + '
    insert_vars = insert_vars[:-7] + ' " + '
    bymodel_params = bymodel_params[:-1]
    bymodel_where = bymodel_where[:-1]
    update_fields = update_fields[:-1]
    
    if config.noupdate:
        update = ""
        save = save_update_null_tpl.format(indent=config.indent)
    else:
        update = update_tpl.format(
            indent=config.indent,
            idswhere=idswhere,
            class_name=config.class_name,
            table_name=config.table_name,
            update_fields=update_fields,
            varname=config.varname,
            update_params=update_params,
            idslog_update=idslog_update,
        )
        
        save = save_update_tpl.format(
            indent=config.indent,
            varname=config.varname
        )
    
    repo = repo_tpl.format(
        indent=config.indent,
        class_name=config.class_name,
        methid=config.methid,
        idsfirm=config.idsfirm,
        idslog=idslog,
        idswhere=idswhere,
        idsparams=idsparams,
        idsinit=idsinit,
        idslist=config.idslist,
        table_name=config.table_name,
        varname=config.varname,
        select_fields=select_fields,
        insert_fields=insert_fields,
        insert_vars=insert_vars,
        insert_params=insert_params,
        bymodel_params=bymodel_params,
        bymodel_where=bymodel_where,
        initial=config.initial,
        pack_model=config.pack_model,
        pack_utility=config.pack_utility,
        pack_repo=config.pack_repo,
        update=update,
        save=save,
        idkey=idkey,
        select_methods_prefix=config.select_methods_prefix,
        firm=config.firm,
    )
    
    util.writeToFile(config.data_dir, config.pack_repo, config.class_name + "RepositoryImpl.java", repo)
