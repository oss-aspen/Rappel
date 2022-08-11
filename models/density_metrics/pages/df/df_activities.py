import pandas as pd
import json
import sqlalchemy as salc
import psycopg2

with open("../config.json") as config_file:
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
/*
In subquery x, left join repo table, repo_groups table, and repo_info table to get the repo org and repo name.

Compute the average value for number of stars, number of commits, etc based on repo org, repo, and month of the year.
In the main select statement, the CASE WHEN condition set to compares the previous row only if within the same repo_id;
the statement is ordered in chronology order so that the window function captures the increase or decrease in 
average number of stars, average number of commits, etc compared to previous month in record.

Adding the increase/decrease in average number of star, and average number of commits, etc times the assigned weight
all together will be the final activity score for a repository.
*/ 

with pr_table as(
select 
	r.repo_id,
	r.repo_name,
	rg.rg_name,
	count(pr.pr_created_at) as pr_count,
	count(pr.pr_closed_at) as pr_closed_count,
	count(pr.pr_merged_at) as pr_merged_count,
	CAST(EXTRACT(YEAR FROM pr.pr_created_at) AS int) as pr_year,
	CAST(EXTRACT(MONTH FROM pr.pr_created_at) AS int) as pr_month
from augur_data.repo r 
	left join augur_data.pull_requests pr 
		on r.repo_id = pr.repo_id 
	left join augur_data.repo_groups rg 
		on r.repo_group_id = rg.repo_group_id
	group by r.repo_id, rg.rg_name, pr_year, pr_month
	order by rg.rg_name, r.repo_id, pr_year, pr_month
),
issue_table as(
select 
	r.repo_id,
	r.repo_name,
	count(*) as issue_count,
	CAST(EXTRACT(YEAR FROM i.created_at) AS int) as issue_year,
	CAST(EXTRACT(MONTH FROM i.created_at) AS int) as issue_month
from augur_data.repo r 
	left join augur_data.issues i 
		on r.repo_id = i.repo_id 
	group by r.repo_id, issue_year, issue_month
	order by r.repo_id, issue_year, issue_month),
cmt_table as(
select 
	r.repo_id,
	r.repo_name,
	count(*) as commit_count,
	CAST(EXTRACT(YEAR FROM cmt_committer_timestamp) AS int) as c_year,
	CAST(EXTRACT(MONTH FROM cmt_committer_timestamp) AS int) as c_month
from augur_data.repo r 
	left join augur_data.commits c 
		on r.repo_id = c.repo_id
	group by r.repo_id, c_year, c_month
	order by r.repo_id, c_year, c_month)
select 
	pr_table.rg_name,
	pr_table.repo_id,
	pr_table.repo_name,
	pr_table.pr_year,
	pr_table.pr_month,
	concat(pr_table.pr_year, '-' , pr_table.pr_month) AS pr_yearmonth,
	pr_table.pr_count,
	pr_table.pr_closed_count,
	pr_table.pr_merged_count,
	issue_table.issue_count,
	/*cmt_table.commit_count,*/
    /*CASE
        WHEN pr_table.repo_id - lag(pr_table.repo_id) over (order by pr_table.rg_name ASC, pr_table.repo_id ASC) = 0 THEN
        (cmt_table.commit_count - lag(cmt_table.commit_count) over (order by pr_table.rg_name ASC, pr_table.repo_id ASC)) * 1.3
    END
        AS commit_increment,*/
    CASE
        WHEN pr_table.repo_id - lag(pr_table.repo_id) over (order by pr_table.rg_name ASC, pr_table.repo_id ASC) = 0 THEN
        (issue_table.issue_count - lag(issue_table.issue_count) over (order by pr_table.rg_name ASC, pr_table.repo_id ASC)) * 0.5
    END
        AS issue_increment,
    CASE
        WHEN pr_table.repo_id - lag(pr_table.repo_id) over (order by pr_table.rg_name ASC, pr_table.repo_id ASC) = 0 THEN
        (pr_table.pr_count - lag(pr_table.pr_count) over (order by pr_table.rg_name ASC, pr_table.repo_id ASC)) * 1
    END
        AS pr_increment,
    CASE
        WHEN pr_table.repo_id - lag(pr_table.repo_id) over (order by pr_table.rg_name ASC, pr_table.repo_id ASC) = 0 THEN
        (pr_table.pr_closed_count - lag(pr_table.pr_closed_count) over (order by pr_table.rg_name ASC, pr_table.repo_id ASC)) * 1.5
    END
        AS closed_pr_increment,
    CASE
        WHEN pr_table.repo_id - lag(pr_table.repo_id) over (order by pr_table.rg_name ASC, pr_table.repo_id ASC) = 0 THEN
        (pr_table.pr_merged_count - lag(pr_table.pr_merged_count) over (order by pr_table.rg_name ASC, pr_table.repo_id ASC)) * 1.8
    END
        AS merged_pr_increment,
    /*CASE
        WHEN pr_table.repo_id - lag(pr_table.repo_id) over (order by pr_table.rg_name ASC, pr_table.repo_id ASC) = 0 THEN
        (cmt_table.commit_count - lag(cmt_table.commit_count) over (order by pr_table.rg_name ASC, pr_table.repo_id ASC))
    END
        AS commit_increment_number,*/
    CASE
        WHEN pr_table.repo_id - lag(pr_table.repo_id) over (order by pr_table.rg_name ASC, pr_table.repo_id ASC) = 0 THEN
        (issue_table.issue_count - lag(issue_table.issue_count) over (order by pr_table.rg_name ASC, pr_table.repo_id ASC))
    END
        AS issue_increment_number,
    CASE
        WHEN pr_table.repo_id - lag(pr_table.repo_id) over (order by pr_table.rg_name ASC, pr_table.repo_id ASC) = 0 THEN
        (pr_table.pr_count - lag(pr_table.pr_count) over (order by pr_table.rg_name ASC, pr_table.repo_id ASC))
    END
        AS pr_increment_number,
    CASE
        WHEN pr_table.repo_id - lag(pr_table.repo_id) over (order by pr_table.rg_name ASC, pr_table.repo_id ASC) = 0 THEN
        (pr_table.pr_closed_count - lag(pr_table.pr_closed_count) over (order by pr_table.rg_name ASC, pr_table.repo_id ASC))
    END
        AS closed_pr_increment_number,
    CASE
        WHEN pr_table.repo_id - lag(pr_table.repo_id) over (order by pr_table.rg_name ASC, pr_table.repo_id ASC) = 0 THEN
        (pr_table.pr_merged_count - lag(pr_table.pr_merged_count) over (order by pr_table.rg_name ASC, pr_table.repo_id ASC))
    END
        AS merged_pr_increment_number
from pr_table
	left join issue_table
		on pr_table.repo_id = issue_table.repo_id
			and pr_table.pr_year = issue_table.issue_year
			and pr_table.pr_month = issue_table.issue_month
	left join cmt_table
		on pr_table.repo_id = cmt_table.repo_id
			and pr_table.pr_year = cmt_table.c_year
			and pr_table.pr_month = cmt_table.c_month
order by pr_table.repo_id, pr_table.repo_name, pr_table.pr_year, pr_table.pr_month   
""")

dframe = pd.read_sql(repo_query, con=engine)


# Fill all NA value into zero
dframe = dframe.fillna(0)

# create a total column
dframe['total'] = dframe['issue_increment'] + dframe['pr_increment']  + dframe['closed_pr_increment'] + dframe['merged_pr_increment']

# create a breakdown frame for the breakdown chart
breakdown_frame = dframe


# calculating activeness percentage based on org and repo_name
dframe_group = dframe.groupby(['rg_name', 'repo_name']).agg({'total': 'sum'})
dframe_perc = dframe_group.groupby(level=0).apply(lambda x:100 * x / float(abs(x.sum())))
dframe_perc = dframe_perc['total'].to_frame().sort_values(by = 'total', ascending=False).reset_index()

# exclude the repo that has no total value and rename the columns
dframe_perc = dframe_perc[dframe_perc['total'] != 0.0]
dframe_perc = dframe_perc.rename(columns={'rg_name':'org',
                                            'repo_name':'repo',
                                            'total':'percentage'})



