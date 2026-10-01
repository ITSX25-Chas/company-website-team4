FROM python:3.13-slim

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

ENV PYTHONPATH=/app/src
ENV FLASK_APP=company_website

EXPOSE 7000

# --preload: appen, och därmed migreringarna, laddas en gång innan workers
# startas. Utan den kör båda workers samma migrering samtidigt.
CMD ["gunicorn", "--preload", "-w", "2", "-b", "0.0.0.0:7000", "--access-logfile", "-", "wsgi:app"]
