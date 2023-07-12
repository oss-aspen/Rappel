import sqlalchemy as salc
import json
import pandas as pd

with open("copy_cage-padres.json") as config_file:
    config = json.load(config_file)

# connect to Augur database
database_connection_string = 'postgresql+psycopg2://{}:{}@{}:{}/{}'.format(config['user'], config['password'], config['host'], config['port'], config['database'])

dbschema='augur_data'
engine = salc.create_engine(
    database_connection_string,
    connect_args={'options': '-csearch_path={}'.format(dbschema)})

#------------------------------------------------------ AUGUR QUERY ------------------------------------------------------ 
def fetch_data(repo_org, repo_name, query_strs):
    # perform queries for event types specified in query_strs
    for event in query_strs: 
        if event == 'cmt':
            cmt_data = commit_query(repo_org, repo_name)
        if event == 'ism':
            ism_data = issue_msg_query(repo_org, repo_name)
        if event == 'pr':
            pr_data = pr_query(repo_org, repo_name)
        if event == 'prm': 
            prm_data = pr_msg_query(repo_org, repo_name)

    return cmt_data, ism_data, pr_data, prm_data

# commit author query
def commit_query(repo_org, repo_name):
    cmt_query = salc.sql.text(f"""
                    SET SCHEMA 'augur_data';
                    SELECT
                        DISTINCT c.cmt_commit_hash,
                        c.cmt_committer_timestamp as timestamp,
                        (SELECT ca.cntrb_id FROM contributors_aliases ca WHERE c.cmt_author_email = ca.alias_email) as author_id,
                        (SELECT ca.cntrb_id FROM contributors_aliases ca WHERE c.cmt_committer_email = ca.alias_email) as committer_id
                    FROM
                        repo_groups rg,
                        repo r,
                        commits c
                    WHERE
                        c.repo_id = r.repo_id AND
                        rg.repo_group_id = r.repo_group_id AND
                        rg.rg_name = \'{repo_org}\' AND
                        r.repo_name = \'{repo_name}\' AND
                        c.cmt_author_email != c.cmt_committer_email
                    ORDER BY
                        timestamp DESC
            """)

    cmt_data = pd.read_sql(cmt_query, con=engine)
    cmt_data = cmt_data.dropna()
    cmt_data['year'] = pd.to_datetime(cmt_data['timestamp'], utc=True).dt.year
    cmt_data['month'] = pd.to_datetime(cmt_data['timestamp'], utc=True).dt.month

    return cmt_data

# issue message query
def issue_msg_query(repo_org, repo_name):
    ism_query = salc.sql.text(f"""
                 SET SCHEMA 'augur_data';
                 SELECT
                    i.issue_id,
                    m.cntrb_id,
                    i.closed_at as timestamp
                FROM
                    repo_groups rg,
                    repo r,
                    issues i,
                    issue_message_ref imr,
                    message m
                WHERE
                    rg.repo_group_id = r.repo_group_id AND
                    i.repo_id = r.repo_id AND
                    i.issue_id = imr.issue_id AND
                    m.msg_id = imr.msg_id AND
                    rg.rg_name = \'{repo_org}\' AND
                    r.repo_name = \'{repo_name}\'
                ORDER BY
                      timestamp DESC
        """)

    ism_data = pd.read_sql(ism_query, con=engine)

    # reformat issue message data, combine contributor ids for each issue
    ism_data = ism_data.groupby('issue_id').agg({'cntrb_id': list, 'timestamp': 'last'}).reset_index()
    # remove issues with only one contributor (no connection to be made)
    ism_data = ism_data[ism_data['cntrb_id'].apply(lambda x: len(x) > 1)]
    ism_data = ism_data.sort_values('timestamp', ascending=False)
    ism_data['year'] = pd.to_datetime(ism_data['timestamp'], utc=True).dt.year
    ism_data['month'] = pd.to_datetime(ism_data['timestamp'], utc=True).dt.month

    return ism_data

def pr_query(repo_org, repo_name): 
    # pull request reviewer query
    pr_query = salc.sql.text(f"""
                  SET SCHEMA 'augur_data';
                  SELECT
                      pr.pull_request_id,
                      pre.cntrb_id,
                      prr.cntrb_id as reviewer,
                      pr.pr_created_at as timestamp
                  FROM
                      repo_groups rg,
                      repo r,
                      pull_requests pr,
                      pull_request_events pre,
                      pull_request_reviewers prr
                  WHERE
                      rg.repo_group_id = r.repo_group_id AND
                      pr.repo_id = r.repo_id AND
                      pr.pull_request_id = pre.pull_request_id AND
                      pr.pull_request_id = prr.pull_request_id AND
                      pre.cntrb_id != prr.cntrb_id AND
                      rg.rg_name = \'{repo_org}\' AND
                      r.repo_name = \'{repo_name}\'
                  ORDER BY
                      timestamp DESC
          """)

    pr_data = pd.read_sql(pr_query, con=engine)
    pr_data = pr_data.dropna()
    pr_data['year'] = pd.to_datetime(pr_data['timestamp'], utc=True).dt.year
    pr_data['month'] = pd.to_datetime(pr_data['timestamp'], utc=True).dt.month

    return pr_data

def pr_msg_query(repo_org, repo_name): 
    #pull request message query
    prm_query = salc.sql.text(f"""
                  SET SCHEMA 'augur_data';
                  SELECT
                      pr.pull_request_id,
                      m.cntrb_id,
                      pr.pr_created_at as timestamp
                  FROM
                      repo_groups rg,
                      repo r,
                      pull_requests pr,
                      pull_request_message_ref prm,
                      message m
                  WHERE
                      rg.repo_group_id = r.repo_group_id AND
                      pr.repo_id = r.repo_id AND
                      pr.pull_request_id = prm.pull_request_id AND
                      m.msg_id = prm.msg_id AND
                      rg.rg_name = \'{repo_org}\' AND
                      r.repo_name = \'{repo_name}\'
                  ORDER BY
                      timestamp DESC
          """)

    prm_data = pd.read_sql(prm_query, con=engine)

    # reformat pull request message data, combine contributor ids for each pr thread
    prm_data = prm_data.groupby('pull_request_id').agg({'cntrb_id': list, 'timestamp': 'last'}).reset_index()
    # remove pr threads with only one contributor (no connection to be made)
    prm_data = prm_data[prm_data['cntrb_id'].apply(lambda x: len(x) > 1)]
    prm_data = prm_data.sort_values('timestamp', ascending=False)
    prm_data['year'] = pd.to_datetime(prm_data['timestamp'], utc=True).dt.year
    prm_data['month'] = pd.to_datetime(prm_data['timestamp'], utc=True).dt.month

    return prm_data
