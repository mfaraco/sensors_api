FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt 

COPY . .

CMD [ "python3", "./run.py", "--host=0.0.0.0"]
