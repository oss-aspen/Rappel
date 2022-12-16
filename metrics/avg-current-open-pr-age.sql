/*
 * Average age of PR's that are currently open
 * 
 * For app query, we'll be conditioning on repo_id only.
 * Then, we can sum the total from all repos in the
 * user's query set.
 * 
 * */

select
	avg(now() - pr.pr_created_at) as difference
from
	augur_data.pull_requests pr,
	augur_data.repo r,
	augur_data.repo_groups rg
where
	r.repo_group_id = rg.repo_group_id
	and rg.rg_name in ('ansible')
	and pr.repo_id = r.repo_id
	and pr.pr_closed_at is null