import pandas as pd
import json
import sqlalchemy as salc
import psycopg2
from df.df_activities import engine

df_pr_committers = pd.DataFrame()
df_pr_authors = pd.DataFrame()
'''
committer_query = salc.sql.text(f"""
    SELECT x.rg_name,
            x.repo_id,
            x.repo_name,
            x.yearmonth,
            COUNT(x.cmt_id) AS num_of_commit,
            COUNT(DISTINCT x.cmt_committer_raw_email) AS num_of_unique_commit
        FROM(
            SELECT rg.rg_name,
                    c.repo_id,
                    r.repo_name,
                    c.cmt_id,
                    c.cmt_committer_raw_email,
                    CAST(EXTRACT(YEAR FROM cmt_committer_timestamp) AS text) || '-' || CAST(EXTRACT(MONTH FROM cmt_committer_timestamp) AS text) AS yearmonth
            FROM commits c 
            LEFT JOIN repo r
                ON c.repo_id = r.repo_id
            left join repo_groups rg
                on r.repo_group_id = rg.repo_group_id
            WHERE c.repo_id is not null
                AND c.cmt_committer_date >= '2018-01-01'
            ORDER BY r.repo_group_id, c.repo_id
            ) as x
        GROUP BY x.yearmonth, x.rg_name, x.repo_id, x.repo_name
    ORDER BY x.rg_name, x.repo_id, x.yearmonth
""")


author_query = salc.sql.text(f"""
    SELECT x.rg_name,
            x.repo_id,
            x.repo_name,
            x.yearmonth,
            COUNT(x.cmt_id) AS num_of_author,
            COUNT(DISTINCT x.cmt_author_raw_email) AS num_of_unique_author
        FROM(
            SELECT rg.rg_name,
                    c.repo_id,
                    r.repo_name,
                    c.cmt_id,
                    c.cmt_author_raw_email,
                    CAST(EXTRACT(YEAR FROM c.cmt_author_timestamp) AS text) || '-' || CAST(EXTRACT(MONTH FROM c.cmt_author_timestamp) AS text) AS yearmonth
            FROM commits c 
            LEFT JOIN repo r
                ON c.repo_id = r.repo_id
            left join repo_groups rg
                on r.repo_group_id = rg.repo_group_id
            WHERE c.repo_id is not null
                AND c.cmt_author_date >= '2018-01-01'
            ORDER BY r.repo_group_id, c.repo_id
            ) as x
        GROUP BY x.yearmonth, x.rg_name, x.repo_id, x.repo_name
    ORDER BY x.rg_name, x.repo_id, x.yearmonth
""")

df_pr_committers = pd.read_sql(committer_query, con=engine)
# df_pr_authors = pd.read_sql(author_query, con=engine)

'''