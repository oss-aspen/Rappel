FROM python:3.8.12-bullseye 
LABEL James Kunstle <jkunstle@redhat.com>
COPY . /dash_app
RUN pip3 install -r /dash_app/requirements.txt
EXPOSE 8050
WORKDIR /dash_app
CMD python3 dash_app.py
