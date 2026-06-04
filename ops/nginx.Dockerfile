FROM nginx:1.27-alpine

COPY ops/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
