# -*- coding: utf-8 -*-
"""
Pre-built installation recipes — expanded edition.
Each recipe sends a task description to the AI which generates
OS/package-manager-specific commands at runtime.
"""

RECIPES = {

    # =========================================================================
    # WEB SERVERS
    # =========================================================================
    "nginx": {
        "name":        "Nginx Web Server",
        "description": "Install Nginx, start and enable on boot",
        "task":        "Install nginx web server, start the service, enable on boot, open port 80 in firewall if ufw or firewalld is active",
        "category":    "web",
    },
    "apache": {
        "name":        "Apache Web Server",
        "description": "Install Apache (httpd/apache2), start and enable",
        "task":        "Install apache2 or httpd depending on OS, start and enable the service, open port 80 in firewall if active",
        "category":    "web",
    },
    "lamp": {
        "name":        "LAMP Stack",
        "description": "Linux + Apache + MySQL/MariaDB + PHP (classic stack)",
        "task": (
            "Install a complete LAMP stack: "
            "1) Install apache2 or httpd, start and enable, "
            "2) Install mysql-server or mariadb-server, start and enable, "
            "3) Install PHP with extensions: php php-mysql php-xml php-mbstring php-curl php-zip php-gd php-intl php-opcache libapache2-mod-php, "
            "4) Enable Apache mod_rewrite, restart Apache, "
            "5) Create /var/www/html/info.php with phpinfo() to verify"
        ),
        "category":    "web",
    },
    "lemp": {
        "name":        "LEMP Stack",
        "description": "Linux + Nginx + MySQL/MariaDB + PHP-FPM (modern stack)",
        "task": (
            "Install a complete LEMP stack: "
            "1) Install nginx, start and enable, "
            "2) Install mysql-server or mariadb-server, start and enable, "
            "3) Install PHP-FPM with extensions: php-fpm php-mysql php-xml php-mbstring php-curl php-zip php-gd php-intl php-opcache, "
            "4) Configure Nginx to pass PHP requests to php-fpm (create /etc/nginx/sites-available/default with fastcgi_pass), "
            "5) Reload nginx, start php-fpm"
        ),
        "category":    "web",
    },
    "caddy": {
        "name":        "Caddy Web Server",
        "description": "Install Caddy with automatic HTTPS",
        "task":        "Add the official Caddy repository for the OS, install caddy, start and enable the caddy service",
        "category":    "web",
    },

    # =========================================================================
    # CMS / APPLICATIONS
    # =========================================================================
    "wordpress": {
        "name":        "WordPress (Full Stack)",
        "description": "Nginx + PHP + MySQL + WordPress + all extensions",
        "task": (
            "Install a complete WordPress stack: "
            "1) Install nginx, start and enable, "
            "2) Install mysql-server or mariadb-server, start and enable, "
            "3) Install PHP-FPM with: php-fpm php-mysql php-xml php-mbstring php-curl php-zip php-gd php-intl php-soap php-opcache, "
            "4) Install wget unzip curl, "
            "5) Download latest WordPress from https://wordpress.org/latest.tar.gz to /tmp, "
            "6) Extract to /var/www/html/wordpress, "
            "7) Set ownership to www-data:www-data and permissions 755/644, "
            "8) Create MySQL database 'wordpress', user 'wpuser' with password 'WPpass123!', grant all privileges, "
            "9) Copy wp-config-sample.php to wp-config.php, set DB_NAME=wordpress DB_USER=wpuser DB_PASSWORD=WPpass123! using sed, "
            "10) Create Nginx server block for WordPress at /etc/nginx/sites-available/wordpress, symlink to sites-enabled, reload nginx"
        ),
        "category":    "cms",
    },
    "joomla": {
        "name":        "Joomla CMS",
        "description": "Nginx + PHP + MySQL + Joomla",
        "task": (
            "Install Joomla CMS: "
            "1) Install nginx, mysql-server or mariadb-server, PHP-FPM with extensions (php-fpm php-mysql php-xml php-mbstring php-curl php-zip php-gd php-intl php-json), "
            "2) Download latest Joomla from https://downloads.joomla.org/latest to /tmp/joomla.zip, "
            "3) Create /var/www/html/joomla, extract Joomla there, set ownership www-data:www-data, "
            "4) Create MySQL database 'joomla' and user 'joomlauser' with password 'Joomla123!', "
            "5) Create Nginx server block for /var/www/html/joomla, reload nginx"
        ),
        "category":    "cms",
    },
    "drupal": {
        "name":        "Drupal CMS",
        "description": "Nginx + PHP + MySQL + Drupal 10",
        "task": (
            "Install Drupal CMS: "
            "1) Install nginx, mysql-server, PHP-FPM with extensions (php-fpm php-mysql php-xml php-mbstring php-curl php-gd php-zip php-intl php-opcache php-dom), "
            "2) Install composer globally, "
            "3) Run composer create-project drupal/recommended-project /var/www/html/drupal, "
            "4) Set ownership www-data:www-data, "
            "5) Create MySQL database 'drupal' and user 'drupaluser' with password 'Drupal123!', "
            "6) Create Nginx server block for Drupal (with clean URLs), reload nginx"
        ),
        "category":    "cms",
    },
    "ghost": {
        "name":        "Ghost Blog",
        "description": "Node.js blogging platform with Nginx reverse proxy",
        "task": (
            "Install Ghost blogging platform: "
            "1) Install Node.js LTS via NodeSource, "
            "2) Install nginx, start and enable, "
            "3) Install ghost-cli globally: npm install -g ghost-cli, "
            "4) Create directory /var/www/ghost, set ownership to current user, "
            "5) Run ghost install --no-prompt --no-stack --dir /var/www/ghost --url http://localhost --db sqlite3 --process systemd, "
            "6) Create Nginx reverse proxy config for Ghost on port 2368, reload nginx"
        ),
        "category":    "cms",
    },
    "nextcloud": {
        "name":        "Nextcloud",
        "description": "Self-hosted cloud storage (Nginx + PHP + MySQL)",
        "task": (
            "Install Nextcloud: "
            "1) Install nginx, mysql-server or mariadb-server, "
            "2) Install PHP-FPM 8.1+ with extensions: php-fpm php-mysql php-xml php-mbstring php-curl php-zip php-gd php-intl php-bcmath php-imagick php-gmp php-apcu php-redis, "
            "3) Download latest Nextcloud from https://download.nextcloud.com/server/releases/latest.tar.bz2, "
            "4) Extract to /var/www/html/nextcloud, set ownership www-data:www-data, "
            "5) Create MySQL database 'nextcloud' and user 'ncuser' with password 'NCpass123!', "
            "6) Create Nginx server block for Nextcloud with correct headers and PHP-FPM, reload nginx"
        ),
        "category":    "cms",
    },
    "matomo": {
        "name":        "Matomo Analytics",
        "description": "Self-hosted web analytics (Nginx + PHP + MySQL)",
        "task": (
            "Install Matomo analytics: "
            "1) Install nginx, mysql-server, PHP-FPM with extensions (php-fpm php-mysql php-xml php-mbstring php-curl php-gd php-zip), "
            "2) Download latest Matomo from https://builds.matomo.org/matomo.zip to /tmp, "
            "3) Extract to /var/www/html/matomo, set ownership www-data:www-data, "
            "4) Create MySQL database 'matomo' and user 'matomouser' with password 'Matomo123!', "
            "5) Create Nginx server block for Matomo, reload nginx"
        ),
        "category":    "cms",
    },

    # =========================================================================
    # DATABASES
    # =========================================================================
    "mysql": {
        "name":        "MySQL Server",
        "description": "Install MySQL/MariaDB, start and secure",
        "task":        "Install mysql-server or mariadb-server, start and enable the service, run mysql_secure_installation steps non-interactively (remove test db, disallow remote root)",
        "category":    "database",
    },
    "postgresql": {
        "name":        "PostgreSQL",
        "description": "Install PostgreSQL, start and enable",
        "task":        "Install postgresql and postgresql-contrib, initialize the cluster if required, start and enable the service, verify with psql --version",
        "category":    "database",
    },
    "mongodb": {
        "name":        "MongoDB",
        "description": "Add official repo, install MongoDB, start and enable",
        "task":        "Add the official MongoDB repository GPG key and repo file for the OS version, install mongodb-org, start mongod, enable on boot",
        "category":    "database",
    },
    "redis": {
        "name":        "Redis",
        "description": "Install Redis, start and enable",
        "task":        "Install redis or redis-server, start the service, enable on boot, verify with redis-cli ping",
        "category":    "database",
    },
    "elasticsearch": {
        "name":        "Elasticsearch",
        "description": "Add Elastic repo, install Elasticsearch 8.x",
        "task":        "Add the official Elastic repository and GPG key, install elasticsearch, start and enable the service, verify it responds on localhost:9200",
        "category":    "database",
    },
    "influxdb": {
        "name":        "InfluxDB",
        "description": "Time-series database for metrics",
        "task":        "Add the official InfluxData repository for the OS, install influxdb2, start and enable the service",
        "category":    "database",
    },
    "memcached": {
        "name":        "Memcached",
        "description": "In-memory caching daemon",
        "task":        "Install memcached, start and enable the service",
        "category":    "database",
    },
    "rabbitmq": {
        "name":        "RabbitMQ",
        "description": "Message broker with management plugin",
        "task":        "Add the RabbitMQ repository and Erlang repository for the OS, install erlang and rabbitmq-server, start and enable rabbitmq-server, enable the rabbitmq_management plugin",
        "category":    "database",
    },

    # =========================================================================
    # RUNTIMES & LANGUAGES
    # =========================================================================
    "php": {
        "name":        "PHP + FPM + Extensions",
        "description": "PHP-FPM with all common extensions",
        "task":        "Install php php-fpm php-cli php-mysql php-xml php-mbstring php-curl php-zip php-gd php-intl php-json php-opcache php-bcmath php-imagick, start php-fpm, enable on boot",
        "category":    "runtime",
    },
    "php_composer": {
        "name":        "PHP Composer",
        "description": "Install PHP Composer globally",
        "task":        "Download composer installer from https://getcomposer.org/installer, run it with php, move composer.phar to /usr/local/bin/composer, make executable, verify with composer --version",
        "category":    "runtime",
    },
    "nodejs": {
        "name":        "Node.js LTS",
        "description": "Install Node.js LTS via NodeSource + npm",
        "task":        "Install Node.js LTS using the official NodeSource setup script for the OS and distribution version, install nodejs and npm, verify with node --version and npm --version",
        "category":    "runtime",
    },
    "nodejs_pm2": {
        "name":        "Node.js LTS + PM2",
        "description": "Node.js with PM2 process manager",
        "task":        "Install Node.js LTS via NodeSource, install pm2 globally with npm, run pm2 startup to configure boot persistence",
        "category":    "runtime",
    },
    "python3": {
        "name":        "Python 3 + pip + venv",
        "description": "Python 3 with pip and virtualenv",
        "task":        "Install python3 python3-pip python3-venv python3-dev, verify with python3 --version and pip3 --version",
        "category":    "runtime",
    },
    "java": {
        "name":        "Java 17 (OpenJDK)",
        "description": "Install OpenJDK 17 JDK",
        "task":        "Install openjdk-17-jdk or java-17-openjdk-devel, set JAVA_HOME in /etc/environment, verify with java -version",
        "category":    "runtime",
    },
    "java21": {
        "name":        "Java 21 (OpenJDK LTS)",
        "description": "Install OpenJDK 21 JDK",
        "task":        "Install openjdk-21-jdk or java-21-openjdk-devel, set JAVA_HOME in /etc/environment, verify with java -version",
        "category":    "runtime",
    },
    "ruby": {
        "name":        "Ruby + Bundler",
        "description": "Install Ruby and Bundler gem",
        "task":        "Install ruby ruby-dev or ruby-devel, install bundler with gem install bundler, verify with ruby --version",
        "category":    "runtime",
    },
    "golang": {
        "name":        "Go (Golang)",
        "description": "Install latest Go from official binary",
        "task":        "Download the latest Go tarball from https://go.dev/dl/ for linux amd64, extract to /usr/local/go, add /usr/local/go/bin to PATH in /etc/profile.d/go.sh, verify with go version",
        "category":    "runtime",
    },
    "rust": {
        "name":        "Rust + Cargo",
        "description": "Install Rust via rustup",
        "task":        "Install curl if not present, run the rustup installer non-interactively: curl -sSf https://sh.rustup.rs | sh -s -- -y, add ~/.cargo/bin to PATH, verify with rustc --version",
        "category":    "runtime",
    },

    # =========================================================================
    # FRAMEWORKS & APP SERVERS
    # =========================================================================
    "laravel": {
        "name":        "Laravel (PHP Framework)",
        "description": "Nginx + PHP + Composer + Laravel project scaffold",
        "task": (
            "Set up a Laravel environment: "
            "1) Install nginx, mysql-server, PHP-FPM with extensions (php-fpm php-mysql php-xml php-mbstring php-curl php-zip php-gd php-intl php-bcmath php-opcache), "
            "2) Install Composer globally, "
            "3) Create a new Laravel project at /var/www/html/laravel using composer create-project laravel/laravel, "
            "4) Set ownership www-data:www-data, set storage/ and bootstrap/cache/ to 775, "
            "5) Create .env from .env.example, generate APP_KEY with php artisan key:generate, "
            "6) Create Nginx server block for Laravel (with try_files and php-fpm), reload nginx"
        ),
        "category":    "framework",
    },
    "django": {
        "name":        "Django (Python Framework)",
        "description": "Nginx + Gunicorn + Django + PostgreSQL",
        "task": (
            "Set up a Django environment: "
            "1) Install python3 python3-pip python3-venv, "
            "2) Install nginx, start and enable, "
            "3) Install postgresql, start and enable, "
            "4) Create /var/www/django, create virtualenv /var/www/django/venv, "
            "5) Install django gunicorn psycopg2-binary in the venv, "
            "6) Create a sample Django project with django-admin startproject, "
            "7) Create systemd service for gunicorn at /etc/systemd/system/gunicorn.service, "
            "8) Create Nginx reverse proxy config for gunicorn on unix socket, reload nginx"
        ),
        "category":    "framework",
    },
    "flask": {
        "name":        "Flask (Python Framework)",
        "description": "Nginx + Gunicorn + Flask app",
        "task": (
            "Set up a Flask environment: "
            "1) Install python3 python3-pip python3-venv, "
            "2) Install nginx, start and enable, "
            "3) Create /var/www/flask, create virtualenv, "
            "4) Install flask gunicorn in the venv, "
            "5) Create a minimal app.py with a hello world route, "
            "6) Create systemd service for gunicorn, enable and start it, "
            "7) Create Nginx reverse proxy config for gunicorn, reload nginx"
        ),
        "category":    "framework",
    },
    "nodejs_express": {
        "name":        "Node.js Express App",
        "description": "Nginx reverse proxy + Node.js + Express",
        "task": (
            "Set up an Express.js environment: "
            "1) Install Node.js LTS via NodeSource, "
            "2) Install nginx, start and enable, "
            "3) Create /var/www/nodeapp, run npm init -y, npm install express, "
            "4) Create a minimal server.js listening on port 3000, "
            "5) Install pm2 globally, start server.js with pm2, save and configure pm2 startup, "
            "6) Create Nginx reverse proxy config for localhost:3000, reload nginx"
        ),
        "category":    "framework",
    },
    "spring_boot": {
        "name":        "Spring Boot (Java)",
        "description": "Java 17 + Maven + Nginx reverse proxy for Spring Boot",
        "task": (
            "Set up a Spring Boot environment: "
            "1) Install openjdk-17-jdk, "
            "2) Install maven, "
            "3) Install nginx, start and enable, "
            "4) Create Nginx reverse proxy config pointing to localhost:8080, reload nginx, "
            "5) Create a systemd service template for running a Spring Boot jar at /opt/app/app.jar"
        ),
        "category":    "framework",
    },

    # =========================================================================
    # DEV TOOLS & CI/CD
    # =========================================================================
    "docker": {
        "name":        "Docker CE",
        "description": "Official Docker CE + CLI + containerd",
        "task":        "Add the official Docker repository GPG key and repo for the OS, install docker-ce docker-ce-cli containerd.io docker-buildx-plugin, start and enable docker, add current user to docker group",
        "category":    "devtools",
    },
    "docker_compose": {
        "name":        "Docker Compose",
        "description": "Install Docker Compose plugin",
        "task":        "Install docker-compose-plugin from the Docker repository, verify with docker compose version",
        "category":    "devtools",
    },
    "portainer": {
        "name":        "Portainer CE (Docker UI)",
        "description": "Web UI for managing Docker containers",
        "task": (
            "Install Portainer CE: "
            "1) Ensure Docker is installed and running, "
            "2) Create Docker volume: docker volume create portainer_data, "
            "3) Run Portainer container: docker run -d -p 8000:8000 -p 9443:9443 --name portainer --restart=always -v /var/run/docker.sock:/var/run/docker.sock -v portainer_data:/data portainer/portainer-ce:latest"
        ),
        "category":    "devtools",
    },
    "git": {
        "name":        "Git",
        "description": "Install latest Git",
        "task":        "Install git, verify with git --version",
        "category":    "devtools",
    },
    "gitea": {
        "name":        "Gitea (Self-hosted Git)",
        "description": "Lightweight self-hosted Git service",
        "task": (
            "Install Gitea: "
            "1) Install git, "
            "2) Create system user 'git' with home /home/git, "
            "3) Download latest Gitea binary from https://dl.gitea.com/gitea/latest/gitea-latest-linux-amd64 to /usr/local/bin/gitea, make executable, "
            "4) Create directories /var/lib/gitea /etc/gitea with correct ownership, "
            "5) Create systemd service for Gitea, enable and start it"
        ),
        "category":    "devtools",
    },
    "jenkins": {
        "name":        "Jenkins CI",
        "description": "Add Jenkins repo, install Jenkins + Java",
        "task":        "Install Java 17 (openjdk-17-jdk), add the official Jenkins LTS repository and GPG key for the OS, install jenkins, start and enable the service. Jenkins runs on port 8080",
        "category":    "devtools",
    },
    "gitlab_runner": {
        "name":        "GitLab Runner",
        "description": "Install and register GitLab Runner",
        "task":        "Add the official GitLab Runner repository for the OS, install gitlab-runner, start and enable the service",
        "category":    "devtools",
    },
    "ansible": {
        "name":        "Ansible",
        "description": "Install Ansible from official PPA/repo",
        "task":        "Install ansible using the official method for the OS (PPA for Ubuntu/Debian, EPEL for RHEL/CentOS, dnf for Fedora), verify with ansible --version",
        "category":    "devtools",
    },
    "terraform": {
        "name":        "Terraform",
        "description": "Install Terraform from HashiCorp repo",
        "task":        "Add the official HashiCorp repository and GPG key for the OS, install terraform, verify with terraform --version",
        "category":    "devtools",
    },
    "kubernetes_tools": {
        "name":        "Kubernetes Tools (kubectl + kubeadm)",
        "description": "Install kubectl and kubeadm from official repo",
        "task":        "Add the official Kubernetes apt/yum repository, install kubelet kubeadm kubectl, hold/pin their versions, verify with kubectl version --client",
        "category":    "devtools",
    },

    # =========================================================================
    # MONITORING & OBSERVABILITY
    # =========================================================================
    "prometheus": {
        "name":        "Prometheus",
        "description": "Download and install Prometheus + systemd service",
        "task": (
            "Install Prometheus: "
            "1) Create system user 'prometheus', create directories /etc/prometheus /var/lib/prometheus, "
            "2) Download latest Prometheus tarball for linux amd64 from https://github.com/prometheus/prometheus/releases/latest, "
            "3) Extract and move prometheus promtool to /usr/local/bin, move config files to /etc/prometheus, "
            "4) Set correct ownership, create basic prometheus.yml config, "
            "5) Create systemd service file, enable and start prometheus. Runs on port 9090"
        ),
        "category":    "monitoring",
    },
    "grafana": {
        "name":        "Grafana",
        "description": "Add Grafana repo, install Grafana OSS",
        "task":        "Add the official Grafana repository and GPG key for the OS, install grafana, start and enable grafana-server. Grafana runs on port 3000",
        "category":    "monitoring",
    },
    "prometheus_grafana": {
        "name":        "Prometheus + Grafana Stack",
        "description": "Full monitoring stack: Prometheus + Node Exporter + Grafana",
        "task": (
            "Install full Prometheus + Grafana monitoring stack: "
            "1) Create system user prometheus, "
            "2) Download and install Prometheus latest for linux amd64, create systemd service on port 9090, "
            "3) Download and install Node Exporter latest for linux amd64, create systemd service on port 9100, "
            "4) Add Node Exporter scrape job to prometheus.yml, "
            "5) Add Grafana repository and install grafana, start on port 3000, "
            "6) Enable and start all three services"
        ),
        "category":    "monitoring",
    },
    "netdata": {
        "name":        "Netdata",
        "description": "Real-time server monitoring dashboard",
        "task":        "Install Netdata using the official kickstart script: bash <(curl -Ss https://my-netdata.io/kickstart.sh) --non-interactive. Netdata runs on port 19999",
        "category":    "monitoring",
    },
    "zabbix": {
        "name":        "Zabbix Server",
        "description": "Enterprise monitoring: Zabbix server + agent + web",
        "task": (
            "Install Zabbix 6 LTS: "
            "1) Download and install the Zabbix release package for the OS, "
            "2) Install zabbix-server-mysql zabbix-frontend-php zabbix-apache-conf zabbix-sql-scripts zabbix-agent, "
            "3) Install mysql-server, create database 'zabbix' and user 'zabbix' with password 'Zabbix123!', import Zabbix schema, "
            "4) Configure /etc/zabbix/zabbix_server.conf with DB credentials, "
            "5) Start and enable zabbix-server zabbix-agent apache2 (or httpd)"
        ),
        "category":    "monitoring",
    },
    "node_exporter": {
        "name":        "Prometheus Node Exporter",
        "description": "Export system metrics for Prometheus",
        "task": (
            "Install Node Exporter: "
            "1) Create system user node_exporter, "
            "2) Download latest node_exporter tarball for linux amd64 from GitHub releases, "
            "3) Extract and move node_exporter binary to /usr/local/bin, set ownership, "
            "4) Create systemd service on port 9100, enable and start it"
        ),
        "category":    "monitoring",
    },
    "loki": {
        "name":        "Grafana Loki (Log Aggregation)",
        "description": "Install Loki + Promtail for log collection",
        "task": (
            "Install Grafana Loki and Promtail: "
            "1) Create system user loki, "
            "2) Download latest loki and promtail binaries for linux amd64 from GitHub releases, "
            "3) Install to /usr/local/bin, create config dirs /etc/loki /etc/promtail, "
            "4) Create basic loki-config.yaml and promtail-config.yaml, "
            "5) Create systemd services for loki (port 3100) and promtail, enable and start both"
        ),
        "category":    "monitoring",
    },

    # =========================================================================
    # SECURITY
    # =========================================================================
    "certbot": {
        "name":        "Certbot (Let's Encrypt SSL)",
        "description": "Install Certbot with Nginx plugin",
        "task":        "Install certbot python3-certbot-nginx or certbot-nginx depending on OS, verify certbot --version",
        "category":    "security",
    },
    "certbot_apache": {
        "name":        "Certbot for Apache",
        "description": "Install Certbot with Apache plugin",
        "task":        "Install certbot python3-certbot-apache or certbot-apache depending on OS, verify certbot --version",
        "category":    "security",
    },
    "ufw": {
        "name":        "UFW Firewall",
        "description": "UFW with SSH + HTTP + HTTPS rules",
        "task":        "Install ufw, set default deny incoming allow outgoing, allow 22/tcp (SSH), allow 80/tcp, allow 443/tcp, enable ufw non-interactively with --force flag",
        "category":    "security",
    },
    "fail2ban": {
        "name":        "Fail2ban",
        "description": "Brute-force SSH and web protection",
        "task":        "Install fail2ban, start and enable the service, create /etc/fail2ban/jail.local with SSH jail enabled (maxretry=5 bantime=3600)",
        "category":    "security",
    },
    "crowdsec": {
        "name":        "CrowdSec",
        "description": "Modern collaborative security engine",
        "task":        "Add the CrowdSec repository for the OS, install crowdsec and the crowdsec-firewall-bouncer-iptables, start and enable the service",
        "category":    "security",
    },
    "openvpn": {
        "name":        "OpenVPN Server",
        "description": "Install OpenVPN using angristan's script",
        "task": (
            "Install OpenVPN using the automated installer: "
            "1) Install curl wget, "
            "2) Download https://raw.githubusercontent.com/angristan/openvpn-install/master/openvpn-install.sh to /tmp/openvpn-install.sh, "
            "3) Make it executable. Note: script requires interactive input for VPN config — run manually: bash /tmp/openvpn-install.sh"
        ),
        "category":    "security",
    },
    "wireguard": {
        "name":        "WireGuard VPN",
        "description": "Install WireGuard kernel module and tools",
        "task":        "Install wireguard wireguard-tools, enable IP forwarding in /etc/sysctl.conf (net.ipv4.ip_forward=1), apply with sysctl -p",
        "category":    "security",
    },
    "trivy": {
        "name":        "Trivy (Container Security Scanner)",
        "description": "Vulnerability scanner for containers and filesystems",
        "task":        "Add the Aqua Security Trivy repository for the OS, install trivy, verify with trivy --version",
        "category":    "security",
    },

    # =========================================================================
    # SELF-HOSTED APPS
    # =========================================================================
    "n8n": {
        "name":        "n8n (Workflow Automation)",
        "description": "Self-hosted n8n via Node.js + PM2",
        "task": (
            "Install n8n workflow automation: "
            "1) Install Node.js LTS via NodeSource, "
            "2) Install n8n globally: npm install -g n8n, "
            "3) Install pm2 globally, "
            "4) Start n8n with pm2: pm2 start n8n -- start, save pm2 config, run pm2 startup, "
            "5) n8n runs on port 5678"
        ),
        "category":    "selfhosted",
    },
    "uptime_kuma": {
        "name":        "Uptime Kuma",
        "description": "Self-hosted uptime monitoring tool",
        "task": (
            "Install Uptime Kuma: "
            "1) Install Node.js LTS and git, "
            "2) Clone https://github.com/louislam/uptime-kuma to /opt/uptime-kuma, "
            "3) Run npm run setup in the directory, "
            "4) Install pm2, start uptime-kuma with pm2: pm2 start server/server.js --name uptime-kuma, "
            "5) Save pm2 and configure startup. Uptime Kuma runs on port 3001"
        ),
        "category":    "selfhosted",
    },
    "mattermost": {
        "name":        "Mattermost (Team Chat)",
        "description": "Self-hosted Slack alternative (Docker)",
        "task": (
            "Install Mattermost using Docker Compose: "
            "1) Ensure Docker and Docker Compose are installed, "
            "2) Create /opt/mattermost, "
            "3) Download the official Mattermost docker-compose.yml from https://raw.githubusercontent.com/mattermost/docker/main/docker-compose.yml to /opt/mattermost, "
            "4) Create .env with required variables, "
            "5) Run docker compose up -d in /opt/mattermost. Mattermost runs on port 8065"
        ),
        "category":    "selfhosted",
    },
    "vaultwarden": {
        "name":        "Vaultwarden (Password Manager)",
        "description": "Lightweight Bitwarden-compatible server (Docker)",
        "task": (
            "Install Vaultwarden: "
            "1) Ensure Docker is installed, "
            "2) Create /opt/vaultwarden/data, "
            "3) Run: docker run -d --name vaultwarden -v /opt/vaultwarden/data:/data -p 8080:80 --restart unless-stopped vaultwarden/server:latest"
        ),
        "category":    "selfhosted",
    },
    "jellyfin": {
        "name":        "Jellyfin Media Server",
        "description": "Self-hosted media streaming server",
        "task":        "Add the official Jellyfin repository for the OS, install jellyfin, start and enable jellyfin service. Jellyfin runs on port 8096",
        "category":    "selfhosted",
    },
    "code_server": {
        "name":        "code-server (VS Code in Browser)",
        "description": "Run VS Code in browser via code-server",
        "task": (
            "Install code-server: "
            "1) Download and run the official installer: curl -fsSL https://code-server.dev/install.sh | sh, "
            "2) Start and enable code-server@$USER service, "
            "3) Set a password in ~/.config/code-server/config.yaml. Runs on port 8080"
        ),
        "category":    "selfhosted",
    },
}


# =========================================================================
# CATEGORY DEFINITIONS (display labels for menus)
# =========================================================================
CATEGORIES = {
    "web":        "Web Servers",
    "cms":        "CMS & Applications",
    "database":   "Databases & Message Queues",
    "runtime":    "Runtimes & Languages",
    "framework":  "App Frameworks",
    "devtools":   "Dev Tools & CI/CD",
    "monitoring": "Monitoring & Observability",
    "security":   "Security & VPN",
    "selfhosted": "Self-Hosted Apps",
}


def get_recipes_by_category() -> dict:
    """Return recipes grouped by category."""
    grouped = {cat: {} for cat in CATEGORIES}
    for key, recipe in RECIPES.items():
        cat = recipe.get("category", "devtools")
        grouped.setdefault(cat, {})[key] = recipe
    return grouped
