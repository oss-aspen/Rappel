/*
 * Tags on issues, ordered by count.
 * 
 * For app query, we'll be conditioning on repo_id only.
 * Then, we can sum the total from all repos in the
 * user's query set.
 * 
 * */

select
	il.label_text, count(*) as label_count
from
	augur_data.issues i,
	augur_data.issue_labels il,
	augur_data.repo r,
	augur_data.repo_groups rg
where
	r.repo_group_id = rg.repo_group_id
	and rg.rg_name in ('ansible')
	and i.repo_id = r.repo_id
	and i.issue_id = il.issue_id 
group by il.label_text
order by label_count desc