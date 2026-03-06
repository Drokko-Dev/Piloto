FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# vite.config.js already configures server.host = true and server.port = 3000
CMD ["npm", "run", "dev"]
