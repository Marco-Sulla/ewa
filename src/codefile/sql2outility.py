import utility.util as util


def write(config):
    sql2outility_tpl = (
"""{firm}

package {pack_utility};

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
    
    sql2outility = sql2outility_tpl.format(
        pack_utility = config.pack_utility, 
        indent = config.indent,
        firm = config.firm,
    )
    
    util.writeToFile(config.data_dir, config.pack_utility, "Sql2oUtility.java", sql2outility)

