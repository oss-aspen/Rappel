import psycopg2
import numpy as np
import pandas as pd 
import sqlalchemy as salc
import json
import os
import matplotlib.pyplot as plt
from datetime import datetime
plt.rcParams['figure.figsize'] = (15, 5)
import warnings
warnings.filterwarnings('ignore')

with open("config_temp.json") as config_file:
    config = json.load(config_file)

database_connection_string = 'postgresql+psycopg2://{}:{}@{}:{}/{}'.format(config['user'], config['password'], config['host'], config['port'], config['database'])

dbschema='augur_data'
engine = salc.create_engine(
    database_connection_string,
    connect_args={'options': '-csearch_path={}'.format(dbschema)})

def get_df_recent_users(project: str):
    repo_name_set = [project]
    repo_set = []

    for repo_name in repo_name_set:
        repo_query = salc.sql.text(f"""
                    SET SCHEMA 'augur_data';
                    SELECT 
                        b.repo_id
                    FROM
                        repo_groups a,
                        repo b
                    WHERE
                        a.repo_group_id = b.repo_group_id AND
                        b.repo_name = \'{repo_name}\'
            """)

        t = engine.execute(repo_query)
        repo_id =t.mappings().all()[0].get('repo_id')
        repo_set.append(repo_id)

    df_issues = pd.DataFrame()

    repo_id = repo_set[0]

    pr_query = salc.sql.text(f"""
                SELECT
                    ca.cntrb_id,
                    MAX(i.created_at) as recent_issue
                FROM
                    issues i,
                    contributors_aliases ca
                WHERE
                    i.repo_id = \'{repo_id}\' AND
                    ca.cntrb_alias_id = i.reporter_id or
                    ca.cntrb_id = i.reporter_id
                GROUP BY
                    ca.cntrb_id
                ORDER BY
                    MAX(i.created_at) DESC
        """)

    df_issues = pd.read_sql(pr_query, con=engine)

    df_issues = df_issues.reset_index()
    df_issues.drop("index", axis=1, inplace=True)

    num_unique = len(pd.unique(df_issues.cntrb_id))

    df_commit_authors = pd.DataFrame()

    repo_id = repo_set[0]

    pr_query = salc.sql.text(f"""
                SELECT
                    ca.cntrb_id,
                    MAX(c.cmt_author_timestamp) as recent_authorship
                FROM
                    commits c,
                    contributors_aliases ca
                WHERE
                    c.repo_id = \'{repo_id}\' AND
                    c.cmt_author_email = ca.alias_email
                GROUP BY
                    ca.cntrb_id
                ORDER BY
                    MAX(c.cmt_author_timestamp) DESC
        """)

    df_commit_authors = pd.read_sql(pr_query, con=engine)

    df_commit_authors = df_commit_authors.reset_index()
    df_commit_authors.drop("index", axis=1, inplace=True)

    num_unique = len(pd.unique(df_commit_authors.cntrb_id))

    df_commit_committers = pd.DataFrame()

    repo_id = repo_set[0]

    pr_query = salc.sql.text(f"""
                SELECT
                    ca.cntrb_id,
                    MAX(c.cmt_committer_timestamp) as recent_committership
                FROM
                    commits c,
                    contributors_aliases ca
                WHERE
                    c.repo_id = \'{repo_id}\' AND
                    c.cmt_committer_email = ca.alias_email
                GROUP BY
                    ca.cntrb_id
                ORDER BY
                    MAX(c.cmt_committer_timestamp) DESC
        """)

    df_commit_committers = pd.read_sql(pr_query, con=engine)

    df_commit_committers = df_commit_committers.reset_index()
    df_commit_committers.drop("index", axis=1, inplace=True)

    num_unique = len(pd.unique(df_commit_committers.cntrb_id))

    df_pr_submitters = pd.DataFrame()

    repo_id = repo_set[0]

    pr_query = salc.sql.text(f"""
                SELECT
                    ca.cntrb_id,
                    MAX(p.pr_created_at) as recent_pr_creatorship
                FROM
                    pull_requests p,
                    contributors_aliases ca
                WHERE
                    p.repo_id = \'{repo_id}\' AND
                    p.pr_augur_contributor_id = ca.cntrb_id
                GROUP BY
                    ca.cntrb_id
                ORDER BY
                    MAX(p.pr_created_at) DESC

        """)

    df_pr_submitters = pd.read_sql(pr_query, con=engine)

    df_pr_submitters = df_pr_submitters.reset_index()
    df_pr_submitters.drop("index", axis=1, inplace=True)

    num_unique = len(pd.unique(df_pr_submitters.cntrb_id))

    # convert datetime.date object to np.datetime64 for comparison convenience
    df_commit_authors.recent_authorship = df_commit_authors.recent_authorship.apply(lambda x: np.datetime64(x))

    # convert datetime.date object to np.datetime64 for comparison convenience
    df_commit_committers.recent_committership = df_commit_committers.recent_committership.apply(lambda x: np.datetime64(x))

    # perform the relevant joins. This could be more concise but it is how it is for the moment.
    df_merged = df_issues.set_index("cntrb_id").join(df_pr_submitters.set_index("cntrb_id"))
    df_merged = df_merged.join(df_commit_authors.set_index("cntrb_id"))
    df_merged = df_merged.join(df_commit_committers.set_index("cntrb_id"))

    # change all NaT to 0
    df_merged = df_merged.apply(lambda x: 0 if x is pd.NaT else x)
    # take the maximum value from each row and create a new column for it
    df_merged["most_recent"] = df_merged.apply(np.max,  axis=1)

    df_recent = df_merged[ "most_recent"].reset_index()

    return df_recent

def get_df_active_drifting_users(project: str):
    df_recent = get_df_recent_users(project)

    # today, 6 month time difference, date six months ago
    now = np.datetime64('now')
    sixmos =  np.timedelta64(6, "M").astype('timedelta64[ns]')
    twelvemos =  np.timedelta64(12, "M").astype('timedelta64[ns]')

    sixmosago = now - sixmos
    twelvemosago = now - twelvemos

    # df of "active contributors" vs df of "drifting contributors"
    df_active = df_recent[ df_recent["most_recent"] >= sixmosago]
    df_drifting = df_recent[(sixmosago > df_recent["most_recent"]) & (df_recent["most_recent"] >= twelvemosago)]
    df_gone = df_recent[(df_recent['most_recent'] < twelvemosago)]

    data = [['active', df_active.shape[0]],
            ['drifting', df_drifting.shape[0]],
            ['gone', df_gone.shape[0]]]
    
    df_summary = pd.DataFrame(data, columns=['Name', 'Count'])
    return df_summary