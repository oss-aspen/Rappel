FROM fedora:34
MAINTAINER James Kunstle <jkunstle@redhat.com>
RUN dnf install -y python3-pip
COPY . /dash_app
RUN pip3 install -r /dash_app/requirements.txt
#CMD python3 /dash_app/dash_app.py
