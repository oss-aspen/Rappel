# Setting Up your Notebook Environment 

1. Make sure you have Python 3 installed. `python3 --version` from the command line. 
2. Create your virtual environment. `python -m venv .venv`. This will install the python virtual environment into a `.venv` folder that you will activate next. This folder will not be loaded to your repository or "the repository" because it is in the `.gitignore` file. 
3. Activate your python environment `source .venv/bin/activate`  
4. Install the required libraries `pip install -r {requirements file}`. The core requirements file is `requirements.txt`. 
5. Start your notebooks `jupyter lab`
6. Have fun!!

## Testing Notebooks in your environment 

1. This can be helpful for knowing if, for example, you are using a newer version of Python that may or may not work. 
2. And it will inform you regarding whether or not some of the notebooks break with the latest version. 

```
pip install pytest nbmake
python ./test_environment.py # Test your basic environment
pytest --nbmake notebooks/ # From the Root directory, test every notebook
```

## For Notebook Queries need Repo Information
This block of code allows you to prompt the user for specific repos they want to analyze in a notebook. It is currently deployed in `notebooks/8knot/bus-factor.ipynb`. 

```

```