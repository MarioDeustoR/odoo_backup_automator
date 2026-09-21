# 📦 Odoo Backup Automator

A robust automation tool written in Python to perform unattended downloads of database backups from the Odoo subscription portal. Designed with a strict focus on execution resilience, credential security, and absolute server memory management.

## ✨ Key Features

* **Advanced Anti-Bot Evasion:** Implements `undetected-chromedriver` to bypass Cloudflare barriers and Odoo's native login engine protections.
* **Strict Memory Management (Anti-Zombie):** Prevents memory leaks on Windows systems through selective subprocess termination by PID, complemented by a dynamic PowerShell sweep to kill orphaned Chrome instances associated with the task's profile.
* **Zero-Trust Security:** Access credentials are injected at runtime via system environment variables, completely eliminating hardcoded passwords from the source code.
* **Error Forensic Autopsy:** If execution fails (e.g., network drop or Odoo DOM update), the script generates emergency dumps: a visual screenshot, the page's HTML code, rendered text, and a full stack trace for quick debugging.
* **Autonomous Maintenance:** Automatic file rotation (7-day backup retention) and a protection system to prevent overwriting older backups.

## ⚙️ Prerequisites

* **Python 3.10+**
* **Google Chrome** installed on the system.
* Required dependencies:
  ```bash
  pip install undetected-chromedriver selenium
