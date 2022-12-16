/*
 * Average historical number of messages on closed PRs.
 * 
 * For app query, we'll be conditioning on repo_id only.
 * Then, we can sum the total from all repos in the
 * user's query set.
 * 
 * */

/*
 * average over the counts
 * */
select
	avg(prmc.message_count) as avg_message_count
from
	/*
	 * count the number of unique message ID's for each PR
	 * */
	(select
		count(distinct prmr.msg_id) message_count
	from
		augur_data.pull_requests pr,
		augur_data.pull_request_message_ref prmr,
		augur_data.repo r,
		augur_data.repo_groups rg
	where
		r.repo_group_id = rg.repo_group_id
		and rg.rg_name in ('ansible')
		and pr.repo_id = r.repo_id
		and prmr.pull_request_id = pr.pull_request_id
		and pr.pr_closed_at is not null
	group by pr.pull_request_id
	) as prmc