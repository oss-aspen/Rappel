FROM python:3.8.12-bullseye 
LABEL James Kunstle <jkunstle@redhat.com>
EXPOSE 8050
WORKDIR /dash_app
COPY ./requirements.txt /dash_app
RUN pip3 install -r /dash_app/requirements.txt
CMD python3 dash_app.py
