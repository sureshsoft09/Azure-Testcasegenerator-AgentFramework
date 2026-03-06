# ─── Stage 1: Build React/Vite app ───────────────────────────────────────────
FROM node:20-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci --silent

COPY . .
RUN npm run build

# ─── Stage 2: Serve with nginx ───────────────────────────────────────────────
FROM nginx:1.27-alpine

# Remove the default site config
RUN rm /etc/nginx/conf.d/default.conf

# Drop in our template; nginx:alpine automatically runs envsubst
# on every file in /etc/nginx/templates/ and writes the result to
# /etc/nginx/conf.d/<filename without .template>
COPY nginx.conf /etc/nginx/templates/default.conf.template

# Copy Vite build output
COPY --from=build /app/dist /usr/share/nginx/html

# Azure Web Apps health probe
EXPOSE 80

# BACKEND_URL must be supplied as an Azure App Setting, e.g.:
#   BACKEND_URL=https://testgen-backend.azurewebsites.net
