FROM node:20-alpine
WORKDIR /srv
COPY host/server.mjs host/index.html host/host.js ./
COPY apps ../apps
EXPOSE 5173
CMD ["node", "server.mjs"]
