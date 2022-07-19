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
    select 
        x.repo_id,
        x.rg_name,
        x.repo_name,
        x.yearmonth,
        CASE
            WHEN x.repo_id - lag(x.repo_id) over (order by x.repo_group_id ASC, x.repo_id ASC, x.yearmonth) = 0 THEN 
            (x.str_avg - lag(x.str_avg) over (order by x.repo_group_id ASC, x.repo_id ASC, x.yearmonth)) * 0.01
        END 
            AS star_increment,
        CASE
            WHEN x.repo_id - lag(x.repo_id) over (order by x.repo_group_id ASC, x.repo_id ASC, x.yearmonth) = 0 THEN
            (x.cmt_avg - lag(x.cmt_avg) over (order by x.repo_group_id ASC, x.repo_id ASC, x.yearmonth)) * 1.3
        END
            AS commit_increment,
        CASE
            WHEN x.repo_id - lag(x.repo_id) over (order by x.repo_group_id ASC, x.repo_id ASC, x.yearmonth) = 0 THEN 
            (x.frk_avg - lag(x.frk_avg) over (order by x.repo_group_id ASC, x.repo_id ASC, x.yearmonth)) * 0.2
        END
            AS fork_increment,
        CASE
            WHEN x.repo_id - lag(x.repo_id) over (order by x.repo_group_id ASC, x.repo_id ASC, x.yearmonth) = 0 THEN
            (x.wth_avg - lag(x.wth_avg) over (order by x.repo_group_id ASC, x.repo_id ASC, x.yearmonth)) * 0.1
        END    
            AS watches_increment,
        CASE
            WHEN x.repo_id - lag(x.repo_id) over (order by x.repo_group_id ASC, x.repo_id ASC, x.yearmonth) = 0 THEN
            (x.cmtr_avg - lag(x.cmtr_avg) over (order by x.repo_group_id ASC, x.repo_id ASC, x.yearmonth)) *1.6
        END
            AS committer_increment,
        CASE
            WHEN x.repo_id - lag(x.repo_id) over (order by x.repo_group_id ASC, x.repo_id ASC, x.yearmonth) = 0 THEN
            (x.iss_avg - lag(x.iss_avg) over (order by x.repo_group_id ASC, x.repo_id ASC, x.yearmonth)) * 0.5
        END
            AS issue_increment,
        CASE
            WHEN x.repo_id - lag(x.repo_id) over (order by x.repo_group_id ASC, x.repo_id ASC, x.yearmonth) = 0 THEN
            (x.pulcnt_avg - lag(x.pulcnt_avg) over (order by x.repo_group_id ASC, x.repo_id ASC, x.yearmonth)) * 1 
        END
            AS pull_request_increment,
        CASE
            WHEN x.repo_id - lag(x.repo_id) over (order by x.repo_group_id ASC, x.repo_id ASC, x.yearmonth) = 0 THEN
            (x.pulpen_avg - lag(x.pulpen_avg) over (order by x.repo_group_id ASC, x.repo_id ASC, x.yearmonth)) * 1.2
        END
            AS open_pull_request_increment,
        CASE
            WHEN x.repo_id - lag(x.repo_id) over (order by x.repo_group_id ASC, x.repo_id ASC, x.yearmonth) = 0 THEN
            (x.pulcls_avg - lag(x.pulcls_avg) over (order by x.repo_group_id ASC, x.repo_id ASC, x.yearmonth)) * 1.5
        END
            AS closed_pull_request_increment,
        CASE
            WHEN x.repo_id - lag(x.repo_id) over (order by x.repo_group_id ASC, x.repo_id ASC, x.yearmonth) = 0 THEN
            (x.pulmgd_avg - lag(x.pulmgd_avg) over (order by x.repo_group_id ASC, x.repo_id ASC, x.yearmonth)) * 1.8
        END
            AS merged_pull_request_increment
    FROM
    (SELECT 
        rg.repo_group_id,
        rg.rg_name,
        r.repo_id,
        r.repo_name,
        CAST(EXTRACT(YEAR FROM last_updated) AS text) || '-' || CAST(EXTRACT(MONTH FROM last_updated) AS text) AS yearmonth,
        AVG(ri.commit_count) as cmt_avg,
        AVG(ri.stars_count) as str_avg,
        AVG(ri.fork_count) as frk_avg,
        AVG(ri.watchers_count) as wth_avg,
        AVG(ri.committers_count) as cmtr_avg,
        AVG(ri.issues_count) as iss_avg,
        AVG(ri.pull_request_count) as pulcnt_avg,
        AVG(ri.pull_requests_open) as pulpen_avg,
        AVG(ri.pull_requests_closed) as pulcls_avg,
        AVG(ri.pull_requests_merged) as pulmgd_avg
    FROM REPO r
        LEFT JOIN repo_groups rg
        ON rg.repo_group_id = r.repo_group_id
        LEFT join repo_info ri 
        on r.repo_id = ri.repo_id 
    group by rg.repo_group_id, r.repo_id, yearmonth
    order by rg.repo_group_id ASC, r.repo_id asc) as x
""")

dframe = pd.read_sql(repo_query, con=engine)


# Fill all NA value into zero
dframe = dframe.fillna(0)
dframe['total'] = dframe['star_increment'] + dframe['commit_increment'] + dframe['fork_increment'] + dframe['watches_increment'] + dframe['committer_increment'] + dframe['issue_increment'] + dframe['pull_request_increment'] + dframe['open_pull_request_increment'] + dframe['closed_pull_request_increment'] + dframe['merged_pull_request_increment']
breakdown_frame = dframe


# calculating activeness percentage based on org and repo_name
df2 = dframe.groupby(['rg_name', 'repo_name']).agg({'total': 'sum'})
df3 = df2.groupby(level=0).apply(lambda x:100 * x / float(abs(x.sum())))
df4 = df3['total'].to_frame().sort_values(by = 'total', ascending=False).reset_index()
df4 = df4[df4['total'] != 0.0]
df4 = df4.rename(columns={'rg_name':'org', 'total':'percentage'})
# df4.head()



ho = df2['total'].to_frame().reset_index()
hoo = ho.groupby(['rg_name']).agg({'total': 'sum'})
drank = hoo.reset_index()
drank.sort_values(by = 'total', ascending=False).reset_index()
drank = drank.rename(columns={'rg_name':'org', 'total':'total_activity_score'})