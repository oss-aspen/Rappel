Project Aspen (Sandiego)
==============================

Project Aspen will glean information from open source-ecosystem data sets that can help drive community- and business-oriented decision making. Using data-analysis tools built by OSPO, as well as community metric tools from Project CHAOSS, Sandiego will enable contributors and participants to ask questions and make data-informed decisions about open source projects and communities.

Project Discussion
------------

We have a [Matrix](https://matrix.org) room for discussion of anything Sandiego-related. Come chat with us in [#sandiego-rh:matrix.org](https://matrix.to/#/!eSeeqXiNqjrlNaeAdQ:matrix.org)!

[Example of config.json file](./config.json.example):
```
{
    "connection_string": "sqlite:///:memory:",
    "database": "sandiegorh",
    "host": "chaoss.tv",
    "password": "<<Your Password>>",
    "port": 5432,
    "schema": "augur_data",
    "user": "<<Your Username>>",
    "user_type": "read_only"
}

```

Project Organization
------------

    ├── LICENSE
    ├── Makefile           <- Makefile with commands like `make data` or `make train`
    ├── Pipfile            <- Pipfile stating package configuration as used by Pipenv.
    ├── Pipfile.lock       <- Pipfile.lock stating a pinned down software stack with as used by Pipenv.
    ├── README.md          <- The top-level README for developers using this project.
    ├── data
    │   ├── external       <- Data from third party sources.
    │   ├── interim        <- Intermediate data that has been transformed.
    │   ├── processed      <- The final, canonical data sets for modeling.
    │   └── raw            <- The original, immutable data dump.
    │
    ├── docs               <- A default Sphinx project; see sphinx-doc.org for details
    │
    ├── models             <- Trained and serialized models, model predictions, or model summaries
    │
    ├── notebooks          <- Jupyter notebooks. Naming convention is a number (for ordering),
    │                         the creator's initials, and a short `-` delimited description, e.g.
    │                         `1.0-jqp-initial-data-exploration`.
    │
    ├── references         <- Data dictionaries, manuals, and all other explanatory materials.
    │
    ├── reports            <- Generated analysis as HTML, PDF, LaTeX, etc.
    │   └── figures        <- Generated graphics and figures to be used in reporting
    │
    ├── requirements.txt   <- The requirements file stating direct dependencies if a library
    │                         is developed.
    │
    ├── setup.py           <- makes project pip installable (pip install -e .) so src can be imported
    ├── src                <- Source code for use in this project.
    │   ├── __init__.py    <- Makes src a Python module
    │   │
    │   ├── data           <- Scripts to download or generate data
    │   │   └── make_dataset.py
    │   │
    │   ├── features       <- Scripts to turn raw data into features for modeling
    │   │   └── build_features.py
    │   │
    │   ├── models         <- Scripts to train models and then use trained models to make
    │   │   │                 predictions
    │   │   ├── predict_model.py
    │   │   └── train_model.py
    │   │
    │   └── visualization  <- Scripts to create exploratory and results oriented visualizations
    │       └── visualize.py
    │
    ├── .thoth.yaml        <- Thoth's configuration file
    ├── .aicoe-ci.yaml     <- AICoE CI configuration file (https://github.com/AICoE/aicoe-ci)
    └── tox.ini            <- tox file with settings for running tox; see tox.readthedocs.io


--------

<p><small>Project based on the <a target="_blank" href="https://drivendata.github.io/cookiecutter-data-science/">cookiecutter data science project template</a>. #cookiecutterdatascience</small></p>
