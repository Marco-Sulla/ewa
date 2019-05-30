import utility.util as util

tpl = (
"""{firm_donottouch}

package {pack_enum};

public enum DatasourceTypeEnum {{
    MSSQL("mssql"),
    ORACLE("oracle");

    private String type;

    private DatasourceTypeEnum(String type) {{
        this.type = type;
    }}

    public String getType() {{
        return type;
    }}
}}

"""
)


def write(config):
    contents = tpl.format(
        pack_enum = config.pack_enum, 
        firm_donottouch = config.firm_donottouch,
    )
    
    util.writeToFile(config.data_dir, config.pack_enum, "DatasourceTypeEnum.java", contents)
