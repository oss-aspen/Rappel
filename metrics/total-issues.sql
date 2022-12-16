/*
 * Total number of open issues in group.
 * 
 * For app query, we'll be conditioning on repo_id only.
 * Then, we can sum the total from all repos in the
 * user's query set.
 * 
 * */

select
	count(distinct i.issue_id) as num_issues
from
	augur_data.issues i,
	augur_data.repo r,
	augur_data.repo_groups rg
where
	r.repo_group_id = rg.repo_group_id
	and rg.rg_name in ('ansible')
	and i.repo_id = r.repo_id