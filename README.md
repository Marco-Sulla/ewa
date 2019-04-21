# EWA

Generator of Java code for Spring Boot + [sql2o](https://www.sql2o.org/) projects.

It auto generates, from a database table:
- Model
- Repository
- Service

# Features
- Support for tables with primary key with multiple fields
- Basic SELECT sql, centralized for all `find` methods. Update it and all `find` methods will be updated
- `find` methods have an optional `fields_to_ignore` parameter, to filter fields in SELECTs
- All methods are overloaded with a method with transaction and a method without transaction, if you don't need it
- Method `findByModel()`, to SELECT from database matching fields populated in model. No need to create `findBySomefield()`
- Similar method `deleteByModel()` 
- `save()` method, that first checks for row existance, and then call `insert()` or `update()`
- `exclude_nulls` optional parameter for `update()`, that does not update fields that are nulls
- `Service` methods returns a [`Aggregate`](https://en.wikipedia.org/wiki/Domain-driven_design#Building_blocks) object, with the model as one of the attributes
- `Service` has an `enrich()` stub method, for augmenting the `Aggregate` and `List<Aggregate>` objects returned by `Service` method. All `Service` method created by EWA calls `enrich()` by default.

# Install
See [`INSTALL.TXT`](https://raw.githubusercontent.com/MarcoSulla/ewa/master/INSTALL.txt) . You can download the program at [Releases](https://github.com/MarcoSulla/ewa/releases).

# Use
1. Go to `src` folder
1. Create a `.ini` file. See [`config_example.ini`](https://raw.githubusercontent.com/MarcoSulla/ewa/master/src/config_example.ini)
2. `python3 ewa.py --config YOUR_CONFIG.ini`
3. Read and follow the instructions at the end of script launching

# Tested databases
Oracle 12C+, MSSQL 2012+. Not all field types are currently supported. Please [open an issue](https://github.com/MarcoSulla/ewa/issues/new?assignees=&labels=&template=bug_report.md&title=%5BBUG%5D+) if you want me to add one.

# Untested, but potentially working databases
I'm using `sqlalchemy`, so in teory I can support any database that [it supports](https://docs.sqlalchemy.org/en/13/dialects/). If you want to add a database, please [open an issue](https://github.com/MarcoSulla/ewa/issues/new?assignees=&labels=&template=bug_report.md&title=%5BBUG%5D+).

# License
See [LICENSE](https://github.com/MarcoSulla/ewa/blob/master/LICENSE)
