#!/usr/bin/env python
# coding: utf-8

# # Introduction to connecting and Querying the Augur DB

# If you made to this point, welcome! :) This short tutorial will show how to connect to the database and how to do a simple query. If you need the config file please email cdolfi@redhat.com
# 
# For Project Sandiego's data, we will be using a personal instance of Augur. Augur is a software suite for collecting and measuring structured data about free and open-source software (FOSS) communities.
# 
# Augur gather's trace data for a group of repositories, normalize it into the data model, and provide a variety of metrics about said data. The structure of the data model enables us to synthesize data across various platforms to provide meaningful context for meaningful questions about the way these communities evolve.
# 
# All the notebooks in this folder are based on https://github.com/chaoss/augur-community-reports templates. 

# ## Connect to your database

# Until the Operate First enviroment can connect to the DB, use config file to access. Do not push config file to Github repo

# In[4]:


import psycopg2
import pandas as pd 
import sqlalchemy as salc
import json
import os

with open("../config_temp.json") as config_file:
    config = json.load(config_file)


# In[5]:


database_connection_string = 'postgresql+psycopg2://{}:{}@{}:{}/{}'.format(config['user'], config['password'], config['host'], config['port'], config['database'])

dbschema='augur_data'
engine = salc.create_engine(
    database_connection_string,
    connect_args={'options': '-csearch_path={}'.format(dbschema)})


# ### Retrieve Available Respositories

# In[13]:


repolist = pd.DataFrame()
repo_query = salc.sql.text(f"""
             SET SCHEMA 'augur_data';
             SELECT a.rg_name,
                a.repo_group_id,
                b.repo_name,
                b.repo_id,
                b.forked_from,
                b.repo_archived,
                b.repo_git
            FROM
                repo_groups a,
                repo b
            WHERE
                a.repo_group_id = b.repo_group_id
            ORDER BY
                rg_name,
                repo_name;
    """)
repolist = pd.read_sql(repo_query, con=engine)
display(repolist)
repolist.dtypes


# ### Create a Simpler List for quickly Identifying repo_group_id's and repo_id's for other queries

# In[15]:



repolist = pd.DataFrame()

repo_query = salc.sql.text(f"""
             SET SCHEMA 'augur_data';
             SELECT b.repo_id,
                a.repo_group_id,
                b.repo_name,
                a.rg_name,
                b.repo_git
            FROM
                repo_groups a,
                repo b 
            WHERE
                a.repo_group_id = b.repo_group_id 
            ORDER BY
                rg_name,
                repo_name;   

    """)

repolist = pd.read_sql(repo_query, con=engine)

repolist


# ### Create a list of all of the tables with the total number of data entries 

# In[16]:


repolist = pd.DataFrame()

repo_query = salc.sql.text(f"""
                ANALYZE;
                SELECT schemaname,relname,n_live_tup 
                  FROM pg_stat_user_tables 
                  ORDER BY n_live_tup DESC;

    """)

repolist = pd.read_sql(repo_query, con=engine)

repolist


# Congrats you have done your first queries! There will be a few more simple examples below on how to pull an entire table. If you would like to explore on your own, the schema.png on the home sandiego directory will be greatly helpful in your explorations! Happy querying :) 

# ### Data from the messages 
# 
# This data is the collection of all comments from any issue, PR, commit, etc opened. This example shows another side of the database and the types of data we can pull from it. 

# In[17]:


repolist = pd.DataFrame()

repo_query = salc.sql.text(f"""
             SET SCHEMA 'augur_data';
             SELECT * FROM message
    """)

repolist = pd.read_sql(repo_query, con=engine)

repolist


# ### Contributor affiliation data
# 
# 
# This data tells us what is the company affiliation of many open source contributors. This can help tell us which companies are involved in a certian open source project. 

# In[18]:


repolist = pd.DataFrame()

repo_query = salc.sql.text(f"""
             SET SCHEMA 'augur_data';
             SELECT * FROM contributor_affiliations
    """)

repolist = pd.read_sql(repo_query, con=engine)

repolist


# In[ ]:




