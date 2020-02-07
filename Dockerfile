FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV CONFIG_FILE config.yaml

CMD [ "python", "./run.py" ]