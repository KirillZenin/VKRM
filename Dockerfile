FROM python:buster
WORKDIR /app
ADD . /app
RUN pip install -r requirements.txt
CMD ["python3","dbf2sql_proto.py"]