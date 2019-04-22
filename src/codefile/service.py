import utility.util as util


def write(config):
    service_tpl = (
"""{firm}

package {pack_service};

import java.util.ArrayList;
import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.sql2o.Connection;

import {pack_aggregator}.{aggregator_class};
import {pack_model}.{class_name};
import {pack_repo}.{class_name}Repository;


@Service
public class {class_name}ServiceImpl implements {class_name}Service {{
{indent}@Autowired
{indent}private {class_name}Repository {varname}Repository;
{indent}
{indent}private {aggregator_class} enrich({class_name} {varname}) {{
{indent}{indent}{aggregator_class} {aggregator_var} = null;
{indent}{indent}
{indent}{indent}if ({varname} != null) {{
{indent}{indent}{indent}{aggregator_var} = new {aggregator_class}();
{indent}{indent}{indent}
{indent}{indent}{indent}{aggregator_var}.set{class_name}({varname});
{indent}{indent}}}
{indent}{indent}
{indent}{indent}return {aggregator_var};
{indent}}}
{indent}
{indent}private List<{aggregator_class}> enrich(List<{class_name}> {varname}s) {{
{indent}{indent}List<{aggregator_class}> {aggregator_var}s = new ArrayList<>();
{indent}{indent}
{indent}{indent}if ({varname}s != null) {{
{indent}{indent}{indent}for ({class_name} {varname}: {varname}s) {{
{indent}{indent}{indent}{indent}{aggregator_var}s.add(this.enrich({varname}));
{indent}{indent}{indent}}}
{indent}{indent}}}
{indent}{indent}
{indent}{indent} return {aggregator_var}s;
{indent}}}
{indent}
{indent}@Override
{indent}public List<{aggregator_class}> {select_methods_prefix}All(List<String> fields_to_ignore, Connection con) {{
{indent}{indent}List<{class_name}> {varname}s = {varname}Repository.{select_methods_prefix}All(fields_to_ignore, con);
{indent}{indent}
{indent}{indent}return this.enrich({varname}s);
{indent}}}
{indent}
{indent}@Override
{indent}public List<{aggregator_class}> {select_methods_prefix}All(Connection con) {{
{indent}{indent}List<{class_name}> {varname}s = {varname}Repository.{select_methods_prefix}All(con);
{indent}{indent}
{indent}{indent}return this.enrich({varname}s);
{indent}}}
{indent}
{indent}@Override
{indent}public List<{aggregator_class}> {select_methods_prefix}All(List<String> fields_to_ignore) {{
{indent}{indent}List<{class_name}> {varname}s = {varname}Repository.{select_methods_prefix}All(fields_to_ignore);
{indent}{indent}
{indent}{indent}return this.enrich({varname}s);
{indent}}}
{indent}
{indent}@Override
{indent}public List<{aggregator_class}> {select_methods_prefix}All() {{
{indent}{indent}List<{class_name}> {varname}s = {varname}Repository.{select_methods_prefix}All();
{indent}{indent}
{indent}{indent}return this.enrich({varname}s);
{indent}}}
{indent}
{indent}@Override
{indent}public List<{aggregator_class}> {select_methods_prefix}ByModel({class_name} {varname}, List<String> fields_to_ignore, Connection con) {{
{indent}{indent}List<{class_name}> {varname}s = {varname}Repository.{select_methods_prefix}ByModel({varname}, fields_to_ignore, con);
{indent}{indent}
{indent}{indent}return this.enrich({varname}s);
{indent}}}
{indent}
{indent}@Override
{indent}public List<{aggregator_class}> {select_methods_prefix}ByModel({class_name} {varname}, Connection con) {{
{indent}{indent}List<{class_name}> {varname}s = {varname}Repository.{select_methods_prefix}ByModel({varname}, con);
{indent}{indent}
{indent}{indent}return this.enrich({varname}s);
{indent}}}
{indent}
{indent}@Override
{indent}public List<{aggregator_class}> {select_methods_prefix}ByModel({class_name} {varname}, List<String> fields_to_ignore) {{
{indent}{indent}List<{class_name}> {varname}s = {varname}Repository.{select_methods_prefix}ByModel({varname}, fields_to_ignore);
{indent}{indent}
{indent}{indent}return this.enrich({varname}s);
{indent}}}
{indent}
{indent}@Override
{indent}public List<{aggregator_class}> {select_methods_prefix}ByModel({class_name} {varname}) {{
{indent}{indent}List<{class_name}> {varname}s = {varname}Repository.{select_methods_prefix}ByModel({varname});
{indent}{indent}
{indent}{indent}return this.enrich({varname}s);
{indent}}}
{indent}
{indent}@Override
{indent}public {aggregator_class} {select_methods_prefix}By{methid}({idsfirm}, List<String> fields_to_ignore, Connection con) {{
{indent}{indent}{class_name} {varname} = {varname}Repository.{select_methods_prefix}By{methid}({idslist}, fields_to_ignore, con);
{indent}{indent}
{indent}{indent}return this.enrich({varname});
{indent}}}
{indent}
{indent}@Override
{indent}public {aggregator_class} {select_methods_prefix}By{methid}({idsfirm}, Connection con) {{
{indent}{indent}{class_name} {varname} = {varname}Repository.{select_methods_prefix}By{methid}({idslist}, con);
{indent}{indent}
{indent}{indent}return this.enrich({varname});
{indent}}}
{indent}
{indent}@Override
{indent}public {aggregator_class} {select_methods_prefix}By{methid}({idsfirm}, List<String> fields_to_ignore) {{
{indent}{indent}{class_name} {varname} = {varname}Repository.{select_methods_prefix}By{methid}({idslist}, fields_to_ignore);
{indent}{indent}
{indent}{indent}return this.enrich({varname});
{indent}}}
{indent}
{indent}@Override
{indent}public {aggregator_class} {select_methods_prefix}By{methid}({idsfirm}) {{
{indent}{indent}{class_name} {varname} = {varname}Repository.{select_methods_prefix}By{methid}({idslist});
{indent}{indent}
{indent}{indent}return this.enrich({varname});
{indent}}}
{indent}
{indent}@Override
{indent}public {class_name} insert({class_name} {varname}, Connection con) {{
{indent}{indent}return {varname}Repository.insert({varname}, con);
{indent}}}
{indent}
{indent}@Override
{indent}public {class_name} insert({class_name} {varname}) {{
{indent}{indent}return {varname}Repository.insert({varname});
{indent}}}
{update}
{indent}
{indent}@Override
{indent}public {class_name} save({class_name} {varname}, Connection con) {{
{indent}{indent}return {varname}Repository.save({varname}, con);
{indent}}}
{indent}
{indent}@Override
{indent}public {class_name} save({class_name} {varname}) {{
{indent}{indent}return {varname}Repository.save({varname});
{indent}}}
{indent}
{indent}@Override
{indent}public void delete({idsfirm}, Connection con) {{
{indent}{indent}{varname}Repository.delete({idslist}, con);
{indent}}}
{indent}
{indent}@Override
{indent}public void delete({idsfirm}) {{
{indent}{indent}{varname}Repository.delete({idslist});
{indent}}}
{indent}
{indent}@Override
{indent}public void deleteByModel({class_name} {varname}, Connection con) {{
{indent}{indent}{varname}Repository.deleteByModel({varname}, con);
{indent}}}
{indent}
{indent}@Override
{indent}public void deleteByModel({class_name} {varname}) {{
{indent}{indent}{varname}Repository.deleteByModel({varname});
{indent}}}
}}
"""
    )
    
    update_tpl = (
"""{indent}
{indent}@Override
{indent}public {class_name} update({class_name} {varname}, boolean exclude_nulls, Connection con) {{
{indent}{indent}return {varname}Repository.update({varname}, exclude_nulls, con);
{indent}}}
{indent}
{indent}@Override
{indent}public {class_name} update({class_name} {varname}, boolean exclude_nulls) {{
{indent}{indent}return {varname}Repository.update({varname}, exclude_nulls);
{indent}}}"""
    )
    
    if config.noupdate:
        update = ""
    else:
        update = update_tpl.format(indent=config.indent, class_name=config.class_name, varname=config.varname)
    
    service = service_tpl.format(
        class_name = config.class_name,
        varname = config.varname,
        idsfirm = config.idsfirm,
        idslist = config.idslist,
        methid = config.methid,
        indent = config.indent,
        pack_model = config.pack_model,
        pack_repo = config.pack_repo,
        pack_service = config.pack_service,
        update = update,
        select_methods_prefix = config.select_methods_prefix,
        aggregator_class = config.aggregator_class,
        aggregator_var = config.aggregator_var,
        pack_aggregator = config.pack_aggregator,
        firm = config.firm,
    )
    
    util.writeToFile(config.data_dir, config.pack_service, config.class_name + "ServiceImpl.java", service)

