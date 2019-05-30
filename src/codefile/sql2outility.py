import utility.util as util

sql2outility_tpl = (
"""{firm_donottouch}

package {pack_utility};

import java.math.BigDecimal;
import java.util.NoSuchElementException;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.sql2o.Connection;
import org.sql2o.Query;

import {pack_enum}.DatasourceTypeEnum;


@Component
public class Sql2oUtility {{
{indent}private static String datasource_type;
{indent}
{indent}@SuppressWarnings("static-method")
{indent}@Value("${{datasource.type}}")
{indent}private void setDatasourceType(String datasource_type) {{
{indent}{indent}Sql2oUtility.datasource_type = datasource_type;
{indent}}}
{indent}@SuppressWarnings("unchecked")
{indent}public static <T extends Object> T getInsertedId(
{indent}{indent}String table, 
{indent}{indent}String idfield, 
{indent}{indent}Connection con, 
{indent}{indent}Object key,
{indent}{indent}Class<T> type
{indent}) {{
{indent}{indent}Object res;
{indent}{indent}
{indent}{indent}if (datasource_type.equals(DatasourceTypeEnum.MSSQL.getType())) {{
{indent}{indent}{indent}res = key;
{indent}{indent}}}
{indent}{indent}else if (datasource_type.equals(DatasourceTypeEnum.ORACLE.getType())) {{
{indent}{indent}{indent}try (Query queryid = con.createQuery("SELECT " + idfield + " FROM " + table + " WHERE rowid  = :key")) {{
{indent}{indent}{indent}{indent}queryid.addParameter("key", key);
{indent}{indent}{indent}{indent}res = queryid.executeAndFetchFirst(type);
{indent}{indent}{indent}}}
{indent}{indent}}}
{indent}{indent}else {{
{indent}{indent}{indent}throw new NoSuchElementException("Unknow datasource type: " + datasource_type);
{indent}{indent}}}
{indent}{indent}
{indent}{indent}if (res != null && (type == Long.class && res instanceof BigDecimal)) {{
{indent}{indent}{indent}res = Long.valueOf(((BigDecimal) res).longValue());
{indent}{indent}}}
{indent}{indent}
{indent}{indent}return (T) res;
{indent}}}
}}

"""
)


def write(config):
    sql2outility = sql2outility_tpl.format(
        pack_utility = config.pack_utility, 
        pack_enum = config.pack_enum, 
        indent = config.indent,
        firm_donottouch = config.firm_donottouch,
    )
    
    util.writeToFile(config.data_dir, config.pack_utility, "Sql2oUtility.java", sql2outility)
