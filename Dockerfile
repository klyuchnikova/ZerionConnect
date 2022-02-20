FROM python:latest
RUN pip install --upgrade pip
WORKDIR /app
COPY flask_app.py .
RUN pip install python-socketio==4.6.1 aiohttp asyncio flask
CMD ["python", "main.py"]