#!/usr/bin/env python
# coding: utf-8

# # New Contributor Analysis

# In[1]:


import psycopg2
import pandas as pd 
import sqlalchemy as salc
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import warnings
import datetime
import json
warnings.filterwarnings('ignore')

with open("../../config_temp.json") as config_file:
    config = json.load(config_file)

database_connection_string = 'postgresql+psycopg2://{}:{}@{}:{}/{}'.format(config['user'], config['password'], config['host'], config['port'], config['database'])

dbschema='augur_data'
engine = salc.create_engine(
    database_connection_string,
    connect_args={'options': '-csearch_path={}'.format(dbschema)})


# ## Control Cells - Set Variables and Filters 

# ### Repo_id Generation
# 
# The cell below is for generating repo_ids from the repo names. For this to work, the repo must already be in the database. If you want to manually assign a repo_id skip the cell below and read the comments on the next cell.

# In[2]:


#add your repo name here of the repo you want to query if known (and in the database)
repo_name_set = ['augur', 'grimoirelab']
repo_set = []

for repo_name in repo_name_set:
    repo_query = salc.sql.text(f"""
                 SET SCHEMA 'augur_data';
                 SELECT 
                    b.repo_id
                FROM
                    repo_groups a,
                    repo b
                WHERE
                    a.repo_group_id = b.repo_group_id AND
                    b.repo_name = \'{repo_name}\'
        """)

    t = engine.execute(repo_query)
    repo_id =t.mappings().all()[0].get('repo_id')
    repo_set.append(repo_id)
print(repo_set)


# ### Variable Setting
# 
# Read in line comments for guidance

# In[3]:


#Take this out of quotes if you want to manually assign a repo_id number
#repo_set = {25440, 25448}

#can be set as 'competitors' or 'repo'
#'competitors' will group graphs by type, so it is easy to compare across repos
# 'repo' will group graphs by repo so it is easy to look at all the contributor data for each repo
display_grouping = 'repo'

#if display_grouping is set to 'competitors', enter the repo ids you do no want to alias, if 'display_grouping' is set to repo the list will not effect anything
not_aliased_repos = [25300, 25290]

#group_by can be set as 'month' or 'year'
group_by = 'month'

#requirements for a contributor to be considered a repeat contributor
time = 365
num_contributions_required = 5

#specify dates for filtering
#if the end_date is in the future, the end_date will default to the current_date
begin_date = '2019-10-01'
end_date = '2020-10-31'

save_files = False


# In[4]:


#create tuple that contains all the contributor rankings needed
rank_list = []
for num in range(1, num_contributions_required + 1):
    rank_list.append(num)
rank_tuple = tuple(rank_list)


# ## Contributor and Month Data Accessing and Processing

# ### Query

# In[5]:


df = pd.DataFrame()

for repo_id in repo_set: 

    pr_query = salc.sql.text(f"""        
    

    SELECT * FROM (
        SELECT ID AS
            cntrb_id,
            A.created_at AS created_at,
            date_part('month', A.created_at::DATE) AS month,
            date_part('year', A.created_at::DATE) AS year,
            A.repo_id,
            repo_name,
            full_name,
            login,
        ACTION,
        rank() OVER (
                PARTITION BY id
                ORDER BY A.created_at ASC
            )
        FROM
            (
                (
                SELECT
                    canonical_id AS ID,
                    created_at AS created_at,
                    repo_id,
                    'issue_opened' AS ACTION,
                    contributors.cntrb_full_name AS full_name,
                    contributors.cntrb_login AS login 
                FROM
                    augur_data.issues
                    LEFT OUTER JOIN augur_data.contributors ON contributors.cntrb_id = issues.reporter_id
                    LEFT OUTER JOIN ( SELECT DISTINCT ON ( cntrb_canonical ) cntrb_full_name, cntrb_canonical AS canonical_email, data_collection_date, cntrb_id AS canonical_id 
                    FROM augur_data.contributors WHERE cntrb_canonical = cntrb_email ORDER BY cntrb_canonical 
                    ) canonical_full_names ON canonical_full_names.canonical_email = contributors.cntrb_canonical 
                WHERE
                    repo_id = {repo_id}
                    AND pull_request IS NULL 
                GROUP BY
                    canonical_id,
                    repo_id,
                    issues.created_at,
                    contributors.cntrb_full_name,
                    contributors.cntrb_login 
                ) UNION ALL
                (
                SELECT
                    canonical_id AS ID,
                    TO_TIMESTAMP( cmt_author_date, 'YYYY-MM-DD' ) AS created_at,
                    repo_id,
                    'commit' AS ACTION,
                    contributors.cntrb_full_name AS full_name,
                    contributors.cntrb_login AS login 
                FROM
                    augur_data.commits
                    LEFT OUTER JOIN augur_data.contributors ON cntrb_email = cmt_author_email
                    LEFT OUTER JOIN ( SELECT DISTINCT ON ( cntrb_canonical ) cntrb_full_name, cntrb_canonical AS canonical_email, data_collection_date, cntrb_id AS canonical_id 
                    FROM augur_data.contributors WHERE cntrb_canonical = cntrb_email ORDER BY cntrb_canonical 
                    ) canonical_full_names ON canonical_full_names.canonical_email = contributors.cntrb_canonical 
                WHERE
                    repo_id = {repo_id} 
                GROUP BY
                    repo_id,
                    canonical_email,
                    canonical_id,
                    commits.cmt_author_date,
                    contributors.cntrb_full_name,
                    contributors.cntrb_login 
                ) UNION ALL
                (
                SELECT
                    message.cntrb_id AS ID,
                    created_at AS created_at,
                    commits.repo_id,
                    'commit_comment' AS ACTION,
                    contributors.cntrb_full_name AS full_name,
                    contributors.cntrb_login AS login
      
                FROM
                    augur_data.commit_comment_ref,
                    augur_data.commits,
                    augur_data.message
                    LEFT OUTER JOIN augur_data.contributors ON contributors.cntrb_id = message.cntrb_id
                    LEFT OUTER JOIN ( SELECT DISTINCT ON ( cntrb_canonical ) cntrb_full_name, cntrb_canonical AS canonical_email, data_collection_date, cntrb_id AS canonical_id 
                    FROM augur_data.contributors WHERE cntrb_canonical = cntrb_email ORDER BY cntrb_canonical 
                    ) canonical_full_names ON canonical_full_names.canonical_email = contributors.cntrb_canonical 
                WHERE
                    commits.cmt_id = commit_comment_ref.cmt_id 
                    AND commits.repo_id = {repo_id} 
                    AND commit_comment_ref.msg_id = message.msg_id
 
                GROUP BY
                    ID,
                    commits.repo_id,
                    commit_comment_ref.created_at,
                    contributors.cntrb_full_name,
                    contributors.cntrb_login
                ) UNION ALL
                (
                SELECT
                    issue_events.cntrb_id AS ID,
                    issue_events.created_at AS created_at,
                    repo_id,
                    'issue_closed' AS ACTION,
                    contributors.cntrb_full_name AS full_name,
                    contributors.cntrb_login AS login 
                FROM
                    augur_data.issues,
                    augur_data.issue_events
                    LEFT OUTER JOIN augur_data.contributors ON contributors.cntrb_id = issue_events.cntrb_id
                    LEFT OUTER JOIN ( SELECT DISTINCT ON ( cntrb_canonical ) cntrb_full_name, cntrb_canonical AS canonical_email, data_collection_date, cntrb_id AS canonical_id 
                    FROM augur_data.contributors WHERE cntrb_canonical = cntrb_email ORDER BY cntrb_canonical 
                    ) canonical_full_names ON canonical_full_names.canonical_email = contributors.cntrb_canonical 
                WHERE
                    issues.repo_id = {repo_id} 
                    AND issues.issue_id = issue_events.issue_id 
                    AND issues.pull_request IS NULL 
                    AND issue_events.cntrb_id IS NOT NULL 
                    AND ACTION = 'closed' 
                GROUP BY
                    issue_events.cntrb_id,
                    repo_id,
                    issue_events.created_at,
                    contributors.cntrb_full_name,
                    contributors.cntrb_login 
                ) UNION ALL
                (
                SELECT
                    pr_augur_contributor_id AS ID,
                    pr_created_at AS created_at,
                    repo_id,
                    'open_pull_request' AS ACTION,
                    contributors.cntrb_full_name AS full_name,
                    contributors.cntrb_login AS login 
                FROM
                    augur_data.pull_requests
                    LEFT OUTER JOIN augur_data.contributors ON pull_requests.pr_augur_contributor_id = contributors.cntrb_id
                    LEFT OUTER JOIN ( SELECT DISTINCT ON ( cntrb_canonical ) cntrb_full_name, cntrb_canonical AS canonical_email, data_collection_date, cntrb_id AS canonical_id 
                    FROM augur_data.contributors WHERE cntrb_canonical = cntrb_email ORDER BY cntrb_canonical 
                    ) canonical_full_names ON canonical_full_names.canonical_email = contributors.cntrb_canonical 
                WHERE
                    pull_requests.repo_id = {repo_id} 
                GROUP BY
                    pull_requests.pr_augur_contributor_id,
                    pull_requests.repo_id,
                    pull_requests.pr_created_at,
                    contributors.cntrb_full_name,
                    contributors.cntrb_login 
                ) UNION ALL
                (
                SELECT
                    message.cntrb_id AS ID,
                    msg_timestamp AS created_at,
                    repo_id,
                    'pull_request_comment' AS ACTION,
                    contributors.cntrb_full_name AS full_name,
                    contributors.cntrb_login AS login 
                FROM
                    augur_data.pull_requests,
                    augur_data.pull_request_message_ref,
                    augur_data.message
                    LEFT OUTER JOIN augur_data.contributors ON contributors.cntrb_id = message.cntrb_id
                    LEFT OUTER JOIN ( SELECT DISTINCT ON ( cntrb_canonical ) cntrb_full_name, cntrb_canonical AS canonical_email, data_collection_date, cntrb_id AS canonical_id 
                    FROM augur_data.contributors WHERE cntrb_canonical = cntrb_email ORDER BY cntrb_canonical 
                    ) canonical_full_names ON canonical_full_names.canonical_email = contributors.cntrb_canonical 
                WHERE
                    pull_requests.repo_id = {repo_id}
                    AND pull_request_message_ref.pull_request_id = pull_requests.pull_request_id 
                    AND pull_request_message_ref.msg_id = message.msg_id 
                GROUP BY
                    message.cntrb_id,
                    pull_requests.repo_id,
                    message.msg_timestamp,
                    contributors.cntrb_full_name,
                    contributors.cntrb_login 
                ) UNION ALL
                (
                SELECT
                    issues.reporter_id AS ID,
                    msg_timestamp AS created_at,
                    repo_id,
                    'issue_comment' AS ACTION,
                    contributors.cntrb_full_name AS full_name,
                    contributors.cntrb_login AS login 
                FROM
                    issues,
                    issue_message_ref,
                    message
                    LEFT OUTER JOIN augur_data.contributors ON contributors.cntrb_id = message.cntrb_id
                    LEFT OUTER JOIN ( SELECT DISTINCT ON ( cntrb_canonical ) cntrb_full_name, cntrb_canonical AS canonical_email, data_collection_date, cntrb_id AS canonical_id 
                    FROM augur_data.contributors WHERE cntrb_canonical = cntrb_email ORDER BY cntrb_canonical 
                    ) canonical_full_names ON canonical_full_names.canonical_email = contributors.cntrb_canonical 
                WHERE
                    issues.repo_id = {repo_id}
                    AND issue_message_ref.msg_id = message.msg_id 
                    AND issues.issue_id = issue_message_ref.issue_id
                    AND issues.pull_request_id = NULL
                GROUP BY
                    issues.reporter_id,
                    issues.repo_id,
                    message.msg_timestamp,
                    contributors.cntrb_full_name,
                    contributors.cntrb_login 
                ) 
            ) A,
            repo 
        WHERE
        ID IS NOT NULL 
            AND A.repo_id = repo.repo_id 
        GROUP BY
            A.ID,
            A.repo_id,
            A.ACTION,
            A.created_at,
            repo.repo_name,
            A.full_name,
            A.login
        ORDER BY 
            cntrb_id
        ) b
        WHERE RANK IN {rank_tuple}

""")
    df_first_repo = pd.read_sql(pr_query, con=engine)
    if not df.empty: 
        df = pd.concat([df, df_first_repo]) 
    else: 
        # first repo
        df = df_first_repo

#end_date = pd.to_datetime(end_date)
#current_time = datetime.datetime.now()
#if end_date > current_time:
#    end_date = current_time



    
months_df = pd.DataFrame()

#months_query makes a df of years and months, this is used to fill the months with no data in the visualizaitons
months_query = salc.sql.text(f"""        
  SELECT
            *
        FROM
        (
        SELECT
            date_part( 'year', created_month :: DATE ) AS year,
            date_part( 'month', created_month :: DATE ) AS MONTH
        FROM
            (SELECT * FROM ( SELECT created_month :: DATE FROM generate_series (TIMESTAMP '{begin_date}', TIMESTAMP '{end_date}', INTERVAL '1 month' ) created_month ) d ) x 
        ) y
""")
months_df = pd.read_sql(months_query, con=engine)

#display(months_df)
display(df)


# ### Remove Bots and Only Keep Actions in Actions List

# In[6]:


df = df.loc[~df['full_name'].str.contains('bot', na=False)]
df = df.loc[~df['login'].str.contains('bot', na=False)]


# ### Add Date Data

# In[7]:


#add yearmonths to contributor
df[['month', 'year']] = df[['month', 'year']].astype(int).astype(str)
df['yearmonth'] = df['month'] + '/' + df['year']
df['yearmonth'] = pd.to_datetime(df['yearmonth'])

#add yearmonths to months_df
months_df[['year','month']] = months_df[['year','month']].astype(float).astype(int).astype(str)
months_df['yearmonth'] = months_df['month'] + '/' + months_df['year']
months_df['yearmonth'] = pd.to_datetime(months_df['yearmonth'])

#filter months_df with begin_date and end_date, the contributor df is filtered in the visualizations
months_df = months_df.set_index(months_df['yearmonth'])
months_df = months_df.loc[begin_date : end_date].reset_index(drop = True)

# add column with every value being one, so when the contributor df is concatenated with the months df, the filler months won't be counted in the sums
df['new_contributors'] = 1

#return the quarter in yearmonth form, when given a month and year
def quarters(month, year):
    if month >= 1 and month <=3:
        return '01' + '/' + year
    elif month >=4 and month <=6:
        return '04' + '/' + year
    elif month >= 5 and month <=9:
        return '07' + '/' + year
    elif month >= 10 and month <= 12:
        return '10' + '/' + year

#add quarters to contributor dataframe
df['month'] = df['month'].astype(int)
df['quarter'] = df.apply(lambda x: quarters(x['month'], x['year']), axis=1)
df['quarter'] = pd.to_datetime(df['quarter'])

#add quarters to months dataframe
months_df['month'] = months_df['month'].astype(int)
months_df['quarter'] = months_df.apply(lambda x: quarters(x['month'], x['year']), axis=1)
months_df['quarter'] = pd.to_datetime(months_df['quarter'])


# ## Repo Aliasing- ignore if not using aliases 

# In[8]:


#create a dictionairy with a number(0-26) as the key and a letter(A-Z) as the value
#this is used to alias repos when using 'competor' display grouping is specified
letters = []
nums = []
alpha = 'a'
for i in range(0, 26): 
    letters.append(alpha) 
    alpha = chr(ord(alpha) + 1)
    nums.append(i)
letters = [x.upper() for x in letters]

#create dict out of list of numbers and letters
repo_alias_dict = {nums[i]: letters[i] for i in range(len(nums))}

# create dict in the form {repo_id : repo_name}
aliased_repos = []
repo_dict = {}
count = 0
for repo_id in repo_set:
    
    #find corresponding repo name from each repo_id 
    repo_name = df.loc[df['repo_id'] == repo_id].iloc[0]['repo_name']
    
    #if competitor grouping is enabled turn all repo names, other than the ones in the 'not_aliased_repos' into an alias
    if display_grouping == 'competitors' and not repo_id in not_aliased_repos:
        repo_name =  'Repo ' + repo_alias_dict[count]
        
        #add repo_id to list of aliased repos, this is used for ordering
        aliased_repos.append(repo_id)
        count += 1
        
    #add repo_id and repo names as key value pairs into a dict, this is used to label the title of the visualizations
    repo_dict.update({repo_id : repo_name})


#gurantees that the non_aliased repos come first when display grouping is set as 'competitors'
repo_list = not_aliased_repos + aliased_repos

#gurantee that the 'repo_list' only includes repos from the main 'repo_set'
for repo_id in repo_list:
    if repo_id not in repo_set:
        repo_list.remove(repo_id)


# In[9]:


display(repo_dict)


# ## Data Visualizations 

# In[10]:


#import visualization libraries
from bokeh.io import output_notebook, show, export_png
from bokeh.plotting import figure
from bokeh.models import Label, LabelSet, ColumnDataSource, Legend
from bokeh.palettes import Colorblind
from bokeh.layouts import gridplot
from bokeh.transform import cumsum

from math import pi


# ### New Contributors Bar Charts

# In[11]:


def vertical_bar_chart(input_df, months_df, repo_id, group_by, y_axis='new_contributors', title = "{}: {} {} Time Contributors Per {}", required_contributions = 4, required_time =5  ):
    contributor_types = ['All', 'repeat', 'drive_by']
    ranks = [1]
    
    #determine if a list or integer is the input, and create a list
    if type(repo_id) == type(repo_list):
        repo_ids = repo_id
    else:
        repo_ids = [repo_id]

    for rank in ranks:
        for contributor_type in contributor_types:
            #do not display these visualizations since drive-by's do not have second contributions, and the second contribution of a repeat contributor is the same thing as the all the second time contributors
            if (rank == 2 and contributor_type == 'drive_by') or (rank == 2 and contributor_type == 'repeat'):
                continue
            #do not display these visualizations since drive-by's do not have second contributions, and the second contribution of a repeat contributor is the same thing as the all the second time contributors
            for repo_id in repo_ids:

                output_notebook()

                #create a copy of contributor dataframe
                driver_df = input_df.copy()
                
                #filter dataframe by repo_id
                driver_df = driver_df.loc[driver_df['repo_id'] == repo_id]
                
                #remove first time contributors before begin date, along with their second contribution
                mask = (driver_df['yearmonth'] < begin_date)
                driver_df= driver_df[~driver_df['cntrb_id'].isin(driver_df.loc[mask]['cntrb_id'])]
                
                
           
                #create separate repeat_df that includes all repeat contributors
                #then any contributor that is not in the repeat_df is a drive-by contributor
                repeats_df = driver_df.copy()
                
                #discards rows other than the first and the row required to be a repeat contributor
                repeats_df = repeats_df.loc[repeats_df['rank'].isin([1,required_contributions])]

                #removes all the contributors that only have a first contirbution
                repeats_df = repeats_df[repeats_df['cntrb_id'].isin(repeats_df.loc[driver_df['rank'] == required_contributions]['cntrb_id'])]
                
                #create lists of 'created_at' times for the final required contribution and the first contribution
                repeat_list = repeats_df.loc[driver_df['rank'] == required_contributions]['created_at'].tolist()
                first_list = repeats_df.loc[driver_df['rank'] == 1]['created_at'].tolist()

                #only keep first time contributions, since those are the dates needed for visualization
                repeats_df = repeats_df.loc[driver_df['rank'] == 1]

                #create list of time differences between the final required contribution and the first contribution, and add it to the df
                differences = []
                for i in range(0, len(repeat_list)):
                    time_difference = repeat_list[i] - first_list[i]
                    total = time_difference.days * 86400 + time_difference.seconds
                    differences.append(total)
                repeats_df['differences'] = differences

                #remove contributions who made enough contributions, but not in a short enough time
                repeats_df = repeats_df.loc[repeats_df['differences'] <= required_time * 86400]
                
                
                
                if contributor_type == 'repeat':
                    driver_df = repeats_df
                    
                    caption = """This graph shows repeat contributors in the specified time period. Repeat contributors are contributors who have 
                    made {} or more contributions in {} days and their first contribution is in the specified time period. New contributors 
                    are individuals who make their first contribution in the specified time period."""
                    
                elif contributor_type == 'drive_by':

                    #create list of 'cntrb_ids' for repeat contributors
                    repeat_cntrb_ids = repeats_df['cntrb_id'].to_list()
        
                    #create df with all contributors other than the ones in the repeats_df
                    driver_df = driver_df.loc[~driver_df['cntrb_id'].isin(repeat_cntrb_ids)]
                 
                    #filter df so it only includes the first contribution
                    driver_df = driver_df.loc[driver_df['rank'] == 1]
                    
                    caption = """This graph shows drive by contributors in the specified time period. Drive by contributors are contributors who 
                    make less than the required {} contributions in {} days. New contributors are individuals who make their first contribution 
                    in the specified time period. Of course, then, “All drive-by’s are by definition first time contributors”. However, not all 
                    first time contributors are drive-by’s."""
                
                
                elif contributor_type == 'All':
                    if rank == 1:
                        #makes df with all first time contributors
                        driver_df = driver_df.loc[driver_df['rank'] == 1]
                        caption = """This graph shows all the first time contributors, whether they contribute once, or contribute multiple times. 
                        New contributors are individuals who make their first contribution in the specified time period."""
                        
                    if rank == 2:
                        #creates df with all second time contributors
                        driver_df = driver_df.loc[driver_df['rank'] == 2]
                        caption = """This graph shows the second contribution of all first time contributors in the specified time period."""
                        y_axis_label = 'Second Time Contributors'
                


                #filter by end_date, this is not done with the begin date filtering because a repeat contributor will look like drive-by if the second contribution is removed by end_date filtering
                mask = (driver_df['yearmonth'] < end_date)
                driver_df = driver_df.loc[mask]

                #adds all months to driver_df so the lists of dates will include all months and years    
                driver_df = pd.concat([driver_df, months_df])

                data = pd.DataFrame()
                if group_by == 'year': 

                    data['dates'] = driver_df[group_by].unique()

                    #new contributor counts for y-axis
                    data['new_contributor_counts'] = driver_df.groupby([group_by]).sum().reset_index()[y_axis]

                    #used to format x-axis and title
                    group_by_format_string = "Year"

                elif group_by == 'quarter' or group_by == 'month':
                    
                    #set variables to group the data by quarter or month
                    if group_by == 'quarter':
                        date_column = 'quarter'
                        group_by_format_string = "Quarter"
                        
                    elif group_by == 'month':
                        date_column = 'yearmonth'
                        group_by_format_string = "Month"
                        
                    #modifies the driver_df[date_column] to be a string with year and month, then finds all the unique values   
                    data['dates'] = np.unique(np.datetime_as_string(driver_df[date_column], unit = 'M'))
                    
                    #new contributor counts for y-axis
                    data['new_contributor_counts'] = driver_df.groupby([date_column]).sum().reset_index()[y_axis]
                
                #if the data set is large enough it will dynamically assign the width, if the data set is too small it will by default set to 870 pixel so the title fits
                if len(data['new_contributor_counts']) >= 15:
                    plot_width = 46 * len(data['new_contributor_counts'])
                else:
                    plot_width = 870
                    
                #create a dict convert an integer number into a word
                #used to turn the rank into a word, so it is nicely displayed in the title
                numbers = ['Zero', 'First', 'Second']
                num_conversion_dict = {}
                for i in range(1, len(numbers)):
                    num_conversion_dict[i] = numbers[i]
                number =  '{}'.format(num_conversion_dict[rank])

                #define pot for bar chart
                p = figure(x_range=data['dates'], plot_height=400, plot_width = plot_width, title=title.format(repo_dict[repo_id].capitalize(), contributor_type.capitalize(), number, group_by_format_string), 
                           y_range=(0, max(data['new_contributor_counts'])* 1.15), margin = (0, 0, 10, 0))
                
                p.vbar(x=data['dates'], top=data['new_contributor_counts'], width=0.8)

                source = ColumnDataSource(data=dict(dates=data['dates'], new_contributor_counts=data['new_contributor_counts']))
                
                #add contributor_count labels to chart
                p.add_layout(LabelSet(x='dates', y='new_contributor_counts', text='new_contributor_counts', y_offset=4,
                          text_font_size="13pt", text_color="black",
                          source=source, text_align='center'))

                p.xgrid.grid_line_color = None
                p.y_range.start = 0
                p.axis.minor_tick_line_color = None
                p.outline_line_color = None

                p.title.align = "center"
                p.title.text_font_size = "18px"

                p.yaxis.axis_label = 'Second Time Contributors' if rank == 2 else 'New Contributors'
                p.xaxis.axis_label = group_by_format_string 

                p.xaxis.axis_label_text_font_size = "18px"
                p.yaxis.axis_label_text_font_size = "16px"

                p.xaxis.major_label_text_font_size = "16px"
                p.xaxis.major_label_orientation = 45.0

                p.yaxis.major_label_text_font_size = "16px"

                plot = p
                
                #creates plot to hold caption 
                p = figure(width = plot_width, height=200, margin = (0, 0, 0, 0))

                p.add_layout(Label(
                x = 0, # Change to shift caption left or right
                y = 160, 
                x_units = 'screen',
                y_units = 'screen',
                text='{}'.format(caption.format(num_contributions_required, time)),
                text_font = 'times', # Use same font as paper
                text_font_size = '15pt',
                render_mode='css'
                ))
                p.outline_line_color = None

                caption_plot = p

                #puts plots together into a grid
                grid = gridplot([[plot], [caption_plot]])

                show(grid)
                
                if save_files:
                    output_file = 'images/' + 'new_contributors_stacked_bar' + '_' + contributor_type + '_' + group_by + '_' + repo_dict[repo_id] + '.png'
                    export_png(grid, filename=output_file)


# In[12]:


if display_grouping == 'repo':
    vertical_bar_chart(df, months_df, repo_id = repo_set, group_by = group_by, required_contributions = num_contributions_required, required_time = time)
elif display_grouping == 'competitors':
    vertical_bar_chart(df, months_df, repo_id = repo_list, group_by = group_by, required_contributions = num_contributions_required, required_time = time)


# ### New Contributors Action Bar Charts

# In[13]:


def vertical_stacked_bar_chart(input_df, months_df, repo_id, group_by, y_axis='new_contributors', title = "{}: {} {} Time Contributors Per {}", required_contributions = 4, required_time = 5):
    
    contributor_types = ['All', 'repeat', 'drive_by']
    ranks = [1]
    
    #determine if a list or integer is the input, and create a list
    if type(repo_id) == type(repo_list):
        repo_ids = repo_id
    else:
        repo_ids = [repo_id]

    for rank in ranks:
        for contributor_type in contributor_types:
            #do not display these visualizations since drive-by's do not have second contributions, and the second contribution of a repeat contributor is the same thing as the all the second time contributors
            if (rank == 2 and contributor_type == 'drive_by') or (rank == 2 and contributor_type == 'repeat'):
                continue
            #do not display these visualizations since drive-by's do not have second contributions, and the second contribution of a repeat contributor is the same thing as the all the second time contributors
            for repo_id in repo_ids:

                output_notebook()

                #create a copy of contributor dataframe
                driver_df = input_df.copy()
                
                #filter dataframe by repo_id
                driver_df = driver_df.loc[driver_df['repo_id'] == repo_id]
                
                #remove first time contributors before begin date, along with their second contribution
                mask = (driver_df['yearmonth'] < begin_date)
                driver_df= driver_df[~driver_df['cntrb_id'].isin(driver_df.loc[mask]['cntrb_id'])]
                        
                
           
                #create separate repeat_df that includes all repeat contributors
                #then any contributor that is not in the repeat_df is a drive-by contributor
                repeats_df = driver_df.copy()
                
                #discards rows other than the first and the row required to be a repeat contributor
                repeats_df = repeats_df.loc[repeats_df['rank'].isin([1,required_contributions])]

                #removes all the contributors that only have a first contirbution
                repeats_df = repeats_df[repeats_df['cntrb_id'].isin(repeats_df.loc[driver_df['rank'] == required_contributions]['cntrb_id'])]
                
                #create lists of 'created_at' times for the final required contribution and the first contribution
                repeat_list = repeats_df.loc[driver_df['rank'] == required_contributions]['created_at'].tolist()
                first_list = repeats_df.loc[driver_df['rank'] == 1]['created_at'].tolist()

                #only keep first time contributions, since those are the dates needed for visualization
                repeats_df = repeats_df.loc[driver_df['rank'] == 1]

                #create list of time differences between the final required contribution and the first contribution, and add it to the df
                differences = []
                for i in range(0, len(repeat_list)):
                    time_difference = repeat_list[i] - first_list[i]
                    total = time_difference.days * 86400 + time_difference.seconds
                    differences.append(total)
                repeats_df['differences'] = differences

                #remove contributions who made enough contributions, but not in a short enough time
                repeats_df = repeats_df.loc[repeats_df['differences'] <= required_time * 86400]
                
                
                
                if contributor_type == 'repeat':
                    driver_df = repeats_df
                    
                    caption = """This graph shows repeat contributors in the specified time period. Repeat contributors are contributors who have 
                    made {} or more contributions in {} days and their first contribution is in the specified time period. New contributors 
                    are individuals who make their first contribution in the specified time period."""
                    
                elif contributor_type == 'drive_by':

                    #create list of 'cntrb_ids' for repeat contributors
                    repeat_cntrb_ids = repeats_df['cntrb_id'].to_list()
        
                    #create df with all contributors other than the ones in the repeats_df
                    driver_df = driver_df.loc[~driver_df['cntrb_id'].isin(repeat_cntrb_ids)]
                 
                    #filter df so it only includes the first contribution
                    driver_df = driver_df.loc[driver_df['rank'] == 1]
                    
                    caption = """This graph shows drive by contributors in the specified time period. Drive by contributors are contributors who 
                    make less than the required {} contributions in {} days. New contributors are individuals who make their first contribution 
                    in the specified time period. Of course, then, “All drive-by’s are by definition first time contributors”. However, not all 
                    first time contributors are drive-by’s."""
                
                
                elif contributor_type == 'All':
                    if rank == 1:
                        #makes df with all first time contributors
                        driver_df = driver_df.loc[driver_df['rank'] == 1]
                        caption = """This graph shows all the first time contributors, whether they contribute once, or contribute multiple times. 
                        New contributors are individuals who make their first contribution in the specified time period."""
                        
                    if rank == 2:
                        #creates df with all second time contributor
                        driver_df = driver_df.loc[driver_df['rank'] == 2]
                        caption = """This graph shows the second contribution of all first time contributors in the specified time period."""
                        y_axis_label = 'Second Time Contributors'
                


                #filter by end_date, this is not done with the begin date filtering because a repeat contributor will look like drive-by if the second contribution is removed by end_date filtering
                mask = (driver_df['yearmonth'] < end_date)
                driver_df = driver_df.loc[mask]
                


                #adds all months to driver_df so the lists of dates will include all months and years    
                driver_df = pd.concat([driver_df, months_df])
                
                actions = ['open_pull_request', 'pull_request_comment', 'commit', 'issue_closed', 'issue_opened', 'issue_comment']
                
                
                data = pd.DataFrame()
                if group_by == 'year': 

                    #x-axis dates
                    data['dates'] = driver_df[group_by].unique()
                    
                    for contribution_type in actions:
                        data[contribution_type] = pd.concat([driver_df.loc[driver_df['action'] == contribution_type], months_df]).groupby(group_by).sum().reset_index()[y_axis]

                    #new contributor counts for all actions
                    data['new_contributor_counts'] = driver_df.groupby([group_by]).sum().reset_index()[y_axis]

                    #used to format x-axis and graph title
                    group_by_format_string = "Year"

                elif group_by == 'quarter' or group_by == 'month':
                    
                    #set variables to group the data by quarter or month
                    if group_by == 'quarter':
                        date_column = 'quarter'
                        group_by_format_string = "Quarter"
                        
                    elif group_by == 'month':
                        date_column = 'yearmonth'
                        group_by_format_string = "Month"
                        
                    #modifies the driver_df[date_column] to be a string with year and month, then finds all the unique values   
                    data['dates'] = np.unique(np.datetime_as_string(driver_df[date_column], unit = 'M'))
                    
                    #new_contributor counts for each type of action
                    for contribution_type in actions:
                        data[contribution_type] = pd.concat([driver_df.loc[driver_df['action'] == contribution_type], months_df]).groupby(date_column).sum().reset_index()[y_axis]

                    #new contributor counts for all actions
                    data['new_contributor_counts'] = driver_df.groupby([date_column]).sum().reset_index()[y_axis]
                    
                    
                #if the data set is large enough it will dynamically assign the width, if the data set is too small it will by default set to 870 pixel so the title fits
                if len(data['new_contributor_counts']) >= 15:
                    plot_width = 46 * len(data['new_contributor_counts']) + 200
                else:
                    plot_width = 870
                    
                #create list of values for data source dict
                actions_df_references = []
                for action in actions:
                    actions_df_references.append(data[action])
                    
                #created dict with the actions as the keys, and the values as the values from the df
                data_source = {actions[i]: actions_df_references[i] for i in range(len(actions))} 
                data_source.update( {'dates' : data['dates'], 'New Contributor Counts': data['new_contributor_counts']} )

                colors = Colorblind[len(actions)]

                source = ColumnDataSource(data=data_source)

                #create a dict convert an integer number into a word
                #used to turn the rank into a word, so it is nicely displayed in the title
                numbers = ['Zero', 'First', 'Second']
                num_conversion_dict = {}
                for i in range(1, len(numbers)):
                    num_conversion_dict[i] = numbers[i]
                number =  '{}'.format(num_conversion_dict[rank])

                #y_max = 20
                #creates plot to hold chart
                p = figure(x_range=data['dates'], plot_height=400, plot_width = plot_width, title=title.format(repo_dict[repo_id].capitalize(), contributor_type.capitalize(), number, group_by_format_string), 
                           toolbar_location=None, y_range=(0, max(data['new_contributor_counts'])* 1.15))
                                #max(data['new_contributor_counts'])* 1.15), margin = (0, 0, 0, 0))

                vbar = p.vbar_stack(actions, x='dates', width=0.8, color=colors, source=source)

                #add total count labels
                p.add_layout(LabelSet(x='dates', y='New Contributor Counts', text='New Contributor Counts', y_offset=4, text_font_size="14pt", 
                                  text_color="black", source=source, text_align='center'))

                #add legend
                legend = Legend(items=[(date, [action]) for (date, action) in zip(actions, vbar)], location=(0, 120), label_text_font_size = "16px")
                p.add_layout(legend, 'right')


                p.xgrid.grid_line_color = None
                p.y_range.start = 0
                p.axis.minor_tick_line_color = None
                p.outline_line_color = None

                p.title.align = "center"
                p.title.text_font_size = "18px"

                p.yaxis.axis_label = 'Second Time Contributors' if rank == 2 else 'New Contributors'
                p.xaxis.axis_label = group_by_format_string 

                p.xaxis.axis_label_text_font_size = "18px"
                p.yaxis.axis_label_text_font_size = "16px"

                p.xaxis.major_label_text_font_size = "16px"
                p.xaxis.major_label_orientation = 45.0

                p.yaxis.major_label_text_font_size = "16px"

                plot = p

                #creates plot to hold caption 
                p = figure(width = plot_width, height=200, margin = (0, 0, 0, 0))

                p.add_layout(Label(
                x = 0, # Change to shift caption left or right
                y = 160, 
                x_units = 'screen',
                y_units = 'screen',
                text='{}'.format(caption.format(num_contributions_required, time)),
                text_font = 'times', # Use same font as paper
                text_font_size = '15pt',
                render_mode='css'
                ))
                p.outline_line_color = None

                caption_plot = p

                #puts plots together into a grid
                grid = gridplot([[plot], [caption_plot]])

                show(grid)
                
                if save_files:
                    output_file = 'images/' + 'new_contributors_stacked_bar' + '_' + contributor_type + '_' + group_by + '_' + repo_dict[repo_id] + '.png'
                    export_png(grid, filename=output_file)


# In[14]:


if display_grouping == 'repo':
    vertical_stacked_bar_chart(df, months_df, repo_id=repo_set, group_by = group_by, required_contributions = num_contributions_required, required_time = time)
elif display_grouping == 'competitors':
    vertical_stacked_bar_chart(df, months_df, repo_id = repo_list, group_by = group_by, required_contributions = num_contributions_required, required_time = time)


# ### Repeat and Drive By Contributor Counts Pie Chart

# In[15]:


def pie_chart(input_df, repo_id, title = " {}: Number of Returning Contributors out of {} from {} to {}", required_contributions = 4, required_time = 5):
    if type(repo_id) == type(repo_list):
        repo_ids = repo_id
    else:
        repo_ids = repo_id
        
    for repo_id in repo_ids:
        output_notebook()
        
        #create a copy of contributor dataframe
        driver_df = input_df.copy()
        
        #filter dataframe by repo_id
        driver_df = driver_df.loc[driver_df['repo_id'] == repo_id]
        
        #remove first time contributors before begin date, along with their second contribution
        mask = (driver_df['yearmonth'] < begin_date)
        driver_df= driver_df[~driver_df['cntrb_id'].isin(driver_df.loc[mask]['cntrb_id'])]

        
        #determine if contributor is a drive by by finding all the cntrb_id's that do not have a second contribution
        repeats_df = driver_df.copy()

        repeats_df = repeats_df.loc[repeats_df['rank'].isin([1,required_contributions])]

        #removes all the contributors that only have a first contirbution
        repeats_df = repeats_df[repeats_df['cntrb_id'].isin(repeats_df.loc[driver_df['rank'] == required_contributions]['cntrb_id'])]

        repeat_list = repeats_df.loc[driver_df['rank'] == required_contributions]['created_at'].tolist()
        first_list = repeats_df.loc[driver_df['rank'] == 1]['created_at'].tolist()

        repeats_df = repeats_df.loc[driver_df['rank'] == 1]
        repeats_df['type'] = 'repeat'
        
        differences = []
        for i in range(0, len(repeat_list)):
            time_difference = repeat_list[i] - first_list[i]
            total = time_difference.days * 86400 + time_difference.seconds
            differences.append(total)
        repeats_df['differences'] = differences

        repeats_df = repeats_df.loc[repeats_df['differences'] <= required_time * 86400]
        
        
        repeat_cntrb_ids = repeats_df['cntrb_id'].to_list()

        drive_by_df = driver_df.loc[~driver_df['cntrb_id'].isin(repeat_cntrb_ids)]

        drive_by_df = drive_by_df.loc[driver_df['rank'] == 1]
        drive_by_df['type'] = 'drive_by'
        
        driver_df = pd.concat([drive_by_df, repeats_df])
        
        #filter df by end date
        mask = (driver_df['yearmonth'] < end_date)
        driver_df = driver_df.loc[mask]

        #first and second time contributor counts
        drive_by_contributors = driver_df.loc[driver_df['type'] == 'drive_by'].count()['new_contributors']
        repeat_contributors = driver_df.loc[driver_df['type'] == 'repeat'].count()['new_contributors']
        
        #create a dict with the # of drive-by and repeat contributors
        x = {'Drive_By': drive_by_contributors,
             'Repeat' : repeat_contributors}
 
        #turn dict 'x' into a dataframe with columns 'contributor_type', and 'counts'
        data = pd.Series(x).reset_index(name='counts').rename(columns={'index':'contributor_type'})

        data['angle'] = data['counts']/data['counts'].sum() * 2*pi
        data['color'] = ('#0072B2', '#E69F00')
        data['percentage'] = ((data['angle']/(2*pi))*100).round(2)
        
        #format title 
        title = title.format(repo_dict[repo_id].capitalize(), drive_by_contributors + repeat_contributors, begin_date, end_date)
        title_text_font_size = 18
        
        plot_width = 850
        
        #sets plot_width to width of title if title is wider than 850 pixels
        if len(title) * title_text_font_size / 2 > plot_width:
            plot_width = int(len(title) * title_text_font_size / 2)
        
        
        source = ColumnDataSource(data)
        
        #creates plot for chart
        p = figure(plot_height=450, plot_width =plot_width, title=title, 
                   toolbar_location=None, x_range=(-0.5, 1.3), tools = 'hover', tooltips = "@contributor_type", margin = (0, 0, 0, 0))

        wedge = p.wedge(x=0.87, y=1, radius=0.4, start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'),
            line_color=None, fill_color='color', legend_field='contributor_type', source=data)

        start_point = 0.88
        for i in range(0, len(data['percentage'])):
            #percentages
            p.add_layout(Label(x=-0.17, y= start_point + 0.13*(len(data['percentage']) - 1 - i), text='{}%'.format(data.iloc[i]['percentage']), 
                        render_mode='css', text_font_size = '15px', text_font_style= 'bold'))

            #contributors
            p.add_layout(Label(x=0.12, y= start_point + 0.13*(len(data['percentage']) - 1 - i), text='{}'.format(data.iloc[i]['counts']), 
                        render_mode='css', text_font_size = '15px', text_font_style= 'bold'))

        #percentages header    
        p.add_layout(Label(x=-0.22, y= start_point + 0.13*(len(data['percentage'])), text='Percentages', render_mode='css', 
                    text_font_size = '15px', text_font_style= 'bold'))

        #legend header
        p.add_layout(Label(x=-0.43, y= start_point + 0.13*(len(data['percentage'])), text='Category', render_mode='css', 
                    text_font_size = '15px', text_font_style= 'bold'))

        #contributors header
        p.add_layout(Label(x=0, y= start_point + 0.13*(len(data['percentage'])), text='# Contributors', render_mode='css', 
                    text_font_size = '15px', text_font_style= 'bold'))

        p.axis.axis_label=None
        p.axis.visible=False
        p.grid.grid_line_color = None 
        
        p.title.align = "center"
        p.title.text_font_size = "{}px".format(title_text_font_size)
   
        p.legend.location = "center_left"
        p.legend.border_line_color = None
        p.legend.label_text_font_style = 'bold'
        p.legend.label_text_font_size = "15px"

        plot = p

        #creates plot for caption
        p = figure(width = 850, height=200, margin = (0, 0, 0, 0))
        
        caption= """This pie chart shows the percentage of new contributors who were drive-by or repeat contributors. Drive by contributors are contributors who make less than the required {0} contributions in {1} days. New contributors are 
                    individuals who make their first contribution in the specified time period. Repeat contributors are contributors who have made {0} or more contributions in {1} days and their first 
                        contribution is in the specified time period."""

        p.add_layout(Label(
        x = 0, 
        y = 160, 
        x_units = 'screen',
        y_units = 'screen',
        text='{}'.format(caption.format(num_contributions_required, time)),
        text_font = 'times', 
        text_font_size = '15pt',
        render_mode='css'
        ))
        p.outline_line_color = None

        caption_plot = p

        #put graph and caption plot together into one grid
        grid = gridplot([[plot], [caption_plot]])

        show(grid)
        
        if save_files:
            output_file = 'images/' + 'pie_chart' + '_' + repo_dict[repo_id] + '.png'
            export_png(grid, filename=output_file)


# In[16]:


if display_grouping == 'repo':
    pie_chart(df, repo_id=repo_set, required_contributions = num_contributions_required, required_time = time)
elif display_grouping == 'competitors':
    pie_chart(df, months_df, repo_id = repo_list, group_by = group_by, required_contributions = num_contributions_required, required_time = time)


# ### Repeat and Drive-by Contributor Counts Stacked Bar Chart

# In[17]:


def vertical_stacked_bar_chart_2(input_df, months_df, repo_id, group_by, y_axis='new_contributors', title = "{}: Drive By and Repeat Contributor Counts per {}", required_contributions= 5, required_time=100):

    if type(repo_id) == type(repo_list):
        repo_ids = repo_id
    else:
        repo_ids = [repo_id]

    for repo_id in repo_ids:

        output_notebook()

        #create a copy of contributor dataframe
        driver_df = input_df.copy()

        #filter dataframe by repo_id
        driver_df = driver_df.loc[driver_df['repo_id'] == repo_id]
        
        #remove first time contributors before begin date, along with their second contribution
        mask = (driver_df['yearmonth'] < begin_date)
        driver_df= driver_df[~driver_df['cntrb_id'].isin(driver_df.loc[mask]['cntrb_id'])]
        
        #determine if contributor is a drive by by finding all the cntrb_id's that do not have a second contribution
        repeats_df = driver_df.copy()

        #discards rows other than the first and the row required to be a repeat contributor
        repeats_df = repeats_df.loc[repeats_df['rank'].isin([1,required_contributions])]

        #removes all the contributors that only have a first contirbution
        repeats_df = repeats_df[repeats_df['cntrb_id'].isin(repeats_df.loc[driver_df['rank'] == required_contributions]['cntrb_id'])]

        #create lists of 'created_at' times for the final required contribution and the first contribution
        repeat_list = repeats_df.loc[driver_df['rank'] == required_contributions]['created_at'].tolist()
        first_list = repeats_df.loc[driver_df['rank'] == 1]['created_at'].tolist()

        #only keep first time contributions, since there only needs to be one instance of each 'cntrb_id' in df
        repeats_df = repeats_df.loc[driver_df['rank'] == 1]
        repeats_df['type'] = 'repeat'
        
        #create list of time differences between the final required contribution and the first contribution, and add it to the df
        differences = []
        for i in range(0, len(repeat_list)):
            time_difference = repeat_list[i] - first_list[i]
            total = time_difference.days * 86400 + time_difference.seconds
            differences.append(total)
        repeats_df['differences'] = differences

        #remove contributions who made enough contributions, but not in a short enough time
        repeats_df = repeats_df.loc[repeats_df['differences'] <= required_time * 86400]
        
        

        #create list of 'cntrb_ids' for repeat contributors
        repeat_cntrb_ids = repeats_df['cntrb_id'].to_list()

        #create df with all contributors other than the ones in the repeats_df
        drive_by_df = driver_df.loc[~driver_df['cntrb_id'].isin(repeat_cntrb_ids)]

        #filter df so it only includes the first contribution
        drive_by_df = drive_by_df.loc[driver_df['rank'] == 1]
        drive_by_df['type'] = 'drive_by'
        
        driver_df = pd.concat([drive_by_df, repeats_df, months_df])

        #filter by end_date
        mask = (driver_df['yearmonth'] < end_date)
        driver_df = driver_df.loc[mask]

        #create df to hold data needed for chart
        data = pd.DataFrame()
        if group_by == 'year': 

            #x-axis dates
            data['dates'] = driver_df[group_by].unique()
            
            data['repeat_counts'] = driver_df.loc[driver_df['type'] == 'repeat'].groupby(group_by).count().reset_index()[y_axis]
            data['drive_by_counts'] = driver_df.loc[driver_df['type'] == 'drive_by'].groupby(group_by).count().reset_index()[y_axis]

            #new contributor counts for all contributor counts
            total_counts = []
            for i in range(0, len(data['drive_by_counts'])):
                total_counts.append(data.iloc[i]['drive_by_counts'] + data.iloc[i]['repeat_counts'])
            data['total_counts'] = total_counts

            #used to format x-axis and graph title
            group_by_format_string = "Year"

            #font size of drive by and repeat labels
            label_text_font_size = "14pt"

        elif group_by == 'quarter' or group_by == 'month':

            #set variables to group the data by quarter or month
            if group_by == 'quarter':
                date_column = 'quarter'
                group_by_format_string = "Quarter"
                
            elif group_by == 'month':
                date_column = 'yearmonth'
                group_by_format_string = "Month"

            #modifies the driver_df[date_column] to be a string with year and month, then finds all the unique values   
            data['dates'] = np.unique(np.datetime_as_string(driver_df[date_column], unit = 'M'))
     
            data['drive_by_counts'] = pd.concat([driver_df.loc[driver_df['type'] == 'drive_by'], months_df]).groupby(date_column).sum().reset_index()[y_axis]
            data['repeat_counts'] = pd.concat([driver_df.loc[driver_df['type'] == 'repeat'], months_df]).groupby(date_column).sum().reset_index()[y_axis]

            #new contributor counts for all contributor types
            total_counts = []
            for i in range(0, len(data['drive_by_counts'])):
                total_counts.append(data.iloc[i]['drive_by_counts'] + data.iloc[i]['repeat_counts'])
            data['total_counts'] = total_counts

            #font size of drive by and repeat labels
            label_text_font_size = "13pt"
            
        data_source = {'Dates' : data['dates'],
                'Drive By'     : data['drive_by_counts'],
                'Repeat'       : data['repeat_counts'],
                'All'          : data['total_counts']}

        groups = ["Drive By", "Repeat"]

        colors = ['#56B4E9', '#E69F00']

        source = ColumnDataSource(data=data_source)
        
        #format title
        title_text_font_size = 18
        title = title.format(repo_dict[repo_id].capitalize(), group_by_format_string)
        
        #if the data set is large enough it will dynamically assign the width, if the data set is too small it will by default set to 780 pixel so the title fits
        if len(data['total_counts']) >= 13:
            plot_width = 46 * len(data['total_counts']) + 210
        else:
            plot_width = 780

        p = figure(x_range=data['dates'], plot_height=500, plot_width = plot_width, title=title, 
                   toolbar_location=None, y_range=(0, max(total_counts)* 1.15), margin = (0, 0, 0, 0))
        
        vbar = p.vbar_stack(groups, x='Dates', width=0.8, color=colors, source=source)

        #add total counts above bars
        p.add_layout(LabelSet(x='Dates', y='All', text='All', y_offset=8, text_font_size="14pt", 
                          text_color="black", source=source, text_align='center'))

        #add drive by count labels
        p.add_layout(LabelSet(x='Dates', y='Drive By', text='Drive By', y_offset=-22, text_font_size=label_text_font_size, 
                  text_color="black", source=source, text_align='center'))

        #add repeat count labels
        p.add_layout(LabelSet(x='Dates', y='All', text='Repeat', y_offset=-22, text_font_size=label_text_font_size, 
                  text_color="black", source=source, text_align='center'))

        #add legend
        legend = Legend(items=[(date, [group]) for (date, group) in zip(groups, vbar)], location=(0, 200), label_text_font_size = "16px")
        p.add_layout(legend, 'right')

        p.xgrid.grid_line_color = None
        p.y_range.start = 0
        p.axis.minor_tick_line_color = None
        p.outline_line_color = None

        p.title.align = "center"
        p.title.text_font_size = "{}px".format(title_text_font_size)

        p.yaxis.axis_label = '# Contributors'
        p.xaxis.axis_label = group_by_format_string 

        p.xaxis.axis_label_text_font_size = "18px"
        p.yaxis.axis_label_text_font_size = "16px"

        p.xaxis.major_label_text_font_size = "16px"
        p.xaxis.major_label_orientation = 45.0

        p.yaxis.major_label_text_font_size = "16px"

        p.legend.label_text_font_size = "20px"

        plot = p

        #add plot to hold caption
        p = figure(width = plot_width, height=200, margin = (0, 0, 0, 0))

        caption = """This graph shows the number of new contributors in the specified time period, and indicates how many were drive-by and repeat 
        contributors. Drive by contributors are contributors who make less than the required {0} contributions in {1} days. New contributors are 
        individuals who make their first contribution in the specified time period. Repeat contributors are contributors who have made {0} or more 
        contributions in {1} days and their first contribution is in the specified time period."""

        p.add_layout(Label(
        x = 0, 
        y = 160, 
        x_units = 'screen',
        y_units = 'screen',
        text='{}'.format(caption.format(num_contributions_required, time)),
        text_font = 'times', 
        text_font_size = '15pt',
        render_mode='css'
        ))
        p.outline_line_color = None

        caption_plot = p

        #put graph and caption plot together into one grid
        grid = gridplot([[plot], [caption_plot]])

        show(grid)
        
        if save_files:
            output_file = 'images/' + 'repeat_and_drive_by_stacked_bar' + '_' + group_by + '_' + repo_dict[repo_id] + '.png'
            export_png(grid, filename=output_file)


# In[18]:


if display_grouping == 'repo':
    vertical_stacked_bar_chart_2(df, months_df, repo_id = repo_set, group_by = group_by, required_contributions = num_contributions_required, required_time = time)
elif display_grouping == 'competitors':
    vertical_stacked_bar_chart_2(df, months_df, repo_id = repo_list, group_by = group_by, required_contributions = num_contributions_required, required_time = time)

