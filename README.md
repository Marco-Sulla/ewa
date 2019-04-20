# EWA

Generator of Java code for Spring + [sql2o](https://www.sql2o.org/) projects.

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
See [`INSTALL.TXT`](https://raw.githubusercontent.com/MarcoSulla/ewa/master/INSTALL.txt)

# Use
1. Create a `.ini` file. See [`src/config_example.ini`](https://raw.githubusercontent.com/MarcoSulla/ewa/master/src/config_example.ini)
2. `python3 ewa.py --config path/to/your_config.ini`
3. Read and follow the instructions at the end of script launching

# Example of use of a transaction

```
MyAggregate myAggregate;

try (Connection con = sql2o.open(); Query query = con.createQuery("")) {
    myAggregate = myService.getByMyid(myid, query, con);
}
```

This trick will autoclose the query even if an exception is throwed. This is because the sql of the query is set inside the repository, using reflections. The reflection trick and the ugly `con.createQuery("")` instead of a simple `con.createQuery()` will disappear if [Pull 323](https://github.com/aaberg/sql2o/pull/323) in sql2o github repo will be merged.

# Tested databases
Oracle 12C+, MSSQL 2012+. Not all field types are currently supported. Please [open an issue](https://github.com/MarcoSulla/ewa/issues/new?assignees=&labels=&template=bug_report.md&title=%5BBUG%5D+) if you want me to add one.

# Untested, but potentially working databases
PostgreSql, MySql, MariaDb. Please install the corresponding python3 driver and see the notes for the "Tested databases"

I'm using `sqlalchemy`, so in teory I can support any database that it supports. If you want to add a database, please [open an issue](https://github.com/MarcoSulla/ewa/issues/new?assignees=&labels=&template=bug_report.md&title=%5BBUG%5D+).
