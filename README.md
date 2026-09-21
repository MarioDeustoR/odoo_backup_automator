# 🏢 Odoo Automated Backup System (RPA Script)

> **💡 Repository Note:** This repository outlines a Robotic Process Automation (RPA) script developed to secure database backups from an enterprise Odoo ERP system. It highlights advanced web automation, anti-bot evasion, and autonomous file management techniques.

## 🚀 Project Vision
The goal of this project was to eliminate the manual, time-consuming process of downloading ERP database backups for a real estate firm. By creating a fully autonomous Python script, the system ensures business continuity and strict data security with zero human intervention.

---

## 🧠 Core Technologies

*   **Language:** Python 3
*   **Automation Framework:** Selenium WebDriver
*   **Anti-Bot Evasion:** Undetected Chromedriver
*   **System Operations:** OS, Sys, and Glob modules for automated local file renaming, timestamping, and log generation.

---

## ⚙️ Key Features & Technical Challenges Overcome

*   **Anti-Bot & Security Bypass:** Successfully implemented strategies to bypass Cloudflare's strict bot protection algorithms and navigate Odoo's complex cross-subdomain session management.
*   **Asynchronous DOM Handling:** Designed robust explicit waits (`WebDriverWait`) to handle Single Page Application (SPA) loading states, ensuring the script perfectly times its actions with asynchronous JavaScript rendering.
*   **Advanced Element Interaction:** Utilized JavaScript injection (`execute_script`) to force-scroll and interact with DOM elements hidden behind dynamic overlays or custom web components.
*   **Autonomous Execution & Logging:** The script runs entirely in the background, automatically archives previous backups with precise timestamps to prevent overwriting, and generates detailed execution logs (`log_odoo_{current_date}.txt`) for system administrators.
*   **Memory & Process Management (DevOps):** Engineered a custom PowerShell garbage collection routine within Python to accurately identify and terminate orphaned Chrome processes based on the user-data directory, ensuring zero memory leaks on the host server.
*   **Secure Credential Handling:** Implemented strict OS-level environment variable integration for authentication, completely removing hardcoded credentials from the source code.

---

## 🎯 My Role: Automation Developer / IT Administrator

As the sole developer and IT Administrator for this project, my responsibilities included:

1.  **Process Analysis:** Identifying the bottlenecks in the manual backup workflow and designing a reliable automated logic flow.
2.  **Script Development:** Writing, debugging, and optimizing the Python automation script to handle unpredictable web loading times and strict security measures.
3.  **Security Navigation:** Researching and implementing advanced automation solutions to interact with enterprise-grade web security without being flagged.
4.  **Deployment & Maintenance:** Setting up the script for scheduled execution on local servers, ensuring robust error handling and memory management to prevent zombie processes.
