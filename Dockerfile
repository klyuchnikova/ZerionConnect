FROM python:latest
RUN pip install --upgrade pip
WORKDIR /app
COPY main.py .
RUN pip install python-socketio==4.6.1 aiohttp asyncio flask quart
CMD ["python", "main.py"]