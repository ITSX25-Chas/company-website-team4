# Basen är låst med digest, så att varje bygge utgår från exakt samma image.
# Taggen står kvar för läsbarheten. Dependabot föreslår ny digest varje
# vecka (.github/dependabot.yml).
FROM python:3.13-slim@sha256:3dd7cc108ec1493442514f5c2a871af6af0ec31d768ff6e378a93340c3b3db5f

# Säkerhetsuppdateringar i Debian-basen kommer med vid varje bygge,
# även när python-imagen inte har byggts om än (F36).
RUN apt-get update \
 && apt-get upgrade -y --no-install-recommends \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
# pip behövs bara vid bygget. Det tas bort i samma lager, så att pip och
# biblioteken det har inbakade inte följer med i imagen som kör (F56).
RUN pip install --no-cache-dir -r requirements.txt \
 && pip uninstall -y pip

# Bara det appen behöver. Med COPY . . följde bl.a. Falcos regler och
# undantag, workflows och skript för kubeconfig med i imagen (F62).
COPY wsgi.py .
COPY src/ src/

# Appen körs som en egen användare utan rättigheter i imagen (F23). UID:t
# är fast, så att k8s/deployment.yaml och volymens ägare kan använda det.
# /app/data skapas här, så att en ny Docker-volym får rätt ägare.
RUN groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app \
 && mkdir -p /app/data \
 && chown app:app /app/data
USER 10001:10001

ENV PYTHONPATH=/app/src
ENV FLASK_APP=company_website

EXPOSE 7000

# --preload: appen, och därmed migreringarna, laddas en gång innan workers
# startas. Utan den kör båda workers samma migrering samtidigt.
CMD ["gunicorn", "--preload", "-w", "2", "-b", "0.0.0.0:7000", "--access-logfile", "-", "wsgi:app"]
