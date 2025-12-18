FROM node:20-alpine AS build
WORKDIR /app

# Digital Ocean passe les variables BUILD_TIME comme variables d'environnement au build
# Il faut les exposer explicitement pour que Vite puisse les lire
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

COPY package.json package-lock.json* pnpm-lock.yaml* yarn.lock* ./
RUN npm install
COPY . .

# Afficher la variable pour debug (sera supprimé dans le build final)
RUN echo "Building with VITE_API_BASE_URL=${VITE_API_BASE_URL}"

RUN npm run build

FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
# Copier la configuration nginx personnalisée pour écouter sur le port 8080
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]

