# EWA

Generator of Java code for Spring Boot + sql2o projects.

It auto generates, from a database table:
- Model
- Repository
- Service
- Aggregate

# Features
- Support for tables with primary key with multiple fields
- Basic SELECT sql, centralized for all `find` methods. Update it and all 
  `find` methods will be updated
- `find` methods have an optional `fields_to_ignore` parameter, to filter 
  fields in SELECTs
- All methods are overloaded with a method with transaction and a method 
  without transaction, if you don't need it
- Method `findByModel()`, to SELECT from database matching fields populated in 
  model. No need to create `findBySomefield()`
- Similar method `deleteByModel()` 
- `save()` method, that first checks for row existance, and then call 
  `insert()` or `update()`
- `exclude_nulls` optional parameter for `update()`, that does not update 
  fields that are nulls
- `Service` methods returns a Aggregate object, with the model as one of the 
  attributes
- `Service` has an `enrich()` stub method, for augmenting the `Aggregate` and 
  `List<Aggregate>` objects returned by `Service` methods. All `Service` methods 
  created by EWA calls `enrich()` by default.
- SELECT methods prefix is configurable. You can use "find", "get", "givePapa" 
  or whatever you want
- Configurable indentation style

# Install
See INSTALL.TXT

# Use
1. Open a cmd or a shell
2. Go to the folder where you extracted EWA
3. Go to `src` folder
4. Copy config_example.ini` in another .ini file, and edit it following its 
   comments
5. If you have Linux, you have to source `oracle_env.sh`. See ORACLE.txt for 
   more details
6. Launch in the shell: `> python3 ewa.py --config YOUR_CONFIG.ini`. If you 
   have Windows, use `python` instead of `python3`
7. Read and follow the instructions at the end of script launching

# Tested databases
Oracle 12C+, MSSQL 2012+. Not all field types are currently supported. Please 
open an issue if you want me to add one:
https://github.com/MarcoSulla/ewa/issues/new?assignees=&labels=&template=bug_report.md&title=%5BBUG%5D+

# Untested, but potentially working databases
I'm using `sqlalchemy`, so in teory I can support any database that it supports: 
https://docs.sqlalchemy.org/en/13/dialects/

If you want to add a database, please open an issue:
https://github.com/MarcoSulla/ewa/issues/new?assignees=&labels=&template=bug_report.md&title=%5BBUG%5D+

# License
See LICENSE file
