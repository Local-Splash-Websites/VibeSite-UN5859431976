# Coolify / any Docker host: Apache + PHP serving public/ with the repo's .htaccess.
FROM python:3.12-slim AS build
WORKDIR /src
COPY . .
RUN python3 build/build.py --strict

FROM php:8.3-apache
RUN a2enmod rewrite headers expires deflate \
 && sed -ri 's!/var/www/html!/var/www/site/public!g' /etc/apache2/sites-available/000-default.conf /etc/apache2/apache2.conf \
 && sed -ri 's!AllowOverride None!AllowOverride All!g' /etc/apache2/apache2.conf
COPY --from=build /src/public /var/www/site/public
# LEADS_API_URL, LEADS_API_KEY and LEADS_SITE_NAME are read from the container environment.
RUN echo 'PassEnv LEADS_API_URL LEADS_API_KEY LEADS_SITE_NAME' > /etc/apache2/conf-enabled/leads-env.conf
EXPOSE 80
