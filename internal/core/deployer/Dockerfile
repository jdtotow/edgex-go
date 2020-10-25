FROM python:3.7.0
RUN pip install --upgrade pip 
RUN pip install docker flask flask_jwt prometheus_client requests pymongo 
RUN mkdir /app 
COPY src/main.py /app/ 
COPY src/deployer.py /app/
EXPOSE 8778 
WORKDIR /app
ENTRYPOINT ["python","-u","main.py"]