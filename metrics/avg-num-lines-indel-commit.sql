/*
 * Average number of lines inserted/deleted per commit in a group.
 * 
 * For app query, we'll be conditioning on repo_id only.
 * Then, we can sum the total from all repos in the
 * user's query set.
 * 
 * */
select 
	round(avg(l_delta.lines_added), 2) as avg_lines_added, round(avg(l_delta.lines_removed), 2) as avg_lines_removed
from
	/*
	 * For each commit, get the total number of lines added/removed across all files in commit.
	 * */
	(select
		sum(c.cmt_added) as lines_added, sum(c.cmt_removed) as lines_removed
	from
		augur_data.commits c,
		augur_data.repo r,
		augur_data.repo_groups rg
	where
		r.repo_group_id = rg.repo_group_id
		and rg.rg_name in ('ansible')
		and c.repo_id = r.repo_id
	group by c.cmt_commit_hash) as l_delta