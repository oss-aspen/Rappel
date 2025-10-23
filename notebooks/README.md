# Notebooks 

This folder is for visualization notebooks. 

    ├── 8knot         <- Visualization development for 8Knot
    ├── density_metrics        <- EDA 
    ├── graph_analysis        <- EDA for discovering important open source projects
    ├── old        <- archieve notebooks from beginning of projects
    ├── performance        <- EDA 
    ├── survival_analysis           <- EDA notebooks for dash app


# Default Database Connection Package
This code will find your database configuration file, `config.json`, wherever it is.
```python
paths = ["../../comm_cage.json", "comm_cage.json", "../../config.json", "../config.json", "config.json","../../../config.json"]

for path in paths:
    if os.path.exists(path):
        with open(path) as config_file:
            config = json.load(config_file)
        break
else:
    raise FileNotFoundError(f"None of the config files found: {paths}")

database_connection_string = 'postgresql+psycopg2://{}:{}@{}:{}/{}'.format(config['user'], config['password'], config['host'], config['port'], config['database'])
dbschema = 'augur_data'
engine = salc.create_engine(
    database_connection_string,
    connect_args={'options': '-csearch_path={}'.format(dbschema)}
)
```