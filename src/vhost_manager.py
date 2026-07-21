# -*- coding: utf-8 -*-
"""
Virtual Host Manager
====================
Add new Nginx or Apache virtual host config files interactively.
Supports:
  - HTTP-only vhost
  - SSL via Let's Encrypt (Certbot)
  - SSL via custom/own certificate files
Calls the AI to generate the correct config, writes it to disk,
tests the config, and reloads the web server.

Fix applied:
  The previous version wrote vhost configs using bash heredoc syntax inside
  execute_commands(). Any single-quote in the AI-generated config (common in
  comments like "don't" or nginx 'maps') would silently corrupt the file.

  New approach: base64-encode the config content and decode with `base64 -d`
  on the target system. Zero injection risk.
"""

import os
import sys
import base64
from ai_engine import _call_api, _strip_markdown_fences
import config
import ui
from executor import ask_permission, run_command


# ── Helper: safe file write ────────────────────────────────────────────────────

def _make_write_command(content: str, dest_path: str) -> str:
    """
    Build a single shell command that writes *content* to *dest_path*
    safely, using base64 encoding to avoid heredoc injection.
    """
    encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
    return (
        f"bash -c \"echo '{encoded}' | base64 -d | tee {dest_path} > /dev/null\""
    )


# ── AI config generator ────────────────────────────────────────────────────────

def _get_vhost_config_from_ai(
    server: str,
    domain: str,
    doc_root: str,
    ssl_mode: str,
    cert_path: str = "",
    key_path: str = "",
    backend_port: int = 0,
    php_fpm: bool = False,
) -> str:
    """Ask AI to generate a complete vhost config block."""
    os_name = config.get("os_name", "Ubuntu 22.04")

    if server == "nginx":
        extra = ""
        if ssl_mode == "letsencrypt":
            extra = (
                "SSL will be handled by Certbot after this config is in place — "
                "generate an HTTP-only block with a redirect placeholder."
            )
        elif ssl_mode == "custom":
            extra = (
                f"Use SSL certificate at {cert_path} and key at {key_path}. "
                "Include HSTS header."
            )
        if backend_port:
            extra += f" Proxy all requests to http://localhost:{backend_port} (reverse proxy)."
        if php_fpm:
            extra += (
                " Pass PHP files to php-fpm via fastcgi_pass unix:/run/php/php-fpm.sock "
                "(or the correct socket path for the OS)."
            )

        prompt = f"""Generate a complete, production-ready Nginx server block for:
- Domain: {domain}
- Document root: {doc_root}
- OS: {os_name}
- SSL mode: {ssl_mode}
{extra}

Include:
- Correct listen directives (80 and/or 443)
- gzip compression
- security headers (X-Frame-Options, X-Content-Type-Options, Referrer-Policy, etc.)
- access_log and error_log
- index index.html index.php (if PHP)

Return ONLY the raw nginx config text, no markdown fences, no explanation."""

    else:  # apache
        extra = ""
        if ssl_mode == "letsencrypt":
            extra = "SSL will be handled by Certbot — generate HTTP VirtualHost only."
        elif ssl_mode == "custom":
            extra = (
                f"Include SSLCertificateFile {cert_path} and "
                f"SSLCertificateKeyFile {key_path}."
            )
        if backend_port:
            extra += (
                f" Use ProxyPass / http://localhost:{backend_port}/ and ProxyPassReverse."
            )
        if php_fpm:
            extra += (
                " Configure FilesMatch for .php to proxy via "
                "SetHandler proxy:unix:/run/php/php-fpm.sock|fcgi://localhost."
            )

        prompt = f"""Generate a complete, production-ready Apache VirtualHost config for:
- Domain: {domain}
- Document root: {doc_root}
- OS: {os_name}
- SSL mode: {ssl_mode}
{extra}

Include:
- Correct <VirtualHost *:80> (and <VirtualHost *:443> if SSL)
- ServerName and ServerAlias www.{domain}
- DirectoryIndex and AllowOverride All
- security headers via Header set
- ErrorLog and CustomLog
- <Directory> block with correct permissions

Return ONLY the raw Apache config text, no markdown fences, no explanation."""

    messages = [
        {
            "role":    "system",
            "content": "You are a senior Linux sysadmin. Generate exact config file content only.",
        },
        {"role": "user", "content": prompt},
    ]
    raw = _call_api(messages, temperature=0.1)
    return _strip_markdown_fences(raw)


# ── Main interactive flow ──────────────────────────────────────────────────────

def add_vhost():
    ui.section("Add Virtual Host (Nginx / Apache)")

    # 1. Web server
    print("  Which web server?\n  1. Nginx\n  2. Apache")
    while True:
        ws = input("  Choice [1/2]: ").strip()
        if ws == "1":
            server = "nginx"
            break
        elif ws == "2":
            server = "apache"
            break
        print("  Enter 1 or 2.")

    # 2. Domain
    domain = input("  Domain name (e.g. example.com): ").strip()
    if not domain:
        ui.error("Domain cannot be empty.")
        return

    # 3. Document root
    default_root = f"/var/www/{domain}"
    doc_root = input(f"  Document root [{default_root}]: ").strip() or default_root

    # 4. PHP-FPM
    php_ans = input("  Is this a PHP site? [y/n]: ").strip().lower()
    php_fpm = php_ans in ("y", "yes")

    # 5. Reverse proxy?
    proxy_ans = input("  Is this a reverse proxy to a local port? [y/n]: ").strip().lower()
    backend_port = 0
    if proxy_ans in ("y", "yes"):
        port_str     = input("  Backend port (e.g. 3000, 8080): ").strip()
        backend_port = int(port_str) if port_str.isdigit() else 0

    # 6. SSL mode
    print("\n  SSL / HTTPS mode:")
    print("  1. No SSL (HTTP only)")
    print("  2. Let's Encrypt (Certbot) — auto-obtain free certificate")
    print("  3. Custom / own certificate (you already have cert + key files)")
    while True:
        ssl_choice = input("  Choice [1/2/3]: ").strip()
        if ssl_choice in ("1", "2", "3"):
            break
        print("  Enter 1, 2, or 3.")

    ssl_mode  = {"1": "none", "2": "letsencrypt", "3": "custom"}[ssl_choice]
    cert_path = ""
    key_path  = ""

    if ssl_mode == "custom":
        cert_path = input("  Full path to certificate file (e.g. /etc/ssl/certs/cert.pem): ").strip()
        key_path  = input("  Full path to private key file  (e.g. /etc/ssl/private/key.pem): ").strip()

    # 7. Generate config via AI
    ui.info(f"Generating {server} config for {domain} via AI...")
    try:
        vhost_config = _get_vhost_config_from_ai(
            server, domain, doc_root, ssl_mode,
            cert_path, key_path, backend_port, php_fpm,
        )
    except Exception as e:
        ui.error(f"AI error: {e}")
        return

    # 8. Show config and confirm
    ui.section(f"Generated {server.upper()} Config")
    print(vhost_config)
    print()
    confirm = input("  Write this config to disk? [y/n]: ").strip().lower()
    if confirm not in ("y", "yes"):
        ui.warn("Aborted.")
        return

    # 9. Determine config file paths
    if server == "nginx":
        conf_path   = f"/etc/nginx/sites-available/{domain}"
        enable_path = f"/etc/nginx/sites-enabled/{domain}"
    else:
        conf_path   = f"/etc/apache2/sites-available/{domain}.conf"
        enable_path = None

    # 10. Build command list
    write_cmd = _make_write_command(vhost_config, conf_path)

    commands = [
        f"mkdir -p {doc_root}",
        f"chown -R www-data:www-data {doc_root}",
        write_cmd,
    ]

    if server == "nginx":
        commands += [
            f"ln -sf {conf_path} {enable_path}",
            "nginx -t",
            "systemctl reload nginx",
        ]
    else:
        commands += [
            f"a2ensite {domain}.conf",
            "apache2ctl configtest",
            "systemctl reload apache2 || systemctl reload httpd",
        ]

    # Certbot command if chosen
    if ssl_mode == "letsencrypt":
        email = input("  Email for Let's Encrypt notifications: ").strip()
        if server == "nginx":
            commands.append(
                f"certbot --nginx -d {domain} -d www.{domain} "
                f"--non-interactive --agree-tos -m {email}"
            )
        else:
            commands.append(
                f"certbot --apache -d {domain} -d www.{domain} "
                f"--non-interactive --agree-tos -m {email}"
            )

    # Run all commands
    os_name = config.get("os_name")
    pkg_mgr = config.get("package_manager")
    from executor import execute_commands
    execute_commands(commands, os_name, pkg_mgr)

    config.log_audit(
        "VHOST_WRITE",
        f"Server: {server}\n"
        f"Domain: {domain}\n"
        f"Document Root: {doc_root}\n"
        f"SSL Mode: {ssl_mode}\n"
        f"Config Path: {conf_path}\n"
        f"Config Content:\n{vhost_config}"
    )

    ui.success(f"Virtual host for {domain} is live!")
    if ssl_mode == "letsencrypt":
        ui.info("SSL certificate obtained via Let's Encrypt.")
    elif ssl_mode == "custom":
        ui.info(f"SSL configured using your certificate: {cert_path}")


def install_custom_ssl():
    """
    Install a custom SSL certificate for an already-existing vhost.
    Updates the config to add SSL directives.
    """
    ui.section("Install Custom SSL Certificate")
    server = input("  Web server [nginx/apache]: ").strip().lower()
    if server not in ("nginx", "apache"):
        ui.error("Enter 'nginx' or 'apache'.")
        return
    domain    = input("  Domain name: ").strip()
    cert_path = input("  Path to certificate file (.crt or .pem): ").strip()
    key_path  = input("  Path to private key file (.key or .pem): ").strip()
    chain     = input("  Path to CA chain file (leave blank if none): ").strip()

    ui.info("Generating SSL update config via AI...")
    os_name = config.get("os_name", "Ubuntu 22.04")
    conf_file = (
        f"/etc/nginx/sites-available/{domain}"
        if server == "nginx"
        else f"/etc/apache2/sites-available/{domain}.conf"
    )
    prompt = f"""I have an existing {server} virtual host for {domain}.
I want to add SSL using my own certificate files:
  SSLCertificateFile: {cert_path}
  SSLCertificateKeyFile: {key_path}
{"  SSLCertificateChainFile: " + chain if chain else ""}
OS: {os_name}

Generate shell commands (not config) to:
1. Add the SSL listen directive and certificate paths to the existing config at {conf_file} using sed
2. Enable SSL module if apache (a2enmod ssl)
3. Test config and reload {server}

Return a JSON array of command strings only, no markdown."""

    messages = [
        {"role": "system", "content": "You are a sysadmin. Return only a JSON array of shell command strings."},
        {"role": "user",   "content": prompt},
    ]
    try:
        import json
        raw = _call_api(messages, temperature=0.1)
        raw = _strip_markdown_fences(raw)
        commands = json.loads(raw)
    except Exception as e:
        ui.error(f"AI error: {e}")
        return

    from executor import execute_commands
    execute_commands(commands, os_name, config.get("package_manager"))
    ui.success("Custom SSL certificate installed.")
