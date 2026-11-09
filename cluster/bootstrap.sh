#!/usr/bin/env bash
# Bygger upp k3s-klustret på primary från grunden, med samma versioner och
# värden som körs i itsx25-lab (avlästa 2026-11-09). Scriptet går att köra
# flera gånger: det som redan finns uppdateras eller hoppas över.
#
# Körs som root på primary, från en utcheckning av repot:
#
#   sudo FALCO_DISCORD_WEBHOOK_FILE=/root/falco-webhook \
#        SCANNER_DISCORD_WEBHOOK_FILE=/root/scanner-webhook \
#        ./cluster/bootstrap.sh
#
# Hemligheter läses från filer och skickas till kubectl via stdin, aldrig på
# kommandoraden. Falco skickar hela kommandoraden till Discord (F33, F34).
# Utan webhook-fil hoppas den komponenten över, och scriptet säger det.
#
# Appen själv deployas inte här. Den kommer från deploy.yml i GitHub Actions,
# som bygger, skannar, signerar och rullar ut imagen.
set -euo pipefail

K3S_VERSION="v1.36.4+k3s1"
HELM_VERSION="v3.22.0"
INGRESS_NGINX_CHART="4.15.1"      # controller v1.15.1
POLICY_CONTROLLER_CHART="0.10.8"  # policy-controller v0.13.1
FALCO_CHART="9.2.0"               # Falco 0.45.0

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

log() { printf '\n==> %s\n' "$*"; }
die() { printf 'FEL: %s\n' "$*" >&2; exit 1; }

[[ $EUID -eq 0 ]] || die "Kör som root (sudo)."

# --- Förutsättningar ---------------------------------------------------------
# Terraform slår på ip_forward permanent på primary (F25, terraform-infra
# PR #70). Utan det når ingen trafik poddarna, och sajten svarar inte.
[[ "$(sysctl -n net.ipv4.ip_forward)" == "1" ]] \
  || die "net.ipv4.ip_forward är 0. Primary ska vara skapad av terraform-infra."

# --- k3s ---------------------------------------------------------------------
# Installern hämtas från samma release-tagg som binären, inte från get.k3s.io
# som kan ändras. Den kontrollerar själv binärens checksumma mot releasen.
# Traefik ersätts av ingress-nginx. metrics-server behövs inte och kostar minne.
if k3s --version 2>/dev/null | grep -qF "$K3S_VERSION"; then
  log "k3s $K3S_VERSION finns redan"
else
  log "Installerar k3s $K3S_VERSION"
  curl -sfL "https://raw.githubusercontent.com/k3s-io/k3s/${K3S_VERSION//+/%2B}/install.sh" \
    | INSTALL_K3S_VERSION="$K3S_VERSION" sh -s - server \
        --disable=traefik \
        --disable=metrics-server
fi

log "Väntar på att noden blir Ready"
for _ in $(seq 1 60); do
  k3s kubectl get nodes 2>/dev/null | grep -q ' Ready ' && break
  sleep 5
done
k3s kubectl get nodes | grep -q ' Ready ' || die "Noden blev aldrig Ready."
kubectl() { k3s kubectl "$@"; }

# --- Helm --------------------------------------------------------------------
if helm version --short 2>/dev/null | grep -qF "$HELM_VERSION"; then
  log "Helm $HELM_VERSION finns redan"
else
  log "Installerar Helm $HELM_VERSION med kontrollerad checksumma"
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' EXIT
  tarball="helm-${HELM_VERSION}-linux-amd64.tar.gz"
  curl -fsSLo "$tmp/$tarball" "https://get.helm.sh/$tarball"
  curl -fsSLo "$tmp/$tarball.sha256sum" "https://get.helm.sh/$tarball.sha256sum"
  (cd "$tmp" && sha256sum -c "$tarball.sha256sum")
  tar -xzf "$tmp/$tarball" -C "$tmp" linux-amd64/helm
  install -m 0755 "$tmp/linux-amd64/helm" /usr/local/bin/helm
fi

helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx --force-update >/dev/null
helm repo add sigstore https://sigstore.github.io/helm-charts --force-update >/dev/null
helm repo add falcosecurity https://falcosecurity.github.io/charts --force-update >/dev/null
helm repo update >/dev/null

# Skapar en secret med ett värde från en fil, via stdin. Finns secreten redan
# rörs den inte, så att ett omkört script aldrig byter en fungerande nyckel.
secret_from_file() {
  local ns="$1" name="$2" key="$3" file="$4"
  if kubectl -n "$ns" get secret "$name" >/dev/null 2>&1; then
    echo "Secret $ns/$name finns redan, rörs inte"
    return 0
  fi
  [[ -r "$file" ]] || return 1
  kubectl -n "$ns" create secret generic "$name" --from-file="$key"=/dev/stdin < "$file"
}

# --- Ingress -----------------------------------------------------------------
log "ingress-nginx $INGRESS_NGINX_CHART"
helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
  --version "$INGRESS_NGINX_CHART" \
  --namespace ingress-nginx --create-namespace \
  --values "$REPO_ROOT/helm/ingress-nginx-values.yaml" \
  --wait

# --- Signaturkontroll ----------------------------------------------------------
# Policy-controllern stoppar varje image i ett inkluderat namespace som inte är
# signerad av vårt deploy-workflow (T1610, T1195.002). Den är fail-closed.
log "policy-controller $POLICY_CONTROLLER_CHART"
helm upgrade --install policy-controller sigstore/policy-controller \
  --version "$POLICY_CONTROLLER_CHART" \
  --namespace cosign-system --create-namespace \
  --wait

kubectl label namespace default policy.sigstore.dev/include=true --overwrite
kubectl apply -f "$REPO_ROOT/k8s/image-policy.yaml"

# --- Detektion -----------------------------------------------------------------
kubectl create namespace falco --dry-run=client -o yaml | kubectl apply -f -
if secret_from_file falco falcosidekick-discord DISCORD_WEBHOOKURL "${FALCO_DISCORD_WEBHOOK_FILE:-}"; then
  log "Falco $FALCO_CHART"
  helm upgrade --install falco falcosecurity/falco \
    --version "$FALCO_CHART" \
    --namespace falco \
    --values "$REPO_ROOT/helm/falco-values.yaml" \
    --wait
else
  log "HOPPAR ÖVER Falco: ange FALCO_DISCORD_WEBHOOK_FILE. Utan larmkanal är Falco blind."
fi

# --- Appens förutsättningar ------------------------------------------------------
# SECRET_KEY genereras här och lämnar aldrig klustret. Den finns inte i Git
# och inte i GitHub (F18).
log "Appens secret och deploy-kontot"
if ! kubectl -n default get secret company-website >/dev/null 2>&1; then
  openssl rand -hex 32 | tr -d '\n' \
    | kubectl -n default create secret generic company-website --from-file=secret-key=/dev/stdin
else
  echo "Secret default/company-website finns redan, rörs inte"
fi
kubectl apply -f "$REPO_ROOT/k8s/github-permissions.yaml"

# --- Skannern ----------------------------------------------------------------------
log "Daglig SBOM-skanner"
kubectl apply -f "$REPO_ROOT/k8s/scanner/namespace.yaml"
kubectl apply -f "$REPO_ROOT/k8s/scanner/image-policy.yaml"
kubectl apply -f "$REPO_ROOT/k8s/scanner/rbac.yaml"
if secret_from_file security-tools sbom-scanner-discord webhook-url "${SCANNER_DISCORD_WEBHOOK_FILE:-}"; then
  kubectl apply -f "$REPO_ROOT/k8s/scanner/cronjob.yaml"
else
  log "HOPPAR ÖVER skannerns CronJob: ange SCANNER_DISCORD_WEBHOOK_FILE."
fi

# --- Klart ---------------------------------------------------------------------------
log "Klustret är uppbyggt"
kubectl get pods -A
cat <<'EOF'

Kvar att göra för hand:
  1. Uppdatera repo-secreten KUBECONFIG i GitHub med en kubeconfig för kontot
     github-deployer, och kör deploy.yml (workflow_dispatch) för att rulla ut appen.
  2. Testa larmkedjan hela vägen: `sudo true` på noden ska ge ett larm i
     Falco-kanalen, och skannern ska rapportera vid nästa körning.
EOF
