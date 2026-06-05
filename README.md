# Cultural Aggregator — Proiect Final DevOps IT School

Aplicatie web pentru agregarea si afisarea evenimentelor culturale din Romania (concerte, teatru, festivaluri, stand-up etc.), cu filtrare si calendar interactiv.

---

## Cuprins

1. [Descrierea aplicatiei](#descrierea-aplicatiei)
2. [Tehnologii folosite](#tehnologii-folosite)
3. [Arhitectura proiectului](#arhitectura-proiectului)
4. [Rulare locala (quickstart)](#rulare-locala-quickstart)
5. [Infrastructura AWS cu Terraform](#infrastructura-aws-cu-terraform)
6. [Configurarea serverului cu Ansible](#configurarea-serverului-cu-ansible)
7. [CI/CD — Jenkins](#cicd--jenkins)
8. [CI/CD — GitHub Actions](#cicd--github-actions)
9. [Variabile de mediu](#variabile-de-mediu)

---

## Descrierea aplicatiei

**Cultural Aggregator** este o aplicatie web Flask care centralizeaza evenimentele culturale din marile orase ale Romaniei. Utilizatorii pot:

- Filtra evenimentele dupa **oras**, **data** si **categorie** simultan
- Vizualiza evenimentele pe un **calendar interactiv** (FullCalendar.js)
- Accesa direct bilete pe **iaBilet.ro** prin link-uri integrate

Aplicatia ruleaza cu **Flask** (Python) in backend, **PostgreSQL** ca baza de date si este complet containerizata cu **Docker**.

---

## Tehnologii folosite

| Categorie | Tehnologie | Versiune |
|---|---|---|
| Backend | Python / Flask | 3.10 / 3.0.0 |
| Baza de date | PostgreSQL | 15 (Alpine) |
| Frontend | Bootstrap 5 + FullCalendar | 5.3.0 / 6.1.11 |
| Containerizare | Docker + Docker Compose | latest |
| Infrastructura (IaC) | Terraform | AWS provider |
| Provisioning | Ansible | — |
| CI/CD | Jenkins + GitHub Actions | — |
| Cloud | AWS EC2 (t3.micro, eu-central-1) | — |

---

## Arhitectura proiectului

**Fluxul complet DevOps:**

1. **Terraform** creeaza instanta EC2 pe AWS
2. **Ansible** instaleaza Docker pe server
3. Codul este impins pe GitHub
4. **Jenkins** sau **GitHub Actions** detecteaza push-ul si face deploy automat pe EC2
5. Aplicatia ruleaza in containere Docker pe server

---

## Rulare locala (quickstart)

### Pasi

```bash
# 1. Cloneaza repository-ul
git clone <URL_REPO>
cd cultural-aggregator

# 2. Porneste aplicatia
docker compose up --build

# 3. Acceseaza in browser
# http://localhost:5000
```

Aplicatia va fi disponibila la **http://localhost:5000** dupa ce ambele containere (web si db) pornesc.

### Oprire

```bash
docker compose down
```

Pentru a sterge si volumul cu datele bazei de date:

```bash
docker compose down -v
```

### Verificare ca totul functioneaza

```bash
docker compose ps
```

Ar trebui sa apara:

```
cultural-aggregator-web-1   Up   0.0.0.0:5000->5000/tcp
cultural-aggregator-db-1    Up   5432/tcp
```

---

## Infrastructura AWS cu Terraform

Terraform creeaza automat:

- O instanta EC2 (t3.micro, Ubuntu, Frankfurt — eu-central-1)
- Un Security Group cu porturile 22 (SSH) si 5000 (Flask) deschise
- O cheie SSH pentru acces la server

### Cerinte

- Terraform instalat 
- AWS CLI configurat cu credentiale valide (`aws configure`)
- O pereche de chei SSH (mai jos)

### Generare cheie SSH

```bash
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa_proiect
```

### Comenzi Terraform

```bash
cd terraform

# Initializare provider AWS (o singura data)
terraform init

# Previzualizare resurse ce vor fi create (fara modificari efective)
terraform plan

# Creare infrastructura (confirma cu "yes")
terraform apply
```

La final, Terraform afiseaza IP-ul public al serverului:

```
Outputs:
  server_ip = "X.X.X.X"
```

**Noteaza acest IP** — este necesar in pasii urmatori pentru Ansible si deploy.

### Stergere infrastructura

```bash
terraform destroy
```

---

## Configurarea serverului cu Ansible

Ansible instaleaza automat Docker si Docker Compose pe serverul EC2 creat cu Terraform.

### Cerinte

- Ansible instalat
- Acces SSH la server (cheia `~/.ssh/id_rsa_proiect`)

> ```bash
> sudo apt update && sudo apt install ansible -y
> ```
> Copiaza cheia SSH din Windows in WSL:
> ```bash
> mkdir -p ~/.ssh
> cp /mnt/c/Users/<USERNAME>/.ssh/id_rsa_proiect ~/.ssh/
> chmod 600 ~/.ssh/id_rsa_proiect
> ```

### Configurare IP server

Actualizeaza fisierul `ansible/inventory.ini` cu IP-ul serverului obtinut din Terraform:

```ini
[cultural_servers]
server_cultural ansible_host=<IP_SERVER> ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/id_rsa_proiect ansible_ssh_common_args='-o StrictHostKeyChecking=no'
```

### Rulare playbook

```bash
cd ansible

ansible-playbook -i inventory.ini playbook.yml
```

Playbook-ul executa automat:

1. Actualizare pachete apt
2. Instalare dependente Docker (curl, GPG, certificates)
3. Adaugare repository oficial Docker
4. Instalare Docker Engine + Docker Compose plugin
5. Pornire serviciu Docker si activare la boot
6. Adaugare user `ubuntu` la grupul Docker

### Verificare

```bash
ssh -i ~/.ssh/id_rsa_proiect ubuntu@<IP_SERVER> "docker --version && docker compose version"
```

---

## CI/CD — Jenkins

Jenkins face deploy automat al aplicatiei pe serverul EC2 la fiecare build.

### Cerinte Jenkins

- Jenkins instalat si ruland
- Plugin **SSH Agent** instalat in Jenkins
- Credentiale SSH configurate in Jenkins cu cheia privata `id_rsa_proiect`

### Configurare Jenkins

1. Creeaza un nou **Pipeline job** in Jenkins
2. Seteaza sursa ca **Pipeline script from SCM** → Git → URL-ul repo-ului
3. Branch: `*/main`
4. Script Path: `Jenkinsfile`

### Ce face pipeline-ul

```
Stage 1: Verificare cod local
   ls -la

Stage 2: Validare Docker Compose
   docker compose config

Stage 3: Deploy pe EC2
   SSH la server
   Copiere cod (scp)
   docker compose down
   docker image prune -f
   docker compose up --build -d
```

### Adaugare credentiale SSH in Jenkins

1. **Manage Jenkins** → **Credentials** → **System** → **Global credentials**
2. **Add Credentials** → Kind: *SSH Username with private key*
3. ID: `cheie-ec2`, Username: `ubuntu`
4. Private Key: continutul fisierului `~/.ssh/id_rsa_proiect`

---

## CI/CD — GitHub Actions

GitHub Actions face deploy automat la fiecare push pe branch-ul `main`.

### Configurare Secrets

In repository-ul GitHub, adauga urmatoarele Secrets (**Settings → Secrets and variables → Actions**):

| Secret | Valoare |
|---|---|
| `SSH_HOST` | IP-ul public al serverului EC2 |
| `SSH_PRIVATE_KEY` | Continutul fisierului `~/.ssh/id_rsa_proiect` (cheia privata) |

### Ce face workflow-ul

Fisierul `.github/workflows/deploy.yml` se declanseaza la push pe `main` si executa:

1. Checkout la cod
2. Conectare SSH la serverul EC2
3. Creare / navigare la directorul `~/app`
4. `docker compose down` — opreste versiunea veche
5. `docker image prune -f` — curata imaginile vechi
6. `docker compose up --build -d` — rebuild si pornire
7. `docker compose ps` — verificare status

---

## Variabile de mediu

Aplicatia foloseste variabilele de mediu definite in `docker-compose.yml`:

| Variabila | Valoare | Descriere |
|---|---|---|
| `DB_HOST` | `db` | Hostname-ul containerului PostgreSQL |
| `DB_NAME` | `cultural_db` | Numele bazei de date |
| `DB_USER` | `devops_user` | Utilizatorul bazei de date |
| `DB_PASSWORD` | `devops_secret_2026` | Parola bazei de date |
