# Linux Agentic Tool

An AI-powered command-line tool that manages your Linux server for you. Tell it what you want to install, it generates the right commands for your OS, asks your permission before running anything, and automatically fixes errors if something goes wrong.

Powered by [OpenRouter](https://openrouter.ai) free API — no cost to use.

---

## Table of Contents

- [What It Does](#what-it-does)
- [Requirements](#requirements)
- [Installation](#installation)
- [First-Time Setup](#first-time-setup)
- [CLI Shortcuts — Skip the Menus](#cli-shortcuts--skip-the-menus)
- [Main Menu (Interactive Mode)](#main-menu-interactive-mode)
- [Option 1 — Install from Recipe](#option-1--install-from-recipe)
- [Option 2 — Custom Task](#option-2--custom-task)
- [Option 3 — Ask AI](#option-3--ask-ai)
- [Option 4 — Add Virtual Host + SSL](#option-4--add-virtual-host--ssl)
- [Option 5 — AI Script Writer](#option-5--ai-script-writer)
- [Option 6 — Cron Job Manager](#option-6--cron-job-manager)
- [Option 7 — Settings](#option-7--settings)
- [Option 8 — Token & Credit Usage](#option-8--token--credit-usage)
- [Changing the AI Model](#changing-the-ai-model)
- [How Commands Are Executed](#how-commands-are-executed)
- [Auto Error Fixing](#auto-error-fixing)
- [All Available Recipes](#all-available-recipes)
- [Supported Linux Distributions](#supported-linux-distributions)
- [Config File](#config-file)
- [Project Structure](#project-structure)
- [Getting a Free OpenRouter API Key](#getting-a-free-openrouter-api-key)
- [Troubleshooting](#troubleshooting)

---

## What It Does

- Asks you which Linux distro you are running and saves it permanently
- Stores your free OpenRouter API key permanently
- Generates correct shell commands for your specific OS and package manager via AI
- Shows you every command before running it — you approve, skip, or quit
- Streams live output while commands run
- If a command fails, AI diagnoses the error, suggests fix commands, and retries
- Comes with 50+ ready-to-use recipes: Nginx, LAMP, LEMP, WordPress, Drupal, Ghost, Nextcloud, MySQL, PostgreSQL, MongoDB, Redis, Elasticsearch, Docker, Jenkins, Gitea, Grafana, Prometheus, Laravel, Django, Flask, Fail2ban, WireGuard, Vaultwarden, and more
- Lets you describe any task in plain English and the AI figures out the commands
- Virtual host manager — generate Nginx or Apache vhost configs with HTTP, Let's Encrypt SSL, or your own custom certificate
- AI script writer — describe what a script should do and get a production-ready bash script written and saved to disk
- Cron job manager — list, add, and remove cron jobs with schedule presets, AI can suggest the schedule

---

## Requirements

- A Linux server (see [Supported Distributions](#supported-linux-distributions))
- Python 3.8 or newer
- `pip3` (usually comes with Python 3)
- Internet access (to reach the OpenRouter API)
- A free OpenRouter API key (see [Getting a Free Key](#getting-a-free-openrouter-api-key))

---

## Installation

### Step 1 — Copy files to your Linux server

From your local machine:

```bash
scp -r linux-agent/ user@your-server-ip:~/
```

Or clone/download directly on the server if you have git:

```bash
git clone https://github.com/Vishalsoni2017/linux-ai-agent.git ~/linux-agent
```

### Step 2 — Install Python dependency

```bash
cd ~/linux-agent
pip3 install -r requirements.txt
```

This only installs one package: `requests`.

### Step 3 — (Optional) Install the launcher

Run the included installer to create a `linuxagent` command you can call from anywhere:

```bash
bash install.sh
```

Then reload your shell:

```bash
source ~/.bashrc
```

---

## First-Time Setup

The first time you run the tool it walks you through a two-step setup wizard. This only happens once — answers are saved permanently.

```bash
python3 ~/linux-agent/main.py
# or if you ran install.sh:
linuxagent
```

### Step 1 — Choose your OS

A numbered list of Linux distributions appears. Type the number for your OS and press Enter.

```
============================================================
  Select Your Linux Distribution
============================================================

   1. Ubuntu 20.04
   2. Ubuntu 22.04
   3. Ubuntu 24.04
   4. Debian 11
   5. Debian 12
   6. CentOS 7
   7. CentOS Stream 8
   8. CentOS Stream 9
   9. Rocky Linux 8
  10. Rocky Linux 9
  11. AlmaLinux 8
  12. AlmaLinux 9
  13. Fedora 38+
  14. RHEL 8
  15. RHEL 9
  16. Arch Linux
  17. openSUSE Leap

  Enter number (1-17): 2
  [OK]  OS saved: Ubuntu 22.04  (package manager: apt)
```

The tool automatically selects the right package manager (`apt`, `yum`, `dnf`, `pacman`, or `zypper`) based on your choice.

### Step 2 — Enter your OpenRouter API key

```
============================================================
  OpenRouter API Key Setup
============================================================

  Get your FREE API key at: https://openrouter.ai/keys
  The key is stored locally in ~/.linux_agent/config.json

  Paste your OpenRouter API key: sk-or-v1-xxxxxxxxxxxx
  [OK]  API key saved securely.
```

Your key is stored in `~/.linux_agent/config.json` with `600` permissions (only your user can read it).

After setup completes the main menu loads and you never see the wizard again unless you change settings manually.

---

---

## CLI Shortcuts — Skip the Menus

You do not have to go through the menus every time. Pass arguments directly on the command line and the tool jumps straight to the action.

### Syntax

```bash
python3 main.py <command> [arguments] [--yes]
# or if you ran install.sh:
linuxagent <command> [arguments] [--yes]
```

### All shortcut commands

| Command | What it does |
|---------|-------------|
| `install <recipe>` | Install a pre-built recipe directly |
| `task "<description>"` | Run any task described in plain English |
| `ask "<question>"` | Ask AI a question and print the answer |
| `list` | Show all available recipes with their shortcut names |
| `setup` | Re-run the first-time setup wizard |
| `--yes` or `-y` flag | Skip the "Proceed? [y/n]" plan confirmation |

---

### install — jump straight to a recipe

```bash
python3 main.py install nginx
python3 main.py install wordpress
python3 main.py install mysql
python3 main.py install docker
python3 main.py install php
python3 main.py install nodejs
python3 main.py install certbot
python3 main.py install ufw
```

Partial names work too:

```bash
python3 main.py install word       # matches wordpress
python3 main.py install post       # matches postgresql
python3 main.py install compose    # matches docker_compose
```

---

### task — describe anything in plain English

```bash
python3 main.py task "install jenkins"
python3 main.py task "set up a LAMP stack"
python3 main.py task "install and configure Postfix mail server"
python3 main.py task "set up swap space of 2GB"
python3 main.py task "configure automatic daily backups with rsync to /mnt/backup"
python3 main.py task "install Python Flask app with Gunicorn behind Nginx"
```

Multi-word descriptions need quotes around them.

---

### ask — get an instant AI answer

```bash
python3 main.py ask "how do I check disk usage?"
python3 main.py ask "what does chmod 755 mean?"
python3 main.py ask "how do I see which process is using port 80?"
python3 main.py ask "difference between apt update and apt upgrade"
python3 main.py ask "how do I create a new sudo user?"
```

Prints the answer and exits — no menu, no prompts.

---

### list — see all recipes and their shortcut names

```bash
python3 main.py list
```

Output:

```
  Web Servers
    nginx                Install and start Nginx, enable on boot
      Shortcut: python3 main.py install nginx
    apache               Install Apache (httpd), start and enable it
      Shortcut: python3 main.py install apache
    wordpress            Install Nginx + PHP + MySQL + WordPress + all required extensions
      Shortcut: python3 main.py install wordpress
  ...
```

---

### --yes flag — skip the plan confirmation

By default, even with shortcuts the tool shows you the AI-generated plan and asks:

```
  Proceed with execution? [y/n] >
```

Add `--yes` (or `-y`) to skip that confirmation and start executing immediately:

```bash
python3 main.py --yes install nginx
python3 main.py -y install docker
python3 main.py --yes task "install git and configure global username"
```

> Note: `--yes` only skips the overall plan confirmation. Each individual command still shows its own `[y/n/s/q]` permission prompt. You stay in full control of every step.

---

### setup — change OS or API key from command line

```bash
python3 main.py setup
```

Re-runs the full setup wizard. Use this to switch to a different OS or update your API key.

---

### Quick reference card

```
# Install software
python3 main.py install nginx
python3 main.py install wordpress
python3 main.py install lamp
python3 main.py install lemp
python3 main.py install mysql
python3 main.py install docker
python3 main.py install php
python3 main.py install nodejs
python3 main.py install redis
python3 main.py install certbot
python3 main.py install ufw
python3 main.py install fail2ban
python3 main.py install grafana
python3 main.py install prometheus_grafana
python3 main.py install laravel
python3 main.py install django

# Custom task
python3 main.py task "your task here"

# Ask a question (no execution, just answer)
python3 main.py ask "your question here"

# Add a new Nginx/Apache site with SSL
python3 main.py vhost

# Write a bash script with AI
python3 main.py script

# Manage cron jobs
python3 main.py cron

# Change AI model (all free)
python3 main.py model

# View token usage stats
python3 main.py usage

# See all 50+ recipe names
python3 main.py list

# Skip plan confirmation
python3 main.py --yes install nginx

# Change OS or API key
python3 main.py setup

# Open interactive menus
python3 main.py
```

---

## Main Menu (Interactive Mode)

```
============================================================
  Main Menu
============================================================

  1. [PKG]    Install from recipe (Nginx, LAMP, WordPress, Docker, Grafana...)
  2. [AI]     Custom task (describe anything in plain English)
  3. [Q&A]    Ask AI a question about Linux
  4. [VHOST]  Add Nginx / Apache virtual host + SSL
  5. [SCRIPT] Write a bash script with AI
  6. [CRON]   Manage cron jobs
  7. [CFG]    Settings (OS / API key / Model)
  8. [STATS]  View token & credit usage
  0. [EXIT]   Exit
```
  4. [CFG]  Settings  (change OS / API key)
  0. [EXIT] Exit
```

Type a number and press Enter.

---

## Option 1 — Install from Recipe

Recipes are pre-built installation plans. The AI takes the recipe description and generates the exact commands for your specific OS and package manager.

Select option `1` from the main menu. You will see a categorised list:

```
  Web Servers
   1. Nginx Web Server              Install and start Nginx, enable on boot
   2. Apache Web Server             Install Apache (httpd), start and enable it

  Web Servers
   3. WordPress (Full Stack)        Install Nginx + PHP + MySQL + WordPress + all required extensions

  Databases
   4. MySQL Server                  Install MySQL (or MariaDB), start and secure it
   5. PostgreSQL Server             Install PostgreSQL, start and enable it
   6. MongoDB                       Add MongoDB repo, install, start and enable
   7. Redis                         Install Redis server, start and enable

  Runtimes & Languages
   8. PHP + Common Extensions       Install PHP with FPM and common extensions
   9. Node.js (LTS)                 Install latest Node.js LTS via NodeSource
  10. Python 3 + pip + venv         Install Python 3, pip, and virtualenv
  11. Java (OpenJDK 17)             Install OpenJDK 17 JDK
  12. Ruby + Bundler                Install Ruby and Bundler gem

  Dev Tools
  13. Docker CE                     Add Docker repo, install Docker CE, start and enable
  14. Docker Compose                Install latest Docker Compose plugin
  15. Git                           Install latest Git

  Security
  16. Certbot (Let's Encrypt SSL)   Install Certbot with Nginx plugin
  17. UFW Firewall                  Install and configure UFW, allow SSH + HTTP + HTTPS
  18. Fail2ban                      Install Fail2ban for brute-force protection

   0. <- Back
```

Type the number for what you want. For example, to install WordPress enter `3`.

The tool then:

1. Sends the task to AI with your OS and package manager context
2. Shows you the full plan and all generated commands
3. Asks for overall confirmation before starting
4. Runs each command one at a time, asking permission for each

---

## Option 2 — Custom Task

Use this when you want to do something that is not in the recipe list. Describe the task in plain English and the AI generates the commands.

```
============================================================
  Custom Task
============================================================

  Describe what you want to install or configure in plain English.
  Examples:
    * Install Jenkins CI server
    * Install and configure a LAMP stack
    * Set up a Python Flask app with Gunicorn and Nginx

  Your task: set up a Django app with PostgreSQL and Nginx as reverse proxy
```

The AI will:
- Understand what you need
- Generate all required commands in the correct order for your OS
- Warn you about anything important before you start

You can use this for things like:
- "Install and configure Postfix mail server"
- "Set up a LEMP stack"
- "Install Kubernetes with kubeadm"
- "Configure automatic daily backups with rsync"
- "Install and harden SSH with key-only authentication"

---

## Option 3 — Ask AI

A free-form question and answer mode. Ask anything about Linux and get a concise practical answer.

```
============================================================
  Ask AI
============================================================

  Question: how do I check which ports are open on this server?

  You can use: ss -tuln
  Or: netstat -tuln (if net-tools is installed)
  Or: nmap localhost (requires nmap)
  The ss command is recommended on modern systems.

  Question: back
```

Type `back`, `exit`, or `quit` to return to the main menu.

---

## Option 4 — Add Virtual Host + SSL

Use this to add a new website config to Nginx or Apache without touching config files manually. The AI generates the complete, production-ready config block.

### Start from menu or shortcut

```bash
python3 main.py vhost
```

### What it asks you

```
  Which web server?
  1. Nginx
  2. Apache
  Choice [1/2]: 1

  Domain name (e.g. example.com): mysite.com

  Document root [/var/www/mysite.com]:

  Is this a PHP site? [y/n]: n

  Is this a reverse proxy to a local port? [y/n]: y
  Backend port (e.g. 3000, 8080): 3000

  SSL / HTTPS mode:
  1. No SSL (HTTP only)
  2. Let's Encrypt (Certbot) — auto-obtain free certificate
  3. Custom / own certificate (you already have cert + key files)
  Choice [1/2/3]: 2

  Email for Let's Encrypt notifications: admin@mysite.com
```

### SSL modes explained

**Option 1 — HTTP only**
Creates a basic vhost on port 80. Good for internal sites or when you will add SSL later.

**Option 2 — Let's Encrypt (Certbot)**
Generates an HTTP config first, then automatically runs Certbot to obtain and install a free certificate. Your domain must point to the server's IP before running this.

```
  Certbot command that will be run:
  certbot --nginx -d mysite.com -d www.mysite.com --non-interactive --agree-tos -m admin@mysite.com
```

**Option 3 — Custom / Own Certificate**
Use an SSL certificate you already have (purchased CA cert, self-signed, wildcard, etc.).

```
  Path to certificate file (e.g. /etc/ssl/certs/cert.pem): /etc/ssl/mysite/cert.pem
  Path to private key file  (e.g. /etc/ssl/private/key.pem): /etc/ssl/mysite/key.pem
```

The generated config includes HSTS headers, security headers (X-Frame-Options, X-Content-Type-Options), gzip compression, and correct listen directives for both 80 and 443.

### What gets created

After you confirm, the tool:
1. Creates the document root directory
2. Sets `www-data:www-data` ownership
3. Writes the config to `/etc/nginx/sites-available/mysite.com` (or `/etc/apache2/sites-available/mysite.com.conf`)
4. Symlinks it to sites-enabled (Nginx) or runs `a2ensite` (Apache)
5. Tests the config (`nginx -t` or `apache2ctl configtest`)
6. Reloads the web server
7. Runs Certbot if Let's Encrypt was chosen

---

## Option 5 — AI Script Writer

Describe any task in plain English and the AI writes a complete, production-quality bash script, saves it to disk, and makes it executable.

### Start from menu or shortcut

```bash
python3 main.py script
```

### Example session

```
  Script description: back up /var/www to /mnt/backup with a timestamp and keep only last 7 backups

  Save to [/usr/local/bin/back.sh]: /usr/local/bin/backup_www.sh

  Asking AI to write the script...

  ============================================================
  Generated Script
  ============================================================

  #!/usr/bin/env bash
  set -euo pipefail

  # Backup /var/www to /mnt/backup with timestamp
  # Keeps only the last 7 backups

  BACKUP_DIR="/mnt/backup"
  SOURCE_DIR="/var/www"
  TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
  BACKUP_NAME="www_backup_${TIMESTAMP}.tar.gz"
  LOG_FILE="/var/log/backup_www.log"
  MAX_BACKUPS=7

  log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"; }

  log "Starting backup of $SOURCE_DIR..."
  mkdir -p "$BACKUP_DIR"
  tar -czf "${BACKUP_DIR}/${BACKUP_NAME}" "$SOURCE_DIR"
  log "Backup created: ${BACKUP_NAME}"

  # Remove old backups keeping only last MAX_BACKUPS
  ls -t "$BACKUP_DIR"/www_backup_*.tar.gz | tail -n +$((MAX_BACKUPS + 1)) | xargs -r rm --
  log "Cleanup done. Backups retained: $MAX_BACKUPS"

  Write this script to disk? [y/n]: y

  [OK] Script written to /usr/local/bin/backup_www.sh

  Add this script to a cron job now? [y/n]: y
```

After writing, it immediately offers to add the script to crontab.

### What the AI always adds to scripts

- `#!/usr/bin/env bash` shebang
- `set -euo pipefail` (strict mode — stops on errors)
- Descriptive comments
- Absolute paths for all commands
- Error handling with meaningful messages
- Timestamped logging to `/var/log/` where appropriate
- Idempotent design where possible

### Script ideas

```bash
python3 main.py script
# then describe any of these:

"Restart nginx if it is not responding"
"Delete files in /tmp older than 3 days"
"Check disk usage and send email if over 85%"
"Sync /var/www to S3 bucket using aws cli"
"Renew all Let's Encrypt certificates and reload nginx"
"Monitor memory usage and log to /var/log/memory.log"
"Create a MySQL dump of all databases to /backups"
"Check if all systemd services are running and alert if any failed"
```

---

## Option 6 — Cron Job Manager

Add, list, and remove cron jobs through a menu. Includes schedule presets so you never have to remember cron syntax.

### Start from menu or shortcut

```bash
python3 main.py cron
```

### Sub-menu

```
  1. List current cron jobs
  2. Add a new cron job
  3. Remove a cron job
  4. Add cron job for a script (AI suggests schedule)
```

### Adding a cron job — schedule picker

When adding a cron job you choose from presets or enter a custom expression:

```
  Pick a schedule:
   1. Every minute                (* * * * *)
   2. Every 5 minutes             (*/5 * * * *)
   3. Every 15 minutes            (*/15 * * * *)
   4. Every 30 minutes            (*/30 * * * *)
   5. Every hour                  (0 * * * *)
   6. Every 6 hours               (0 */6 * * *)
   7. Every day at midnight       (0 0 * * *)
   8. Every day at 2am            (0 2 * * *)
   9. Every Sunday at 3am         (0 3 * * 0)
  10. Every Monday at 4am         (0 4 * * 1)
  11. 1st of every month 1am      (0 1 1 * *)
  12. Custom (enter manually)
```

You can also choose to log output:

```
  Log output to file? [y/n]: y
  Log file [/var/log/backup_www.log]:
```

Final cron line shown before adding:

```
  Cron line to add:
  0 2 * * * /usr/local/bin/backup_www.sh >> /var/log/backup_www.log 2>&1

  Add this cron job? [y/n]:
```

### AI suggests schedule (Option 4)

Give it the script path and the AI reads the filename and suggests the most appropriate schedule automatically:

```
  Path to script: /usr/local/bin/backup_www.sh

  AI suggests: 0 2 * * *
  Use this schedule? [y/n]:
```

### Remove a cron job

Lists numbered cron entries, you pick the number to remove:

```
  1. 0 2 * * * /usr/local/bin/backup_www.sh >> /var/log/backup_www.log 2>&1
  2. */5 * * * * /usr/local/bin/check_nginx.sh

  Remove which job number: 1
  Confirm? [y/n]:
```

---

## Option 7 — Settings

Change your saved OS, API key, or AI model at any time.

```
============================================================
  Settings
============================================================

  1. Change OS
  2. Change API Key
  3. Change AI Model
  4. View token / credit usage
  0. Back
```

Changing the OS automatically updates the stored package manager.

---

## Option 8 — Token & Credit Usage

See how many tokens were used this session and across all sessions.

```bash
# From menu: option 8
# From CLI shortcut:
python3 main.py usage
```

Example output:

```
============================================================
  Token Usage
============================================================

  This session:
    API calls  : 4
    Prompt     : 1,842 tokens
    Completion : 614 tokens
    Total      : 2,456 tokens

  Lifetime (all sessions):
    API calls  : 27
    Prompt     : 11,203 tokens
    Completion : 3,891 tokens
    Total      : 15,094 tokens

  Note: All models used are FREE — $0.00 cost.
```

After every single API call the tool also prints a compact inline usage line:

```
  [tokens]  prompt: 312  completion: 148  total: 460  model: deepseek/deepseek-r1:free
```

This appears directly below the AI response so you always know the cost of the last operation.

---

## Changing the AI Model

All models are free on OpenRouter. The default `openrouter/auto` lets OpenRouter pick the best available free model automatically.

```bash
# From menu: option 7 → 3
# From CLI shortcut:
python3 main.py model
```

Available models:

| Model | Best for |
|-------|---------|
| `openrouter/auto` | Default — OpenRouter picks the best free model automatically |
| `deepseek/deepseek-r1:free` | Complex reasoning, multi-step Linux tasks |
| `deepseek/deepseek-chat:free` | Fast general-purpose tasks |
| `meta-llama/llama-3.3-70b-instruct:free` | Meta's latest large model, great all-rounder |
| `meta-llama/llama-3.1-8b-instruct:free` | Lightweight, fastest responses |
| `google/gemma-3-27b-it:free` | Google's instruction-tuned model |
| `mistralai/mistral-7b-instruct:free` | Fast, good at scripting |
| `qwen/qwen-2.5-72b-instruct:free` | Excellent at code and shell commands |
| `microsoft/phi-3-medium-128k-instruct:free` | 128K context window |

The selected model is saved permanently in `~/.linux_agent/config.json` and used for all future API calls until you change it again.

---

## How Commands Are Executed

Every single command is shown to you before it runs. You have four choices:

```
  +--------------------------------------------------+
  |  Command to execute                              |
  |  $ apt install -y nginx php-fpm php-mysql        |
  +--------------------------------------------------+
  Run this command? [y/n/s(skip)/q(quit)] >
```

| Input | What happens |
|-------|-------------|
| `y` or `yes` | Command runs immediately with live output |
| `n`, `s`, or `skip` | Command is skipped, moves to the next one |
| `q` or `quit` | Stops everything and exits the tool |

Commands run with `sudo` automatically so you do not need to be root.

Live output streams to your terminal as the command runs so you can see exactly what is happening in real time.

---

## Auto Error Fixing

If a command fails, the tool does not just stop. It asks the AI to diagnose what went wrong.

Here is the full flow:

```
  [3/7]
  +--------------------------------------------------+
  |  $ apt install -y php8.1-fpm                     |
  +--------------------------------------------------+
  Run this command? [y/n/s(skip)/q(quit)] > y

  Running: sudo apt install -y php8.1-fpm
     ...output...
  [ERR] Command failed (exit code 100).

  Asking AI to diagnose and fix (attempt 1/2)...

  [!] Diagnosis: php8.1 repository is not added yet

  Fix step:
  +--------------------------------------------------+
  |  $ add-apt-repository ppa:ondrej/php -y          |
  +--------------------------------------------------+
  Run this command? [y/n/s(skip)/q(quit)] > y

  Running: sudo add-apt-repository ppa:ondrej/php -y
  [OK] Command succeeded.

  Retrying original command...
  +--------------------------------------------------+
  |  $ apt install -y php8.1-fpm                     |
  +--------------------------------------------------+
  Run this command? [y/n/s(skip)/q(quit)] > y

  Running: sudo apt install -y php8.1-fpm
  [OK] Command succeeded.
```

The tool retries up to **2 times** per command. If it still cannot fix the error after 2 attempts it logs the failure and moves on to the next command.

You approve every fix command the same way you approve normal commands — nothing ever runs without your `y`.

---

## All Available Recipes

Run `python3 main.py list` to see all recipe shortcut names at any time.

### Web Servers

| Shortcut | What gets installed |
|----------|-------------------|
| `nginx` | Nginx, service started and enabled on boot |
| `apache` | Apache2 or httpd, started and enabled |
| `lamp` | Apache + MySQL/MariaDB + PHP + mod_rewrite (classic stack) |
| `lemp` | Nginx + MySQL/MariaDB + PHP-FPM + Nginx PHP config (modern stack) |
| `caddy` | Caddy web server with automatic HTTPS |

### CMS & Applications

| Shortcut | What gets installed |
|----------|-------------------|
| `wordpress` | Nginx + PHP-FPM + MySQL + WordPress + all extensions + DB + config |
| `joomla` | Nginx + PHP-FPM + MySQL + Joomla + DB setup |
| `drupal` | Nginx + PHP-FPM + MySQL + Composer + Drupal 10 |
| `ghost` | Node.js + Ghost blog + Nginx reverse proxy |
| `nextcloud` | Nginx + PHP-FPM + MySQL + Nextcloud + all required extensions |
| `matomo` | Nginx + PHP-FPM + MySQL + Matomo analytics |

### Databases & Message Queues

| Shortcut | What gets installed |
|----------|-------------------|
| `mysql` | MySQL or MariaDB, started and secured |
| `postgresql` | PostgreSQL, cluster init if needed, started |
| `mongodb` | Official MongoDB repo + mongodb-org |
| `redis` | Redis server, started and enabled |
| `elasticsearch` | Official Elastic repo + Elasticsearch 8.x |
| `influxdb` | InfluxData repo + InfluxDB 2 (time-series) |
| `memcached` | Memcached in-memory cache daemon |
| `rabbitmq` | Erlang + RabbitMQ + management plugin |

### Runtimes & Languages

| Shortcut | What gets installed |
|----------|-------------------|
| `php` | PHP-FPM + cli + all common extensions (mysql/xml/mbstring/curl/zip/gd/bcmath/imagick) |
| `php_composer` | PHP Composer installed globally to /usr/local/bin |
| `nodejs` | Node.js LTS via NodeSource + npm |
| `nodejs_pm2` | Node.js LTS + PM2 process manager with startup config |
| `python3` | python3 + pip + venv + dev headers |
| `java` | OpenJDK 17 JDK + JAVA_HOME in /etc/environment |
| `java21` | OpenJDK 21 JDK (latest LTS) |
| `ruby` | Ruby + ruby-dev + Bundler gem |
| `golang` | Latest Go binary installed to /usr/local/go |
| `rust` | Rust + Cargo via rustup (non-interactive) |

### App Frameworks

| Shortcut | What gets installed |
|----------|-------------------|
| `laravel` | Nginx + PHP-FPM + Composer + new Laravel project + Nginx vhost |
| `django` | Nginx + Gunicorn + Django + PostgreSQL + systemd service |
| `flask` | Nginx + Gunicorn + Flask + systemd service |
| `nodejs_express` | Node.js + Express + PM2 + Nginx reverse proxy |
| `spring_boot` | Java 17 + Maven + Nginx reverse proxy + systemd service template |

### Dev Tools & CI/CD

| Shortcut | What gets installed |
|----------|-------------------|
| `docker` | Official Docker CE + CLI + containerd + current user in docker group |
| `docker_compose` | Docker Compose plugin |
| `portainer` | Portainer CE in Docker (web UI for containers, port 9443) |
| `git` | Git, version verified |
| `gitea` | Gitea self-hosted Git (binary install + systemd) |
| `jenkins` | Java 17 + Jenkins LTS (port 8080) |
| `gitlab_runner` | Official GitLab Runner |
| `ansible` | Ansible from official repo/PPA |
| `terraform` | Terraform from HashiCorp repo |
| `kubernetes_tools` | kubectl + kubeadm + kubelet from official Kubernetes repo |

### Monitoring & Observability

| Shortcut | What gets installed |
|----------|-------------------|
| `prometheus` | Prometheus binary + systemd service (port 9090) |
| `grafana` | Grafana OSS from official repo (port 3000) |
| `prometheus_grafana` | Full stack: Prometheus + Node Exporter + Grafana all configured together |
| `netdata` | Netdata real-time monitoring via kickstart script (port 19999) |
| `zabbix` | Zabbix 6 LTS server + agent + web frontend + MySQL |
| `node_exporter` | Prometheus Node Exporter binary + systemd (port 9100) |
| `loki` | Grafana Loki + Promtail log aggregation + systemd services |

### Security & VPN

| Shortcut | What gets installed |
|----------|-------------------|
| `certbot` | Certbot + python3-certbot-nginx (Let's Encrypt for Nginx) |
| `certbot_apache` | Certbot + python3-certbot-apache (Let's Encrypt for Apache) |
| `ufw` | UFW firewall: deny incoming, allow SSH/HTTP/HTTPS, enabled |
| `fail2ban` | Fail2ban + SSH jail config (maxretry=5, bantime=1h) |
| `crowdsec` | CrowdSec collaborative security + iptables bouncer |
| `openvpn` | OpenVPN installer script (downloads angristan's script) |
| `wireguard` | WireGuard kernel module + tools + IP forwarding enabled |
| `trivy` | Aqua Trivy container/filesystem vulnerability scanner |

### Self-Hosted Apps

| Shortcut | What gets installed |
|----------|-------------------|
| `n8n` | n8n workflow automation via Node.js + PM2 (port 5678) |
| `uptime_kuma` | Uptime Kuma monitoring via Node.js + PM2 (port 3001) |
| `mattermost` | Mattermost team chat via Docker Compose (port 8065) |
| `vaultwarden` | Vaultwarden (Bitwarden-compatible) via Docker (port 8080) |
| `jellyfin` | Jellyfin media server from official repo (port 8096) |
| `code_server` | code-server (VS Code in browser, port 8080) |

---

## Supported Linux Distributions

| Distribution | Package Manager |
|-------------|----------------|
| Ubuntu 20.04 | apt |
| Ubuntu 22.04 | apt |
| Ubuntu 24.04 | apt |
| Debian 11 | apt |
| Debian 12 | apt |
| CentOS 7 | yum |
| CentOS Stream 8 | dnf |
| CentOS Stream 9 | dnf |
| Rocky Linux 8 | dnf |
| Rocky Linux 9 | dnf |
| AlmaLinux 8 | dnf |
| AlmaLinux 9 | dnf |
| Fedora 38+ | dnf |
| RHEL 8 | dnf |
| RHEL 9 | dnf |
| Arch Linux | pacman |
| openSUSE Leap | zypper |

---

## Config File

Your settings are stored at `~/.linux_agent/config.json`. The file is only readable by your user (permissions `600`).

Example:

```json
{
  "os_name": "Ubuntu 22.04",
  "package_manager": "apt",
  "api_key": "sk-or-v1-xxxxxxxxxxxxxxxxxxxx",
  "model": "openrouter/auto",
  "setup_done": true,
  "lifetime_tokens": {
    "prompt": 11203,
    "completion": 3891,
    "total": 15094,
    "calls": 27
  }
}
```

You can edit this file manually if needed. To reset everything and re-run setup, delete the file:

```bash
rm ~/.linux_agent/config.json
```

---

## Project Structure

```
linux-agent/
├── main.py            Entry point, main loop, CLI argument handling
├── config.py          Reads/writes ~/.linux_agent/config.json (OS, API key)
├── ai_engine.py       OpenRouter API: generate commands, diagnose errors, Q&A
├── executor.py        Runs commands, streams output, permission prompts, auto-fix
├── recipes.py         50+ pre-built installation recipes grouped by category
├── vhost_manager.py   Nginx/Apache virtual host generator + SSL manager
├── script_manager.py  AI bash script writer + cron job manager
├── ui.py              Terminal menus, colors, OS dropdown, banners
├── requirements.txt   Python dependencies (requests only)
├── install.sh         Installer — creates the linuxagent command
└── README.md          This file
```

---

## Getting a Free OpenRouter API Key

1. Open [https://openrouter.ai/keys](https://openrouter.ai/keys) in your browser
2. Click **Sign Up** and create a free account
3. After logging in, click **Create Key**
4. Give it a name like `linux-agent` and click **Create**
5. Copy the key — it starts with `sk-or-`
6. Paste it when the tool asks during first-time setup

The free tier gives you access to several capable AI models at no cost. No credit card is required.

---

## Troubleshooting

**"No API key configured" error**

Run the tool, go to option `7` (Settings), and choose `2` to re-enter your API key.

**"API request failed: 401" error**

Your API key is invalid or expired. Get a new one at [https://openrouter.ai/keys](https://openrouter.ai/keys) and update it via Settings.

**Commands fail with "sudo: command not found"**

Your system may not have sudo installed. Install it first:
```bash
su -c "apt install sudo" root       # Debian/Ubuntu
su -c "yum install sudo" root       # CentOS 7
```

**Python 3 not found**

```bash
# Ubuntu/Debian
apt install python3 python3-pip

# CentOS/RHEL/Rocky/AlmaLinux
dnf install python3 python3-pip

# Arch
pacman -S python python-pip
```

**"requests" module not found**

```bash
pip3 install requests
# or
pip3 install -r ~/linux-agent/requirements.txt
```

**Tool runs but AI generates wrong commands for my OS**

Go to option `7` → Settings → Change OS and make sure you selected the right distribution. The AI uses your saved OS to tailor every command.

**Permission denied writing to `/var/www` or `/etc`**

The tool automatically prefixes commands with `sudo`. Make sure your user is in the `sudo` or `wheel` group:
```bash
usermod -aG sudo your-username      # Debian/Ubuntu
usermod -aG wheel your-username     # CentOS/RHEL
```
Then log out and back in.

**Virtual host config test fails (nginx -t error)**

The AI-generated config may reference a PHP socket path that differs on your OS. Common paths:
```
Ubuntu/Debian:  /run/php/php8.1-fpm.sock
CentOS/RHEL:    /run/php-fpm/www.sock
```
Edit the generated config file and update the `fastcgi_pass` or `proxy_pass` line to the correct socket path, then run `nginx -t` and `systemctl reload nginx` manually.

**Let's Encrypt certbot fails with "domain not pointing to this server"**

Your domain's DNS A record must point to this server's IP before Certbot can issue a certificate. Check with:
```bash
dig +short yourdomain.com
curl ifconfig.me
```
Both must return the same IP.

**Custom SSL certificate — "SSL_CTX_use_PrivateKey_file failed"**

The certificate and private key do not match. Verify they are a pair:
```bash
openssl x509 -noout -modulus -in /path/to/cert.pem | md5sum
openssl rsa  -noout -modulus -in /path/to/key.pem  | md5sum
```
Both md5 hashes must be identical.

**Script written but "Permission denied" when running it**

Make it executable:
```bash
chmod +x /path/to/your/script.sh
```

**Cron job added but not running**

Check that the cron daemon is running:
```bash
systemctl status cron        # Debian/Ubuntu
systemctl status crond       # CentOS/RHEL/Rocky
```
Also check the cron log:
```bash
grep CRON /var/log/syslog          # Debian/Ubuntu
grep cron /var/log/cron            # CentOS/RHEL
```
Make sure the script path in the cron line is absolute and the script is executable.

**vhost command says "a2ensite not found"**

Apache is not installed or `apache2` utilities are missing. Install Apache first:
```bash
python3 main.py install apache
```

---

## Tips

- Press `Ctrl+C` at any time to safely exit the tool
- Use `s` to skip any command you are unsure about — run it manually later
- The custom task mode works for almost anything: "set up swap space", "configure logrotate for nginx", "install and configure Postfix", etc.
- After installing WordPress, visit `http://your-server-ip/wordpress` to complete the browser setup wizard
- After adding a vhost with Let's Encrypt, auto-renewal is configured by Certbot automatically via a systemd timer or cron
- Use `python3 main.py list` to see all recipe shortcut names without opening the menus
- Use `--yes` flag to skip the plan confirmation when you trust the recipe (still prompts per-command)
- Scripts written by the AI are saved with `chmod +x` — they are ready to run immediately
- The AI schedule suggestion for cron works best when the script filename describes its purpose (e.g. `backup_db.sh`, `check_nginx.sh`)
- Custom SSL certificates work with any CA — purchased certs, wildcard certs, or self-signed certs
