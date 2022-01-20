import pandas as pd 
import sqlalchemy as salc
import json
import matplotlib.pyplot as plt
plt.rcParams['figure.figsize'] = (15, 5)

with open("config_temp.json") as config_file:
    config = json.load(config_file)

database_connection_string = 'postgresql+psycopg2://{}:{}@{}:{}/{}'.format(config['user'], config['password'], config['host'], config['port'], config['database'])

dbschema='augur_data'
engine = salc.create_engine(
    database_connection_string,
    connect_args={'options': '-csearch_path={}'.format(dbschema)})


def issues_open_over_time(project: str):
    #add your repo name(s) here of the repo(s) you want to query if known (and in the database)
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

    for repo_id in repo_set: 

        pr_query = salc.sql.text(f"""
                    SELECT
                        r.repo_name,
                        i.issue_id AS issue, 
                        i.gh_issue_number AS issue_number,
                        i.gh_issue_id AS gh_issue,
                        i.created_at AS created, 
                        i.closed_at AS closed,
                        i.pull_request_id
                    FROM
                        repo r,
                        issues i
                    WHERE
                        r.repo_id = i.repo_id AND
                        i.repo_id = \'{repo_id}\'
            """)
        df_current_repo = pd.read_sql(pr_query, con=engine)
        df_issues = pd.concat([df_issues, df_current_repo])

    df_issues = df_issues.reset_index()
    df_issues.drop("index", axis=1, inplace=True)
    df_issues = df_issues[df_issues['pull_request_id'].isnull()]
    df_issues = df_issues.drop(columns = 'pull_request_id' )


    """
        TODO: James Kunstle; remove this because it's useless now.
    """
    repo_focus = project
    df_issues_focus = df_issues[df_issues['repo_name'] == repo_focus]
    df_issues_focus = df_issues_focus.sort_values(by= "created")
    df_issues_focus = df_issues_focus.reset_index(drop=True)


    df_created = pd.DataFrame(df_issues_focus["created"])
    df_created["issue"] = df_created["created"]
    df_created['open'] = 1
    df_created = df_created.drop(columns="created")

    df_closed = pd.DataFrame(df_issues_focus["closed"]).dropna()
    df_closed["issue"] = df_closed["closed"]
    df_closed['open'] = -1
    df_closed = df_closed.drop(columns= "closed")

    df_open = pd.concat([df_created, df_closed])
    df_open = df_open.sort_values("issue")
    df_open = df_open.reset_index(drop=True)
    df_open["total"] = df_open["open"].cumsum()
    df_open['issue'] = df_open['issue'].dt.floor("D")

    df_open = pd.concat([df_created, df_closed])
    df_open = df_open.sort_values("issue")
    df_open = df_open.reset_index(drop=True)
    df_open["total"] = df_open["open"].cumsum()
    #df_open['issue'] = df_open['issue'].apply(lambda x: x.replace(hour = 0, minute=0, second=0))
    df_open = df_open.drop_duplicates(subset='issue', keep='last')
    df_open = df_open.drop(columns= 'open')

    return df_open
