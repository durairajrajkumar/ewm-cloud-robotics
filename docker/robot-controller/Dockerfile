# Dockerfile robot-controller
# Meant to be build from root directory of repository (!), in order to enable installing local modules,
# due to:
#    "The <src> path must be inside the context of the build; you cannot COPY ../something /something, 
#     because the first step of a docker build is to send the context directory (and subdirectories) 
#     to the docker daemon." - https://docs.docker.com/engine/reference/builder/#copy

FROM python:3.7.3-slim-stretch

RUN pip3 install -U wss_plugin

COPY ./python-modules/k8scrhandler /k8scrhandler
RUN pip3 install ./k8scrhandler
RUN rm -rf /k8scrhandler

COPY ./python-modules/robcoewmtypes /robcoewmtypes
RUN pip3 install ./robcoewmtypes
RUN rm -rf /robcoewmtypes

COPY ./python-modules/robcoewmrobotcontroller /robcoewmrobotcontroller
RUN pip3 install ./robcoewmrobotcontroller
RUN rm -rf /robcoewmrobotcontroller

COPY docker/robot-controller/app /app
WORKDIR /app

RUN pip3 install -r ./requirements.txt

STOPSIGNAL SIGTERM
ENTRYPOINT [ "python3", "main.py" ]