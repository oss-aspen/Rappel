Project Sandiego will discover information from open source-ecosystem datasets that can help drive community- and business-oriented decision making for users around community health and sustainability. Sandiego will enable contributors and observers to ask questions and make data-informed decisions about open source projects and communities, as well as enable organization make clearer decisions about investing resources into new and existing open source projects.

## Mission

The mission of this project is to be able to create a system to:

* Monitor the health and sustainability of individual open source projects
* Identify and monitor projects within the surrounding ecosystem to identify issues

This will be an external upstream service-oriented tool to enable users from across the business units and open source communities to view trends and answer questions about the at-large open source ecosystem. This will be a web-based service offered to anyone interested in open source projects, providing on-demand generated statistics about “the state of open source,” and the ability to be able to look at the health of the projects that individuals are involved in.

## Deliverables

For deliverables, Project Sandiego will be split into two open source stages: the data explorer and the dataset.

### Data Explorer

The data explorer will provide an interactive user experience for connecting and displaying open source project metrics from various sources. Users will be able to choose from multiple different search criteria options for this dashboard style tool.

Potential search options for the dashboard:

* A single git-based repository (repo)
* All repos associated with a certain project
* Project networks and sector ecosystems (sector ecosystems listed below)
* Projects associated with organizations

Project networks are defined as a set of projects that directly align and connect with a given project through dependencies or contributor relationships. Sector ecosystems are much broader in scope, and are defined as a collection of projects that fall within a given technology sector, such as:

* Management
* Security
* Networking
* Observability
* AI/ML
* AIOps
* Back-up/recovery
* Database DevOps

When searching by project, each metric will have an aggregate comparison to their sector ecosystem by value and graded scale. This will be used to determine an overall health analysis of the project. Watson Debater will also be used to analyze the project’s internal dynamics, compared to similar projects in the sector ecosystem.

(An important note to this project feature: the IBM Watson Debater has an argument analyzer that will give specific pros and cons around any of these search topics, which is much more specific than traditional sentiment analysis.)

The data sources that will generate the metrics for the dashboard:

* Augur (Github data collection software suite from the CHAOSS project)
* Cauldron (Github data collection software based on Kibana and OpenElastic)
* Meetup data
* Social media content of OSS “influencers” (analysts, experts, known innovators)
* Conference data
* Open Source Security Foundation scorecard
* Project communication channels (mailing lists, chat channels, etc.)

From the dashboard, there may be some user response to the analysis to help develop the grouping algorithm for sector ecosystems and train any prediction models.

### Dataset

The dataset will be a snapshot of all the open source projects that are vaguely related to enterprise software.

Beginning with the Augur tool, the connection points (common contributors, orgs, etc.) will be used to build connected searches between projects. This will build the expanding project network of open source projects from their relationships with one another.

From the preliminary crawling points, there will be a “trial and error” checking phase of projects, especially suspected outliers, on if they are included in the currently detected project network. As outliers are detected, it will be determined what new connection point that should be crawled from for the set of projects related to those detected outliers are included. This will be repeated multiple times until the best-fit project network is generated.

This network of open source projects will be generated into a dataset for broader examinations of the open source ecosystem. The connection points found will be periodically checked monthly to add the new projects as they are created and discovered.

### Community

Because of the wide scope of Sandiego, we will have an opportunity to provide some of the information we find (such as within the dashboards) in a broader community upstream aspect of the project. 

## Project roles

Project Sandiego will be led by the OSPO Community Insights team, with Cali Dolfi as the project lead.

This project will depend on cross-team help throughout Red Hat. These are the following skillsets that we have identified as needed:

* Data Science/Machine Learning support
* Front end/data visualization
* AIOps/Dev Ops
* Data engineering
* Database integration expertise

## Repos/code/project

Repo: [https://github.com/OSAS/sandiego](https://github.com/OSAS/sandiego)
