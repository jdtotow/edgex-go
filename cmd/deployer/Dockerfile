FROM alpine:3.12
RUN mkdir /app 
COPY cmd/deployer/deployer /usr/bin/deployer
RUN apk add musl 
RUN chmod +x /usr/bin/deployer 
EXPOSE 8778 
CMD [ "deployer" ] 
