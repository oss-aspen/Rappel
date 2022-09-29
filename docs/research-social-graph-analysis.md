# Project ideas for Social Graph Analysis

The goal of this project is to determine the connections between open source projects, determine project clusters, and map out technology ecosystems.

This document lists several possible mini-projects or approaches that can be taken to make progress towards our eventual goal.


1. **NetworkX for community detection**
    * **Motivation**
        * Represent the GitHub dataset as a graph using the [NetworkX](https://www.kirenz.com/post/2019-08-13-network_analysis/).
    * **Possible Approaches:**
        * Define edges and nodes and construct a network using the NetworkX framework.
            * Try various graph representations eg:
                1. Nodes: projects, Edges: shared contributors
                2. Nodes: contributors, Edges: no. of shared projects/ events (like forks, watches, code contribution, membership)
                3. Nodes: Projects and contributors, Edges: interactions (pr, issue, comment, etc.)
                   Since Projects themselves don't interact w/ contributors, we can make the heuristic that projects \in \set (outdeg(V = repo ) == 0). Likewise it lets us learn the weight of interactions (comment replying, liking, pr'ing, etc) in our graph representation.
            * Recommendations/clustering etc Given a known project, what are other interesting projects.
            * Use Girvan Newman algorithm to detect new communities, [influential users](https://github.com/Dhanya-Abhirami/Social-Network-Analysis-of-Github-Users) etc

2. **Discover interesting projects from issue mentions and cross-linked issues**
    * **Motivation**
        * Discover new projects through cross-linking in issues
    * **Assumption**
        * Increased cross linking between a commonly known or an important project and a lesser known project may indicate interest in the new project.
        * Assuming our Augur database consists of only a subset of all repositories that exists on GitHub, this approach helps us broaden the scope of that project space and organically discover new important projects to load into the Augur database.
    * **Possible Approaches:**
        * Discover : Out of all issues across projects, find cross-linking issues (issue, [repo1, repo2, repo3, …]).
            * In order to parse linked issues from an existing issue, we could parse through comments on the issue and apply techniques like regex and filter out linked issues by using keywords and extracting events.
        * Define: Define well-known projects by some category/threshold (eg: >x contributors, activity status)
        * Filter: Filter those issues which have well known projects in their list of repositories [repo1, repo2, repo3, …]
        * Compare: If in the list of repositories there are projects which do not categorize as well-known then compare contributors. 
            * Determine a project’s contributors from membership in github org/contribution metrics
            * Compare and see overlap in list of contributors across this projects
            * If there is an overlap, and the project falls under a certain category (new, undiscovered, recently active etc TBD) then categorize project as interesting project
        * Rank: We can alternatively design this tool to filter projects by looking at shared contributors or individuals amongst projects. From there, we can rank “project importances” by looking at issue cross-links.

3. **GraphSAGE for link prediction and new project discovery**
    * **Motivation**
        * Represent the GitHub dataset as a graph using the [GraphSAGE framework](http://snap.stanford.edu/snappy/index.html). 
    * **Possible Approaches:**
        * Evaluate the appropriate graph representation/representation learning technique to be used.
        * Learn node interdependencies. Predict neighboring nodes.
        * Predict linkages between nodes - eg. same approach as recommendation engines for e-commerce websites - HITS algorithm - [Paper](https://springerplus.springeropen.com/articles/10.1186/s40064-016-2897-7)
        * Clustering of nodes to discover interesting patterns/outlier nodes. 
        * In order to limit the data space, one idea is to filter repositories by category
            * A project can be defined in various ways, it could be determined by language of code, readmes.

4. **Influential community detection using HITS**
    * **Motivation**
        * Use HITS (Hyperlink-Induced Topic Search) algorithm for repository influence analysis by establishing star relationship between GitHub users and repositories
    * **Possible Approaches**
        * Base work on the [paper](https://springerplus.springeropen.com/articles/10.1186/s40064-016-2897-7) where authors use weighted HITS where features within a GitHub repository such as the following are used as weights.
            * user creation event
            * repository creation event
            * commit event
            * fork event
            * star event


## Resources


* [https://towardsdatascience.com/graph-embeddings-the-summary-cc6075aba007](https://towardsdatascience.com/graph-embeddings-the-summary-cc6075aba007)
* Github’s dependency graphs - [https://docs.github.com/en/code-security/supply-chain-security/understanding-your-software-supply-chain/exploring-the-dependencies-of-a-repository](https://docs.github.com/en/code-security/supply-chain-security/understanding-your-software-supply-chain/exploring-the-dependencies-of-a-repository)
* Project-to-vec - [https://developers.redhat.com/articles/2021/10/06/find-and-compare-python-libraries-project2vec#finding_matching_projects](https://developers.redhat.com/articles/2021/10/06/find-and-compare-python-libraries-project2vec#finding_matching_projects)  
* NetworkX
    * [https://www.kirenz.com/post/2019-08-13-network_analysis/](https://www.kirenz.com/post/2019-08-13-network_analysis/)
    * [https://towardsdatascience.com/social-network-analysis-from-theory-to-applications-with-python-d12e9a34c2c7](https://towardsdatascience.com/social-network-analysis-from-theory-to-applications-with-python-d12e9a34c2c7)
    * [https://github.com/Dhanya-Abhirami/Social-Network-Analysis-of-Github-Users](https://github.com/Dhanya-Abhirami/Social-Network-Analysis-of-Github-Users)
    * [https://medium.com/@gokulkarthikk/github-social-network-analysis-28f72b2f5e3](https://medium.com/@gokulkarthikk/github-social-network-analysis-28f72b2f5e3)
    * 
* [Gephi](https://gephi.org/users/download/)
    * [https://towardsdatascience.com/how-to-get-started-with-social-network-analysis-6d527685d374](https://towardsdatascience.com/how-to-get-started-with-social-network-analysis-6d527685d374)
    * 
* HITS algorithm for influence analysis of GitHub repositories
    * [https://springerplus.springeropen.com/articles/10.1186/s40064-016-2897-7](https://springerplus.springeropen.com/articles/10.1186/s40064-016-2897-7)
* Usage of graph as a series of events 
    * https://arxiv.org/abs/2006.10637