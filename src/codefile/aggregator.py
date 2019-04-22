import utility.util as util


def write(config):
    aggregator_tpl = (
"""{firm}

package {pack_aggregator};

import {pack_model}.{class_name};

public class {class_name}Aggregator {{
{indent}private {class_name} {varname};
{indent}
{indent}public {class_name} get{class_name}() {{
{indent}{indent}return this.{varname};
{indent}}}
{indent}
{indent}public void set{class_name}({class_name} {varname}) {{
{indent}{indent}this.{varname} = {varname};
{indent}}}
}}
"""
    )
    
    aggregator = aggregator_tpl.format(
        pack_aggregator = config.pack_aggregator,
        pack_model = config.pack_model,
        class_name = config.class_name,
        varname = config.varname,
        indent = config.indent,
        firm = config.firm, 
    )
    
    util.writeToFile(config.data_dir, config.pack_aggregator, config.class_name + "Aggregator.java", aggregator)

