import sqlalchemy as salc
import json
import pandas as pd
import os 

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

def fetch_data(repo_org, repo_name):
    """
    Fetch data from the Augur database for different events in a GitHub repository.

    Args:
    -----
        repo_org (str): The organization name of the repository.
        repo_name (str): The name of the repository.
       
    Returns:
    --------
        tuple: A tuple containing data frames for each event:
            - cmt_data (pd.DataFrame): Data frame containing commit data with commit hash, timestamps, 
                                      and corresponding author and committer IDs.
            - ism_data (pd.DataFrame): Data frame containing issue message data with issue IDs, 
                                      timestamps, and contributor IDs associated with each issue.
            - pr_data (pd.DataFrame): Data frame containing pull request data with pull request IDs, 
                                     timestamps, contributor IDs, and reviewer IDs for each pull request.
            - prm_data (pd.DataFrame): Data frame containing pull request message data with pull 
                                      request IDs, timestamps, and contributor IDs associated with 
                                      each pull request message thread.
    """

    cmt_data = commit_query(repo_org, repo_name)
    ism_data = issue_msg_query(repo_org, repo_name)
    pr_data = pr_query(repo_org, repo_name)
    prm_data = pr_msg_query(repo_org, repo_name)

    return cmt_data, ism_data, pr_data, prm_data


def is_repo_exists(repo_org, repo_name):
    """
    Check if the given repository exists in the database.

    Args:
    -----
        repo_org (str): The organization name of the repository.
        repo_name (str): The name of the repository.

    Returns:
    --------
        bool: True if the repository exists, False otherwise.
    """
    repo_check_query = salc.sql.text(f"""
        SET SCHEMA 'augur_data';
        SELECT EXISTS (
            SELECT 1
            FROM repo_groups rg
            JOIN repo r ON rg.repo_group_id = r.repo_group_id
            WHERE r.repo_git = \'{f"https://github.com/{repo_org}/{repo_name}"}\'
        )
    """)

    result = pd.read_sql(repo_check_query, con=engine)
    exists = result.iloc[0, 0] 
    return exists


def commit_query(repo_org, repo_name):
    """
    Execute a SQL query to fetch commit data for a given repository.

    Args:
    -----
        repo_org (str): The organization name of the repository.
        repo_name (str): The name of the repository.

    Returns:
    --------
        pd.DataFrame: Data frame containing commit data with commit hash, timestamps, and corresponding 
                      author and committer IDs.
    """
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
                        r.repo_git = \'{f"https://github.com/{repo_org}/{repo_name}"}\' AND
                        c.cmt_author_email != c.cmt_committer_email
                    ORDER BY
                        timestamp DESC
            """)

    cmt_data = pd.read_sql(cmt_query, con=engine)
    cmt_data = cmt_data.dropna()
    # Convert the timestamp column to offset-naive datetime objects
    cmt_data['timestamp'] = cmt_data['timestamp'].apply(lambda x: x.replace(tzinfo=None) if x.tzinfo else x)

    return cmt_data


def issue_msg_query(repo_org, repo_name):
    """
    Execute a SQL query to fetch issue message data for a given repository.

    Args:
    -----
        repo_org (str): The organization name of the repository.
        repo_name (str): The name of the repository.

    Returns:
    --------
        pd.DataFrame: Data frame containing issue message data with issue IDs, timestamps, and 
                      contributor IDs associated with each issue.
    """
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
                    r.repo_git = \'{f"https://github.com/{repo_org}/{repo_name}"}\'
                ORDER BY
                      timestamp DESC
        """)

    ism_data = pd.read_sql(ism_query, con=engine)

    # reformat issue message data, combine contributor ids for each issue
    ism_data = ism_data.groupby('issue_id').agg({'cntrb_id': list, 'timestamp': 'last'}).reset_index()
    
    # remove issues with only one contributor (no connection to be made)
    ism_data = ism_data[ism_data['cntrb_id'].apply(lambda x: len(x) > 1)]
    ism_data = ism_data.sort_values('timestamp', ascending=False)

    return ism_data


def pr_query(repo_org, repo_name): 
    """
    Execute a SQL query to fetch pull request data for a given repository.
    
    Args:
    -----
        repo_org (str): The organization name of the repository.
        repo_name (str): The name of the repository.

    Returns:
    --------
        pd.DataFrame: Data frame containing pull request data with pull request IDs, timestamps, 
                      contributor IDs, and reviewer IDs for each pull request.
    """
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
                      r.repo_git = \'{f"https://github.com/{repo_org}/{repo_name}"}\'
                  ORDER BY
                      timestamp DESC
          """)

    pr_data = pd.read_sql(pr_query, con=engine)
    pr_data = pr_data.dropna()

    return pr_data


def pr_msg_query(repo_org, repo_name): 
    """
    Execute a SQL query to fetch pull request message data for a given repository.

    Args:
    -----
        repo_org (str): The organization name of the repository.
        repo_name (str): The name of the repository.

    Returns:
    --------
        pd.DataFrame: Data frame containing pull request message data with pull request IDs, timestamps, 
                      and contributor IDs associated with each pull request message thread.
    """
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
                      r.repo_git = \'{f"https://github.com/{repo_org}/{repo_name}"}\'
                  ORDER BY
                      timestamp DESC
          """)

    prm_data = pd.read_sql(prm_query, con=engine)

    # reformat pull request message data, combine contributor ids for each pr thread
    prm_data = prm_data.groupby('pull_request_id').agg({'cntrb_id': list, 'timestamp': 'last'}).reset_index()
    # remove pr threads with only one contributor (no connection to be made)
    prm_data = prm_data[prm_data['cntrb_id'].apply(lambda x: len(x) > 1)]
    prm_data = prm_data.sort_values('timestamp', ascending=False)

    return prm_data
