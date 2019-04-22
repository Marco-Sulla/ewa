import utility.util as util


def write(config):
    serviceint_tpl = (
"""{firm}

package {pack_service};

import java.util.List;

import org.sql2o.Connection;

import {pack_aggregator}.{aggregator_class};
import {pack_model}.{class_name};

public interface {class_name}Service {{
{indent}{aggregator_class} {select_methods_prefix}By{methid}({idsfirm}, List<String> fields_to_ignore, Connection con);
{indent}
{indent}{aggregator_class} {select_methods_prefix}By{methid}({idsfirm}, Connection con);
{indent}
{indent}{aggregator_class} {select_methods_prefix}By{methid}({idsfirm}, List<String> fields_to_ignore);
{indent}
{indent}{aggregator_class} {select_methods_prefix}By{methid}({idsfirm});
{indent}
{indent}{class_name} insert({class_name} {varname}, Connection con);
{indent}
{indent}{class_name} insert({class_name} {varname});
{update}
{indent}
{indent}{class_name} save({class_name} {varname}, Connection con);
{indent}
{indent}{class_name} save({class_name} {varname});
{indent}
{indent}List<{aggregator_class}> {select_methods_prefix}All(List<String> fields_to_ignore, Connection con);
{indent}
{indent}List<{aggregator_class}> {select_methods_prefix}All(Connection con);
{indent}
{indent}List<{aggregator_class}> {select_methods_prefix}All(List<String> fields_to_ignore);
{indent}
{indent}List<{aggregator_class}> {select_methods_prefix}All();
{indent}
{indent}List<{aggregator_class}> {select_methods_prefix}ByModel({class_name} {varname}, List<String> fields_to_ignore, Connection con);
{indent}
{indent}List<{aggregator_class}> {select_methods_prefix}ByModel({class_name} {varname}, Connection con);
{indent}
{indent}List<{aggregator_class}> {select_methods_prefix}ByModel({class_name} {varname}, List<String> fields_to_ignore);
{indent}
{indent}List<{aggregator_class}> {select_methods_prefix}ByModel({class_name} {varname});
{indent}
{indent}void delete({idsfirm}, Connection con);
{indent}
{indent}void delete({idsfirm});
{indent}
{indent}void deleteByModel({class_name} {varname}, Connection con);
{indent}
{indent}void deleteByModel({class_name} {varname});
}}
"""
    )
    
    update_tpl = (
"""{indent}
{indent}{class_name} update({class_name} {varname}, boolean exclude_nulls, Connection con);
{indent}
{indent}{class_name} update({class_name} {varname}, boolean exclude_nulls);"""
    )
    
    if config.noupdate:
        update = ""
    else:
        update = update_tpl.format(indent=config.indent, class_name=config.class_name, varname=config.varname)
    
    serviceint = serviceint_tpl.format(
        class_name = config.class_name,
        varname = config.varname,
        methid = config.methid,
        idsfirm = config.idsfirm,
        indent = config.indent,
        pack_service = config.pack_service,
        pack_model = config.pack_model,
        update = update,
        select_methods_prefix = config.select_methods_prefix,
        aggregator_class = config.aggregator_class,
        pack_aggregator = config.pack_aggregator,
        firm = config.firm,
    )
    
    util.writeToFile(config.data_dir, config.pack_service, config.class_name + "Service.java", serviceint)
