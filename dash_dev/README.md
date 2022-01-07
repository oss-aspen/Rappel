Use the Dockerfile to build a Docker image in which we can run
a Dash dashboard server.

Use "$./build.sh" to build the image locally.
    This will move the current folder into the Docker container,
    install pip3 from the dnf servers,
    download the required Python libraries to run dash_app.py,
    and run dash_app.py exposed on port 8050 via localhost.

Use "$./run.sh" to run the docker container for Dash from the docker image.

Navigate to http://0.0.0.0:8050/ in your browser to see the output. 
