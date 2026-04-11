# syntax=docker/dockerfile:1.7
FROM node:22-alpine AS deps

WORKDIR /app
COPY package*.json /app/
RUN --mount=type=cache,target=/root/.npm npm ci

FROM deps AS build

COPY . /app
RUN npm run build

FROM deps AS test

ARG FRONTEND_SOURCE_HASH=unknown
LABEL com.exercise.frontend-source-hash=$FRONTEND_SOURCE_HASH

COPY . /app

CMD ["npm", "test"]

FROM deps AS dev

COPY . /app

EXPOSE 4200

CMD ["npm", "start"]

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist/frontend/browser /usr/share/nginx/html

EXPOSE 80
