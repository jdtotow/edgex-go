FROM alpine:3.12
RUN mkdir /app 
COPY src/dist/main /usr/bin
RUN apk add musl 
RUN chmod +x /usr/bin/main 
EXPOSE 8778 
CMD [ "main" ] 