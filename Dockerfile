FROM lint:latest
RUN apt-get update -y
RUN apt-get install -y python-pip python-dev build-essential
COPY main.py /app
WORKDIR /app
RUN pip install python-socketio==4.6.1 aiohttp asyncio flask
ENTRYPOINT ['python']
CMD ['main.py']