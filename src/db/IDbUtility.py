from abc import ABC, abstractmethod


class IDbUtility(ABC):
    @classmethod
    @abstractmethod
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
        pass

    @classmethod
    @property
    @abstractmethod
    def get_columns_data_sql(cls):
        pass
