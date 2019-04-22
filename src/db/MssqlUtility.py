from .IDbUtility import IDbUtility


class MssqlUtility(IDbUtility):
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
        sql_type = sql_type.lower()
    
        if prec is None:
            prec = 0
    
        if scale is None:
            scale = 0
        
        if sql_type == "numeric":
            if scale == 0:
                maxn = radix**(prec - scale)
                
                if maxn < 2**16:
                    if use_integer_instead_of_short:
                        return "Integer"
                    else:
                        return "Short"
                elif maxn < 2**32:
                    return "Integer"
                elif maxn < 2**64:
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
    
    @classmethod
    @property
    def get_columns_data_sql(cls):
        return (
"""
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
        )

