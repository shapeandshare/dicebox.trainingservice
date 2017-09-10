# https://hub.docker.com/r/tiangolo/uwsgi-nginx/
FROM tiangolo/uwsgi-nginx:python2.7

WORKDIR /app

COPY ./app /app

# Environment Variables
ENV DD_INSTALL_ONLY true
ENV DD_API_KEY #############

RUN pip install -r requirements.txt \
    && useradd -M -U -u 1000 trainingservice \
    && chown -R trainingservice /app \
    && chmod +x /app/install_agent.sh \
    && /app/install_agent.sh

EXPOSE 80