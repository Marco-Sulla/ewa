import re
from .IDbUtility import IDbUtility


class OracleUtility(IDbUtility):
    @classmethod
    def convertToJavaType(
            cls,
            sql_type,
            prec,
            radix,
            scale,
            use_integer_instead_of_short,
            use_bigdecimal_instead_of_double,
            use_bigdecimal_instead_of_long
    ):
        if prec is None:
            prec = 0

        if scale is None:
            scale = 0
    
        sql_type = sql_type.lower()
        re_ts = re.compile("timestamp\(\d+\)")
    
        if sql_type == "number":
        
            if scale == 0:
                maxn = radix ** (prec - scale)
                if maxn < 2 ** 16:
                    if use_integer_instead_of_short:
                        return "Integer"
                    else:
                        return "Short"
                elif maxn < 2 ** 32:
                    return "Integer"
                elif maxn < 2 ** 64:
                    return "Long"
                else:
                    if use_bigdecimal_instead_of_long:
                        return "BigDecimal"
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
    
    get_columns_data_sql = (
"""
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
    )

