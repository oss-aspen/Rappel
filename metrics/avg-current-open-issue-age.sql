/*
 * Average age of issues that are currently open.
 * 
 * For app query, we'll be conditioning on repo_id only.
 * Then, we can sum the total from all repos in the
 * user's query set.
 * 
 * */

select
	avg(now() - i.created_at) as difference
from
	augur_data.issues i,
	augur_data.repo r,
	augur_data.repo_groups rg
where
	r.repo_group_id = rg.repo_group_id
	and rg.rg_name in ('ansible')
	and i.repo_id = r.repo_id
	and i.closed_at is null