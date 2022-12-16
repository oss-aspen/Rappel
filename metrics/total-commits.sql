/*
 * Total number of distinct commits in group.
 * 
 * For app query, we'll be conditioning on repo_id only.
 * Then, we can sum the total from all repos in the
 * user's query set.
 * 
 * */

select
	/*commit_hash'es are unique per commit*/
	count(distinct c.cmt_commit_hash) as num_commits
from 
	augur_data.commits c,
	augur_data.repo r,
	augur_data.repo_groups rg
where
	r.repo_group_id = rg.repo_group_id
	and rg.rg_name in ('ansible')
	and c.repo_id = r.repo_id