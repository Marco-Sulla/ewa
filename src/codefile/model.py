import utility.util as util


def write(config):
    model_start = (
"""{firm}

package {pack_model};

{imports}

public class {class_name} {{"""
    )
    
    model_end = "}\n"
    field = "{indent}private {type} {name};"
    
    getter = (
"""{indent}public {type} get{methname}() {{
{indent}{indent}return this.{name};
{indent}}}"""
    )
    
    setter = (
"""{indent}public void set{methname}({type} {name}) {{
{indent}{indent}this.{name} = {name};
{indent}}}"""
    )
    
    fields = ""
    methods = ""
    bigdecimal = False
    
    for row in config.rows:
        col = row[0].upper()
        
        jtype = config.col_types[col]
        
        if jtype == "BigDecimal":
            bigdecimal = True
        
        name = col.lower()
        methname = col.capitalize()
        fields += field.format(type=jtype, name=name, indent=config.indent) + "\n"
        
        methods += (
                getter.format(
                    type=jtype,
                    methname=methname,
                    name=name,
                    select_methods_prefix=config.select_methods_prefix,
                    indent=config.indent,
                ) + "\n\n" +
                setter.format(type=jtype, methname=methname, name=name, indent=config.indent) + "\n\n"
        )
    
    model = ""
    imports = ""
    
    if bigdecimal:
        imports += "import java.math.BigDecimal;\n"
    
    imports += config.import_date_eff
    
    model += model_start.format(
        imports = imports, 
        class_name = config.class_name, 
        pack_model = config.pack_model,
        firm = config.firm,
    )
    model += "\n" + fields + "\n\n" + methods.rstrip() + "\n" + model_end

    util.writeToFile(config.data_dir, config.pack_model, config.class_name + ".java", model)

