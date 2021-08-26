#!/usr/bin/env python
# coding: utf-8

# # Introduction to connecting and Querrying the Augur DB

# If you made to this point, welcome! :) This short tutorial will show how to connect to the database and how to do a simple querry. If you need the config file please email cdolfi@redhat.com
# 
# All the notebooks in this folder are based on https://github.com/chaoss/augur-community-reports templates. 

# ## Connect to your database

# Until the Operate First enviroment can connect to the DB, use config file to access. Do not push config file to Github repo

# In[2]:


import psycopg2
import pandas as pd 
import sqlalchemy as salc
import json
import os

with open("../../config.json") as config_file:
    config = json.load(config_file)


# In[3]:


database_connection_string = 'postgresql+psycopg2://{}:{}@{}:{}/{}'.format(config['user'], config['password'], config['host'], config['port'], config['database'])

dbschema='augur_data'
engine = salc.create_engine(
    database_connection_string,
    connect_args={'options': '-csearch_path={}'.format(dbschema)})


# ### Retrieve Available Respositories

# In[4]:


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

# In[5]:



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

repolist[50:150]


# ### Create a list of all of the tables with the total number of data entries 

# In[6]:


repolist = pd.DataFrame()

repo_query = salc.sql.text(f"""
                ANALYZE;
                SELECT schemaname,relname,n_live_tup 
                  FROM pg_stat_user_tables 
                  ORDER BY n_live_tup DESC;

    """)

repolist = pd.read_sql(repo_query, con=engine)

repolist[:35]


# Congrats you have done your first queries! There will be a few more simple examples below on how to pull an entire table. If you would like to explore on your own, the schema.png on the home sandiego directory will be greatly helpful in your explorations! Happy querying :) 

# ### Data from the messages 

# In[12]:


repolist = pd.DataFrame()

repo_query = salc.sql.text(f"""
             SET SCHEMA 'augur_data';
             SELECT * FROM message
    """)

repolist = pd.read_sql(repo_query, con=engine)

repolist[:100]


# ### Contributor affiliation data

# In[11]:


repolist = pd.DataFrame()

repo_query = salc.sql.text(f"""
             SET SCHEMA 'augur_data';
             SELECT * FROM contributor_affiliations
    """)

repolist = pd.read_sql(repo_query, con=engine)

repolist[650:700]


# In[ ]:




