import utility.util as util

sql2outility_tpl = (
"""{firm_donottouch}

package {pack_utility};

import org.sql2o.Connection;
import org.sql2o.Query;


public class Sql2oUtility {{
{indent}public static <T extends Object> T getInsertedId(
{indent}{indent}String table, 
{indent}{indent}String idfield, 
{indent}{indent}Connection con, 
{indent}{indent}Object key,
{indent}{indent}Class<T> type
{indent}) {{
{indent}{indent}try (Query queryid = con.createQuery("SELECT " + idfield + " FROM " + table + " WHERE rowid  = :key")) {{
{indent}{indent}{indent}queryid.addParameter("key", key);
{indent}{indent}{indent}return type.cast(queryid.executeAndFetchFirst(type));
{indent}{indent}}}   
{indent}}}
}}

"""
)


def write(config):
    sql2outility = sql2outility_tpl.format(
        pack_utility = config.pack_utility, 
        indent = config.indent,
        firm_donottouch = config.firm_donottouch,
    )
    
    util.writeToFile(config.data_dir, config.pack_utility, "Sql2oUtility.java", sql2outility)
