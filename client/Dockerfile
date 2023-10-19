FROM ubuntu:22.04

RUN     apt-get update && \ 
        apt-get upgrade -y && \
        apt-get install -y python3.11

RUN mkdir /project
WORKDIR /project

RUN apt update && apt install python3-pip -y


COPY requirements.txt /project
RUN python3.11 -m pip install --upgrade pip && python3.11 -m pip install -r requirements.txt

COPY client /project

CMD [ "python3.11", "client/client.py" ]