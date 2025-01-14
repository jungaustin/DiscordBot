FROM python:3.11.5-slim

WORKDIR /APP

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

CMD ["python", "main.py"]