# Community Dynamics Analysis dashboard 

This dashboard is part of an enhancement project for [Project Aspen](https://github.com/oss-aspen) and [8Knot](https://github.com/oss-aspen/8Knot). 
The applet is designed with the primary objective of provided users with a comprehensive analysis of contributor behavior within their open-source project, 
presented over temporal intervals through an array of insightful visualizations.

**Authored by Maria Shevchuk, 8-10-2023**

## Dashboard Organization

    ├── components
    │    ├── network_graph
    │    │   ├── network_graph_callbacks.py         <- Callback functions for network graph component.
    │    │   ├── network_graph_layout.py            <- Layout definition for network graph component.
    │    │   └── __init__.py
    │    │
    │    ├── plots 
    │    │   ├── avg_core_intervals.py              <- Callback function and layout definition for average intervals as core plot. 
    │    │   ├── cardinality_by_type.py             <- Callback function and layout definition for cardinality by contributor type plot. 
    │    │   ├── promotions_demotions.py            <- Callback function and layout definition for promotions/demotions plot.
    │    │   ├── plots_helper.py                    <- Helper functions for plot data collection and visualization.
    │    │   └── __init__.py
    │    │
    │    └── sidebar
    │        ├── sidebar_callbacks.py               <- Callback functions for sidebar component.
    │        ├── sidebar_layout.py                  <- Layout definition for sidebar component.
    │        └── __init__.py
    │
    ├── data_utils
    │   ├── queries.py                              <- Augur queries. 
    │   └── __init__.py                            
    │
    ├── graph_utils 
    │   ├── graph_helper.py                         <- Utility functions for network graph operations.
    │   └── __init__.py
    │
    ├── __init__.py                                 <- Top-level package initialization.
    ├── app.py                                      <- Main application script that assembles the dashboard.
    └── README.md                                   <- The top-level README for developers using this project.

## Visualizations
### Contributor Network Graph 
The network graph represents the contributor connections at a given time interval. Each node represents a contributor (red =  core, blue = peripheral). The edges represent the connections between contributors. The more central a node is, the more a given contributor has contributed to the project.

Contributors are connected if:

- They've created (committed, authored) a commit together,
- They've participated in an issue thread together,
- They've participated in the same PR message series together,
- One has reviewed the other's PR.

<img width="600" alt="network_graph" src="https://github.com/mariashev/Rappel/assets/87496627/f22413ba-624d-4a1b-8758-38025e7d6f87">

### Cardinality by Contributor Type plot
This graph captures the trend of counts of core, peripheral, and new developers at each interval in the specified time frame. It also shows the total number of contributors over time. 

<img width="500" alt="cardinality_by_type" src="https://github.com/mariashev/Rappel/assets/87496627/07e61b4d-6c64-4d4a-911c-5fc7965bcdea">

### Promotions/Demotions plot
This graph captures the trend of contributors switching from peripheral to core type (promotion) and from core to peripheral (demotion).

<img width="500" alt="promotions_demotions" src="https://github.com/mariashev/Rappel/assets/87496627/38119133-9168-4ff1-bce2-fad4bb175685">

### Average Intervals as Core
This graph captures the trend of the average number of time intervals that the core contributors have served as core.

<img width="500" alt="avg_core_intervals" src="https://github.com/mariashev/Rappel/assets/87496627/7c81c052-dfb1-493c-ac7a-99110f9a574e">

## Project Definitions
|  | **Term**                                       |                          Definition                                   |
|-:|:----------------------------------------------------------------------------------------------------------------------:|:---------------------------------------------------------------------------------------------------------------------------|
| 1| Core Contributor                               | Contributors that play an essential role in developing the system <br> architecture and forming the general leadership structure, and <br>they have substantial, long-term involvement.                      |
| 2| Peripheral Contributor                         | Contributors that are typically involved in bug fixes/small <br> enhancements, and they have irregular or short-term involvement.                      |
| 3| New Contributor                                | Net new contributors, not seen in any of the previous intervals.                     |
| 4| Promotion                                      | Switching from peripheral status in previous interval to core.                           |
| 5| Demotion                                       | Switching from core status in previos interval to core. |


## How to run the app locally
1. Clone this project from GitHub in your local project directory
2. Change into the project directory
3. Add the config.json file to the same level as app.py. 

Example of config.json file:
```
{
    "connection_string": "sqlite:///:memory:",
    "database": "sandiegorh",
    "host": "chaoss.tv",
    "password": "<<Your Password>>",
    "port": 5432,
    "schema": "augur_data",
    "user": "<<Your Username>>",
    "user_type": "read_only"
}
```
4. Run `app.py`, the application should now start loading

## How to use the dashboard
1. In the sidebar, enter the information for the repository of interest (organization and name).
2. Select the time period over which you would like your data to be analysed. 
3. Select the time interval.
4. *Optional.* Select the theshold type for identifying core contributors. <br>
    Default threshold type is "elbow" and no additional input is required. <br>
    If you select "percentage" or number", specify the value: <br>
        E.g. If you would like to count the top 10% of contributors as core, select "percentage" and type 10 in the new input space. <br>
5. *Optional.* Set custom weights.  <br>
    The weight of an event signifies the relative 'importance' of the type of interaction between two contributors  <br>
    The default weights follow the [Orbit-Love model](https://orbitmodel.com/).
6. Press the `Submit` button and wait for the network graph and trend plots to load. 
7. Once the network graph is loaded you can: <br>
    a. Press the ▶️ (play) button that will begin the animation of the graph, moving along the slider one interval at a time.<br>
    b. Manually select which intervals you want to see displayed in the network graph by using the range slider. 
8. Once the trend plots are loaded you can select which metrics you wish to display/hide. 

<img width="1696" alt="dashboard" src="https://github.com/mariashev/Rappel/assets/87496627/09e3e85b-cb75-41d4-bcb1-3777b4a7238e">

## Resources
You may find the following resources helpful for this project:

|  | **Resource**                                   |                                Link                                   |
|-:|:----------------------------------------------------------------------------------------------------------------------:|:---------------------------------------------------------------------------------------------------------------------------|
| 1| Augur (Data Source)                            | [Click Here](https://github.com/chaoss/augur)                         |
| 2| CHAOSS                                         | [Click Here](https://chaoss.community/)                               |
| 3| Dash                                           | [Click Here](https://dash.plotly.com/)                                |
| 4| Orbit-Love model                               | [Click Here](https://orbitmodel.com/)                                 |
| 5| Dashboard Demo                                 | [Click Here](https://drive.google.com/file/d/1V6VL5WOKShKlvsDUJ6TrDum1wqgcGDrn/view?usp=drive_link) |


