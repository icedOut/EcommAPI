FROM ubuntu:latest
RUN apt-get update -y
RUN apt-get install -y python-pip python-dev build-essential
COPY . /projet-de-session-dream-team
WORKDIR /projet-de-session-dream-team
RUN pip install -r requirements.txt
ENTRYPOINT ["python"]
CMD ["inf5190.py"]