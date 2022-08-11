import pandas as pd
import numpy as np
import json
import sqlalchemy as salc
import psycopg2
from pages.df.df_activities import engine

df_pr_committers = pd.DataFrame()

committer_query = salc.sql.text(f"""
/*
1. Join contributors, repo, and repo_groups to get the repo_name, org_name
2. Extract and cast timestamp to year-monthly level
3. Exclude committers from Red Hat (by identifying their company)
4. Exclude committers that are likely to be bot (by identifying their name and contribution time inteval)
5. Get the number of unique committor of an org/repo, along with the committor's info (name, location, company)
6. Current query sets a manual condition to capture only the data since 2022. Future modification needed.
*/
    SELECT x.rg_name,
            x.repo_id,
            x.repo_name,
            x.yearmonth,
            x.cmt_committer_name,
            x.cmt_committer_raw_email,
            x.cntrb_company,
            x.cntrb_location,
            COUNT(x.cmt_id) AS num_of_commit,
            COUNT(DISTINCT x.cmt_committer_raw_email) AS num_of_unique_commit
        FROM(
            SELECT rg.rg_name,
                    c.repo_id,
                    r.repo_name,
                    c.cmt_id,
                    c.cmt_committer_name,
                    c.cmt_committer_raw_email,
                    cntrb.cntrb_company,
                    cntrb.cntrb_location,
                    CAST(EXTRACT(YEAR FROM cmt_committer_timestamp) AS text) || '-' || CAST(EXTRACT(MONTH FROM cmt_committer_timestamp) AS text) AS yearmonth
            FROM commits c 
            LEFT JOIN repo r
                ON c.repo_id = r.repo_id
            LEFT JOIN repo_groups rg
                ON r.repo_group_id = rg.repo_group_id
            LEFT JOIN contributors cntrb
                ON c.cmt_ght_author_id = cntrb.cntrb_id
            WHERE c.repo_id is not null
                AND c.cmt_committer_date > '2022-01-01'
                /*AND c.cmt_committer_name != 'Javadoc Publisher'
                AND c.cmt_committer_name != 'github-actions[bot]'
                AND c.cmt_committer_name != 'GitHub'
                AND c.cmt_committer_name != 'ohip_automation_bot'
                AND c.cmt_committer_name != 'Openshift'*/
                AND c.cmt_ght_author_id IS NOT NULL
            ORDER BY r.repo_group_id, c.repo_id, c.cmt_author_timestamp
            ) as x
        GROUP BY x.yearmonth, x.rg_name, x.repo_id, x.repo_name, x.cmt_committer_name, x.cmt_committer_raw_email, x.cntrb_company, x.cntrb_location
    ORDER BY x.rg_name, x.repo_id, x.yearmonth
""")


df_pr_committers = pd.read_sql(committer_query, con=engine)
