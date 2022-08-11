# DENSITY METRICS
Documentation for 2022 Summer Internship with OSPO

## Project Goal
The summer project is a side project for [Sandiego](https://github.com/sandiego-rh/sandiego) and [Explorer](https://github.com/sandiego-rh/explorer). Project Sandiego is a front-end development that gleans information from open source ecosystem data sets that help drive community and business-oriented decision-making.

The goal for my summer project - density metrics, applied statistical methods to developing algorithms to quantify GitHub log data and user data on activity, community, and performance. 

The metrics are based on activities in PR, issue, committer, etc for repositories within an organization. The goal of the project is to assist open-source community managers monitor and diagnosing community health and making actionable decisions.

## Resources
Useful metrics link:

[CHAOSS](https://chaoss.community/)

[ORBIT MODEL](https://orbitmodel.com/)

## Data Source
[AUGUR](https://github.com/chaoss/augur)

## Code
[GITHUB REPO]()

## Metrics
### Activity (-> weight)
The activity metrics aim to discover the repository activeness percentage within an organization. The features taken into the calculation are the increment in star, watch, fork, issue, PR, open PR, closed PR, commit PR, commit, and committer. By taking the above monthly average activities and comparing them with last month to determine the increase or decrease in the attribute.

Since different features indicate different importance of contribution, the following weights are given based on [ORBIT MODEL](https://orbitmodel.com/) and domain input.

- #star increment -> weight: 0.01
- #watch increment -> weight: 0.1
- #fork increment -> weight: 0.2
- #Issue increment -> weight: 0.5
- #pull request increment -> weight: 1
- #pull request open increment -> weight: 1.2
- #pull request closed increment -> weight: 1.5
- #pull request commit increment -> weight: 1.7
- #commit increment -> weight: 1.3
- #committer increment -> weight: 1.6

The percentage of the repository activity within an org determines which repository within an organization has been contributing a positive (or negative) activity. By clicking on the repo, a breakdown graph will be generated and display the breakdown of each activity, so that community managers can have a sense of whether it is the decrease in committer that is slowing down the growth of open source projects, or it is the increase in pull requests that are driving the projects, etc.

![Activity Metrics](https://user-images.githubusercontent.com/106325570/182034210-b274166e-00ad-420f-9bba-ecf9c3749db3.png)

### Communities
The community metrics aim to detect which repo in an organization is growing/ declining in the number of unique committers by month.

By clicking on the repo, a breakdown table would display the name of the committer and its affiliation followed by its location. With the number of commits by month from each committer, the community manager would be able to know whom the community is losing or how many new contributors are coming into the community, thus making impactful decisions on building a stronger community.

- Contributor
    - #committers
        - #of unique contributors
        - #of commits by committer by month

![Community Metrics](https://user-images.githubusercontent.com/106325570/182034291-666e1773-af52-4bf2-aacf-5ba82c415194.png)

### Performances (-> weight)
The performance metrics aim to discover and segment how much time an issue/pr requires from open to close, along with consideration on how much time an issue/pr has been closed (exponential decay). The more recent an issue/pr is closed, the stronger contribution to the performance; the lesser time an issue/pr requires from open to close, indicates a better performance, thus a higher weight. 

By clicking on each repo, it generates a monthly breakdown bar chart in the bottom, which gives the community manager a better sense on how the performance goes by time, whether it is turning from a fastly response repo into a stale repo or growing in speed.


- Issue from open to close duration
    - 5 groups (fast, mild, slow, stale, expired)
        - <= 30 days -> weight: 1
        - <= 60 days -> weight: 0.66
        - <= 90 days -> weight: 0.33
        - > 90 days -> weight: 0.1
        - > 365 days -> weight: 0
Issue close within an hour will be considered as bot response -> exclude

- PR from open to close duration
    - 5 groups (fast, mild, slow, stale, expired)
        - <= 15 days -> weight: 1
        - <= 30 days -> weight: 0.66
        - <= 45 days -> weight: 0.33
        - > 60 days -> weight: 0.1
        - > 365 days -> weight: 0
PR close within an hour will be considered as bot response -> exclude

- PR/ issue close exponential decay
The more recent an issue or a PR is being closed, the stronger indication it is to the performance. Thus a higher weight it has to the metric.
    - Close within 1 mo -> weight: 1
    - Close within 2 mo -> weight: 0.9
    - Close within 3 mo -> weight: 0.9*0.9
    - etc…
    - PR/ issue been closed longer than 365 days ago is no longer considered

![Performance Metrics](https://user-images.githubusercontent.com/106325570/182034322-02b8d188-9d8d-4590-9db2-9e50293fa2c1.png)

### Statistics
- Elbow method for clustering
- Normalization on time series data

### Visualization
[Dash](https://dash.plotly.com/) is an open source python framework create by plotly for creating interactive and customized web applications.

### What can be done more with the data...
- Organizational diversity (company sponsored project)