import pandas as pd 
import sqlalchemy as salc
import matplotlib.pyplot as plt
import json
import warnings

plt.rcParams['figure.figsize'] = (17, 5)

warnings.filterwarnings('ignore')

with open("config_temp.json") as config_file:
    config = json.load(config_file)

database_connection_string = 'postgresql+psycopg2://{}:{}@{}:{}/{}'.format(config['user'], 
                                                                           config['password'], 
                                                                           config['host'], 
                                                                           config['port'], 
                                                                           config['database'])

dbschema='augur_data'
engine = salc.create_engine(
    database_connection_string,
    connect_args={'options': '-csearch_path={}'.format(dbschema)})


def new_pr_submitters(project: str):

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

    df_pr = pd.DataFrame()

    for repo_id in repo_set: 

        pr_query = salc.sql.text(f"""
                    SELECT
                        p.pr_augur_contributor_id as pr_src_id,
                        p.pr_created_at
                    FROM
                        pull_requests p
                    WHERE
                        p.repo_id = \'{repo_id}\'
                    ORDER BY
                        p.pr_created_at
            """)
        df_current_repo = pd.read_sql(pr_query, con=engine)
        df_pr = pd.concat([df_pr, df_current_repo])

    df_pr = df_pr.reset_index()
    df_pr.drop("index", axis=1, inplace=True)

    # get only the first incidence of a user making a pr.
    df_pr = df_pr.drop_duplicates(subset="pr_src_id", keep="first")

    # sort the values by the time/date of pr.
    df_pr = df_pr.sort_values("pr_created_at")

    # reset the index and drop the index - gets rid of sorting index problem.
    df_pr = df_pr.reset_index()
    df_pr.drop("index", axis=1, inplace=True)

    # reset the index so index is a column, increasing (1,df.size+1)
    df_pr = df_pr.reset_index()

    return df_pr