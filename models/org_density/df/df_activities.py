import pandas as pd
import json
import sqlalchemy as salc
import psycopg2

with open("/home/yunlee/Desktop/config.json") as config_file:
    config = json.load(config_file)

database_connection_string = 'postgresql+psycopg2://{}:{}@{}:{}/{}'.format(
                              config['user'],
                              config['password'],
                              config['host'],
                              config['port'],
                              config['database']
                            )

dbschema='augur_data'
engine = salc.create_engine(
    database_connection_string,
    connect_args={'options': '-csearch_path={}'.format(dbschema)})


dframe = pd.DataFrame()

repo_query = salc.sql.text(f"""
SELECT x.repo_id,
       x.rg_name,
       x.repo_name,
       last_updated,
       DATE(last_updated),
       to_char(last_updated, 'DAY'),
       EXTRACT(year FROM last_updated) AS "Year",
       EXTRACT(month FROM last_updated) AS "month",
       extract(hour from last_updated) AS "hour",
       x.increase_committer,
       x.increase_pr_open,
       x.increase_commit,
       (x.increase_committer + x.increase_pr_open + x.increase_pr_close + x.increase_pr_merge + x.increase_issue + x.increase_pr + x.increase_star + x.increase_fork)*10 AS total
            FROM(
        SELECT 
            rg.repo_group_id,
            rg.rg_name,
            r.repo_id,
            r.repo_name,
            /*ri.license,*/
            CASE
                WHEN r.repo_id - lag(r.repo_id) over (order by rg.repo_group_id ASC, r.repo_id ASC, ri.last_updated) = 0 THEN 
                (ri.stars_count - lag(ri.stars_count) over (order by rg.repo_group_id ASC, r.repo_id ASC, ri.last_updated)) * 0.01
            END
                AS increase_star,
            CASE
                WHEN r.repo_id - lag(r.repo_id) over (order by rg.repo_group_id ASC, r.repo_id ASC, ri.last_updated) = 0 THEN 
                (ri.fork_count - lag(ri.fork_count) over (order by rg.repo_group_id ASC, r.repo_id ASC, ri.last_updated)) * 0.25
            END
                AS increase_fork,
            CASE
                WHEN r.repo_id - lag(r.repo_id) over (order by rg.repo_group_id ASC, r.repo_id ASC, ri.last_updated) = 0 THEN 
                (ri.watchers_count - lag(ri.watchers_count) over (order by rg.repo_group_id ASC, r.repo_id ASC, ri.last_updated)) * 0.1
            END
                AS increase_watch,
            CASE
                WHEN r.repo_id - lag(r.repo_id) over (order by rg.repo_group_id ASC, r.repo_id ASC, ri.last_updated) = 0 THEN 
                (ri.committers_count - lag(ri.committers_count) over (order by rg.repo_group_id ASC, r.repo_id ASC, ri.last_updated)) *1.5
            END
                AS increase_committer,
            CASE
                WHEN r.repo_id - lag(r.repo_id) over (order by rg.repo_group_id ASC, r.repo_id ASC, ri.last_updated) = 0 THEN 
                (ri.commit_count - lag(ri.commit_count) over (order by rg.repo_group_id ASC, r.repo_id ASC, ri.last_updated)) * 1.2
            END
                AS increase_commit,
            CASE
                WHEN r.repo_id - lag(r.repo_id) over (order by rg.repo_group_id ASC, r.repo_id ASC, ri.last_updated) = 0 THEN 
                (ri.issues_count - lag(ri.issues_count) over (order by rg.repo_group_id ASC, r.repo_id ASC, ri.last_updated)) * 1.3
            END
                AS increase_issue,
            CASE
                WHEN r.repo_id - lag(r.repo_id) over (order by rg.repo_group_id ASC, r.repo_id ASC, ri.last_updated) = 0 THEN 
                (ri.pull_request_count - lag(ri.pull_request_count) over (order by rg.repo_group_id ASC, r.repo_id ASC, ri.last_updated)) * 1.6
            END
                AS increase_pr,
            CASE
                WHEN r.repo_id - lag(r.repo_id) over (order by rg.repo_group_id ASC, r.repo_id ASC, ri.last_updated) = 0 THEN 
                (ri.pull_requests_open - lag(ri.pull_requests_open) over (order by rg.repo_group_id ASC, r.repo_id ASC, ri.last_updated)) * 1.6
            END
                AS increase_pr_open,
            CASE
                WHEN r.repo_id - lag(r.repo_id) over (order by rg.repo_group_id ASC, r.repo_id ASC, ri.last_updated) = 0 THEN 
                (ri.pull_requests_closed - lag(ri.pull_requests_closed) over (order by rg.repo_group_id ASC, r.repo_id ASC, ri.last_updated)) * 1.8
            END
                AS increase_pr_close,
            CASE
                WHEN r.repo_id - lag(r.repo_id) over (order by rg.repo_group_id ASC, r.repo_id ASC, ri.last_updated) = 0 THEN 
                (ri.pull_requests_merged - lag(ri.pull_requests_merged) over (order by rg.repo_group_id ASC, r.repo_id ASC, ri.last_updated)) * 2    
            END
                AS increase_pr_merge,
            ri.last_updated,
            CASE
                WHEN EXTRACT(YEAR FROM ri.last_updated) < 2022 THEN 'far away'
                WHEN EXTRACT(YEAR FROM ri.last_updated) >= 2022 THEN 'recent'
            END
                AS segment,
            EXTRACT(year FROM last_updated) AS "Year",
            EXTRACT(month FROM last_updated) AS "month" 
        FROM REPO r
            LEFT JOIN repo_groups rg
            ON rg.repo_group_id = r.repo_group_id
            LEFT join repo_info ri 
            on r.repo_id = ri.repo_id 
        /*where rg.rg_name = 'agroal'*/
        order by rg.repo_group_id ASC, r.repo_id ASC, ri.last_updated) AS x
""")

dframe = pd.read_sql(repo_query, con=engine)


# Fill all NA value into zero
dframe = dframe.fillna(0)
# calculating activeness percentage based on org and repo_name
df2 = dframe.groupby(['rg_name', 'repo_name']).agg({'total': 'sum'})
df3 = df2.groupby(level=0).apply(lambda x:100 * x / float(x.sum()))
df4 = df3['total'].to_frame().sort_values(by = 'total', ascending=False).reset_index()
df4 = df4[df4['total'] != 0.0]
df4 = df4.rename(columns={'rg_name':'org', 'total':'percentage'})
# df4.head()



ho = df2['total'].to_frame().reset_index()
hoo = ho.groupby(['rg_name']).agg({'total': 'sum'})
drank = hoo.reset_index()
drank.sort_values(by = 'total', ascending=False).reset_index()
drank = drank.rename(columns={'rg_name':'org', 'total':'total_activity_score'})