import pandas as pd
import json
import sqlalchemy as salc
import psycopg2
from pages.df.df_activities import engine

pr_query = salc.sql.text(f"""
/*
1. whether the PR is closed or open -> status
2. time required to close an PR -> duration
3. Only the data from 2021 (?)
4. how many days has passed since the ticket is closed -> exp decay
*/
SELECT x.repo_group_id,
		rg.rg_name,
        x.repo_id,
        x.repo_name,
		x.yearmonth,
		x.pr_created_at,
		x.pr_closed_at,
		x.pull_request_duration,
		x.close_duration,
		x.segment,
		x.exp_decay,
		count(pull_request_id) AS num,
		close_duration*count(pull_request_id) + exp_decay*count(pull_request_id) as total
		FROM(
			SELECT pull_request_id,
                    pull_requests.repo_id,
                    r.repo_name,
                    r.repo_group_id,
				    pr_src_state,
					CAST(EXTRACT(YEAR FROM pr_created_at) AS text) || '-' || CAST(EXTRACT(MONTH FROM pr_created_at) AS text) AS yearmonth,
					pull_requests.pr_created_at,
					pull_requests.pr_closed_at,
				    (pr_closed_at - pr_created_at) AS pull_request_duration,
				   CASE 
				   	WHEN pull_requests.pr_closed_at - pull_requests.pr_created_at <= INTERVAL '15 days' THEN 1
				   	WHEN pull_requests.pr_closed_at - pull_requests.pr_created_at <= INTERVAL '30 days' THEN 0.66
				   	WHEN pull_requests.pr_closed_at - pull_requests.pr_created_at <= INTERVAL '60 days' THEN 0.33
				   	WHEN pull_requests.pr_closed_at - pull_requests.pr_created_at > INTERVAL '90 days' THEN 0.1
				   	WHEN pull_requests.pr_closed_at IS NULL AND NOW() - pull_requests.pr_created_at < INTERVAL '45 days' THEN 0.5
				   	ELSE 0
				   END
				   AS close_duration,
				   CASE 
				   	WHEN pull_requests.pr_closed_at - pull_requests.pr_created_at <= INTERVAL '15 days' THEN 'Fast'
				   	WHEN pull_requests.pr_closed_at - pull_requests.pr_created_at <= INTERVAL '30 days' THEN 'Mild'
				   	WHEN pull_requests.pr_closed_at - pull_requests.pr_created_at <= INTERVAL '60 days' THEN 'Slow'
				   	WHEN pull_requests.pr_closed_at - pull_requests.pr_created_at > INTERVAL '90 days' THEN 'Stale'
				   	WHEN pull_requests.pr_closed_at IS NULL AND NOW() - pull_requests.pr_created_at < INTERVAL '45 days' THEN 'Still Open'
				   	ELSE 'Expired'
				   END
				   AS segment,
				   NOW() - pull_requests.pr_closed_at AS "time_passed",
				   CASE 
				   	WHEN NOW() - pull_requests.pr_closed_at < INTERVAL '30 days' THEN 1
				   	WHEN NOW() - pull_requests.pr_closed_at < INTERVAL '60 days' THEN 0.9
				   	WHEN NOW() - pull_requests.pr_closed_at < INTERVAL '90 days' THEN 0.9*0.9
				   	WHEN NOW() - pull_requests.pr_closed_at < INTERVAL '120 days' THEN 0.9*0.9*0.9
				   	WHEN NOW() - pull_requests.pr_closed_at < INTERVAL '150 days' THEN 0.9*0.9*0.9*0.9
				   	WHEN NOW() - pull_requests.pr_closed_at < INTERVAL '180 days' THEN 0.9*0.9*0.9*0.9*0.9
				   	WHEN NOW() - pull_requests.pr_closed_at < INTERVAL '210 days' THEN 0.9*0.9*0.9*0.9*0.9*0.9
				   	WHEN NOW() - pull_requests.pr_closed_at < INTERVAL '240 days' THEN 0.9*0.9*0.9*0.9*0.9*0.9*0.9
				   	WHEN NOW() - pull_requests.pr_closed_at < INTERVAL '270 days' THEN 0.9*0.9*0.9*0.9*0.9*0.9*0.9*0.9
				   	WHEN NOW() - pull_requests.pr_closed_at < INTERVAL '300 days' THEN 0.9*0.9*0.9*0.9*0.9*0.9*0.9*0.9*0.9
				   	WHEN NOW() - pull_requests.pr_closed_at < INTERVAL '330 days' THEN 0.9*0.9*0.9*0.9*0.9*0.9*0.9*0.9*0.9*0.9
				   	WHEN NOW() - pull_requests.pr_closed_at < INTERVAL '360 days' THEN 0.9*0.9*0.9*0.9*0.9*0.9*0.9*0.9*0.9*0.9*0.9
				   	ELSE 0
				   END
				   AS exp_decay
			FROM pull_requests
            LEFT JOIN repo r
                ON r.repo_id = pull_requests.repo_id
			WHERE pull_requests.pr_closed_at - pull_requests.pr_created_at > INTERVAL '1 hours'
			ORDER BY repo_id 
		) AS x
		left join repo_groups rg 
			on rg.repo_group_id = x.repo_group_id
	GROUP BY x.repo_id, x.repo_name, x.repo_group_id, rg.rg_name, x.yearmonth, x.segment, x.pr_created_at, x.pr_closed_at, x.pull_request_duration, close_duration, exp_decay
	order by x.repo_id

""")

def Bar_Color(i):  
    if i == 'Fast':
        return "lightgreen"
    elif i == 'Mild':
        return "blueviolet"
    elif i == 'Slow':
        return "yellow"
    elif i == 'Stale':
        return "orange"
    elif i == 'Expired':
        return "grey"

dframe_pr = pd.read_sql(pr_query, con=engine)
dframe_pr['color'] = list(map(Bar_Color, dframe_pr['segment']))


issue_query = salc.sql.text(f"""
SELECT x.repo_group_id,
		rg.rg_name,
		x.repo_id,
		x.repo_name,
		x.yearmonth,
		close_duration,
		segment,
		exp_decay,
		count(issue_id) AS num,
		close_duration*count(issue_id) + exp_decay*count(issue_id) AS total
		FROM(
			SELECT i.repo_id,
				   i.issue_id,
                    r.repo_name,
                    r.repo_group_id,
				   i.issue_state,
				   CAST(EXTRACT(YEAR FROM i.created_at) AS text) || '-' || CAST(EXTRACT(MONTH FROM i.created_at) AS text) AS yearmonth,
				   (i.closed_at - i.created_at) AS issue_close_duration,
				   CASE 
					   	WHEN i.closed_at - i.created_at <= interval '30 days' THEN 1
					   	WHEN i.closed_at - i.created_at <= interval '60 days' THEN 0.66
					   	WHEN i.closed_at - i.created_at <= interval '90 days' THEN 0.33
					   	WHEN i.closed_at - i.created_at > interval '90 days' THEN 0.1
						/* the issue that has recently been opened*/
					   	when i.closed_at IS NULL AND NOW() - i.created_at < interval '45 days' THEN 0.5
					   	ELSE 0
				   END
				   AS close_duration,
				   CASE 
				   	WHEN i.closed_at - i.created_at <= INTERVAL '30 days' THEN 'Fast'
				   	WHEN i.closed_at - i.created_at <= INTERVAL '60 days' THEN 'Mild'
				   	WHEN i.closed_at - i.created_at <= INTERVAL '90 days' THEN 'Slow'
				   	WHEN i.closed_at - i.created_at > INTERVAL '90 days' THEN 'Stale'
				   	WHEN i.closed_at IS NULL AND NOW() - i.created_at < INTERVAL '45 days' THEN 'Still Open'
				   	ELSE 'Expired'
				   END
				   AS segment,
				   i.created_at,
				   i.closed_at,
				   NOW() - i.closed_at AS "time_passed_after_closing",
				   CASE 
				   	WHEN NOW() - i.closed_at < interval '30 days' THEN 1
				   	WHEN NOW() - i.closed_at < interval '60 days' THEN 0.9
				   	WHEN NOW() - i.closed_at < interval '90 days' THEN 0.9*0.9
				   	WHEN NOW() - i.closed_at < interval '120 days' THEN 0.9*0.9*0.9
				   	WHEN NOW() - i.closed_at < interval '150 days' THEN 0.9*0.9*0.9*0.9
				   	WHEN NOW() - i.closed_at < interval '180 days' THEN 0.9*0.9*0.9*0.9*0.9
				   	WHEN NOW() - i.closed_at < interval '210 days' THEN 0.9*0.9*0.9*0.9*0.9*0.9
				   	WHEN NOW() - i.closed_at < interval '240 days' THEN 0.9*0.9*0.9*0.9*0.9*0.9*0.9
				   	WHEN NOW() - i.closed_at < interval '270 days' THEN 0.9*0.9*0.9*0.9*0.9*0.9*0.9*0.9
				   	WHEN NOW() - i.closed_at < interval '300 days' THEN 0.9*0.9*0.9*0.9*0.9*0.9*0.9*0.9*0.9
				   	WHEN NOW() - i.closed_at < interval '330 days' THEN 0.9*0.9*0.9*0.9*0.9*0.9*0.9*0.9*0.9*0.9
				   	WHEN NOW() - i.closed_at < interval '360 days' THEN 0.9*0.9*0.9*0.9*0.9*0.9*0.9*0.9*0.9*0.9*0.9
				   	ELSE 0
				   END
				   AS exp_decay
			FROM issues i
			/*WHERE EXTRACT(YEAR FROM i.closed_at) >= 2022*/
            LEFT JOIN repo r
                ON r.repo_id = i.repo_id
			WHERE i.closed_at - i.created_at > INTERVAL '1 hours'
			ORDER BY i.repo_id
			) AS x
		LEFT JOIN repo_groups rg 
			ON rg.repo_group_id = x.repo_group_id
	GROUP BY x.repo_id, x.repo_name, x.repo_group_id, rg.rg_name, x.yearmonth, x.segment, close_duration, exp_decay
	order by x.repo_id
""")

dframe_issue = pd.read_sql(issue_query, con=engine)

# iterate through the Bar_Color function to unify the color for different groups
dframe_issue['color'] = list(map(Bar_Color, dframe_issue['segment']))