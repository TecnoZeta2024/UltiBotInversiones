# Supabase DNS and Connection Troubleshooting Guide

## Introduction
Supabase typically manages DNS resolution seamlessly for its default project URLs. When you create a project, Supabase provides you with connection details that should work out-of-the-box. This guide primarily focuses on troubleshooting client-side DNS and connectivity issues that you might encounter when trying to connect to your standard Supabase project URLs (e.g., `your-project-ref.supabase.co`, the direct database URL like `db.your-project-ref.supabase.co`, or the Supabase session pooler URL like `*.pooler.supabase.com`).

Configuration of custom domains (e.g., setting up CNAME or A records for `api.yourdomain.com` to point to your Supabase project) is a separate topic. For guidance on custom domains, please refer to Supabase's official documentation.

## Understanding Your Supabase Connection Information
You can find your Supabase project's connection details by navigating to your project's settings in the Supabase dashboard, then to "Database" settings. Look for the "Connection string" or "Connection info" section.

A typical Supabase PostgreSQL connection string looks like this:
`postgresql://<user>:<password>@<host>:<port>/<database>`

Key components:
-   **User**: Your database user (e.g., `postgres` or a custom role).
-   **Password**: The password for your database user.
-   **Host**: The hostname of the database server. This is the part that DNS resolves.
-   **Port**: The port number for the connection (usually `5432` for PostgreSQL).
-   **Database**: The name of the database to connect to (usually `postgres`).

There are two common patterns for the `<host>`:
1.  **Direct Connection**: `db.your-project-ref.supabase.co`
    *   Replace `your-project-ref` with your actual project reference.
2.  **Session Pooler Connection**: `aws-0-region.pooler.supabase.com` (or similar, like `europe-west-2.pooler.supabase.com`, etc.)
    *   The username format for the pooler is often `postgres.your-project-ref`.
    *   The pooler is recommended for serverless environments and managing a large number of temporary connections.

It is crucial to use the exact hostname, username, password, and port provided in your project settings to avoid connection issues.

## Common Connection Errors and DNS Issues

### 1. "Name or service not known" / "[Errno -2] Name or service not known"
-   **Meaning**: This error indicates that your system (the client attempting to connect) was unable to resolve the Supabase hostname (e.g., `db.your-project-ref.supabase.co`) to an IP address. Essentially, it's a DNS resolution failure. Your computer asked "What IP address is `hostname`?" and didn't get a valid answer.
-   **Potential Causes**:
    -   **Typo in Hostname**: The most common cause. Even a small misspelling will cause DNS lookup to fail.
    -   **Local DNS Cache Issue**: Your operating system or application might have an old, incorrect DNS entry cached.
    -   **Local DNS Server Issues**: The DNS servers configured on your local machine or network router might be experiencing problems or be misconfigured.
    -   **Network Firewall or Security Software**: Firewalls (on your machine or network) or security software can block DNS queries (usually UDP port 53) or access to specific domains.
    -   **ISP DNS Problems**: Your Internet Service Provider's DNS servers might be temporarily down or have issues.
    -   **(Rarely) Supabase DNS Issues**: While unlikely for standard, established URLs, there could theoretically be issues with Supabase's DNS records. Check the official Supabase status page (status.supabase.com).
    -   **Restricted Execution Environments**: CI/CD runners, Docker containers, sandboxed environments (like the one used for automated tasks in some development tools), or corporate networks with strict egress policies might have limited network access or specifically configured DNS resolvers that don't know the public Supabase hostnames.

### 2. "Address family for hostname not supported"
-   **Meaning**: This is a less common and more technical error. It typically means that the DNS lookup was successful (a hostname was resolved to an IP address), but the type of IP address returned (e.g., IPv6) is not compatible with what the application or network stack was expecting or is configured to handle (e.g., it might only be expecting an IPv4 address). It can also point to more fundamental problems in the network configuration of the client system.
-   **Potential Causes**:
    -   Similar to "Name or service not known," but can be more specific to IPv4/IPv6 network stack configurations on the client.
    -   The client application or library might not correctly handle available IP address types (e.g., preferring IPv4 but only getting IPv6, or vice-versa).
    -   Incorrect network interface configurations on the client machine.
    -   Problems within the specific networking libraries or tools being used.

## Troubleshooting Steps

### Step 1: Verify Supabase Hostname and Connection String
-   Carefully compare the hostname, username, password, port, and database name with the details provided in your Supabase project dashboard (Settings -> Database).
-   Check for any typos, extra spaces, or missing characters.
-   If you copied the connection string, paste it into a plain text editor (like Notepad, TextEdit in plain text mode, or VS Code) first to ensure no hidden characters or rich formatting was included.

### Step 2: Basic Network Connectivity
-   Confirm that your machine has a working internet connection.
-   Try browsing a well-known website (e.g., `google.com`).
-   From your terminal, try to `ping 8.8.8.8` (Google's Public DNS) or `curl https://google.com` to test raw internet connectivity.

### Step 3: Test DNS Resolution using Command-Line Tools
These tools directly query DNS servers and can help confirm if your system can resolve the hostname.
-   **`nslookup`**:
    -   Open your terminal (Command Prompt on Windows, Terminal on macOS/Linux).
    -   Type `nslookup your-supabase-hostname` (e.g., `nslookup db.your-project-ref.supabase.co` or `nslookup aws-0-sa-east-1.pooler.supabase.com`).
    -   **Expected Output**: You should see one or more IP addresses listed under "Non-authoritative answer" or similar.
    -   **Error Output**: Messages like "** server can't find your-supabase-hostname: NXDOMAIN" or timeouts indicate a DNS resolution problem.
-   **`dig`** (Common on Linux/macOS; may need installation on Windows):
    -   Type `dig your-supabase-hostname`.
    -   `dig` provides more detailed information. Look for the `ANSWER SECTION` for IP addresses. An empty answer section or error status (like `NXDOMAIN`) indicates a problem.
-   **`ping`**:
    -   Type `ping your-supabase-hostname`.
    -   When you `ping` a hostname, the first thing your system does is try to resolve it to an IP address.
    -   If `ping` reports "unknown host," "cannot resolve," or a similar message, it's a DNS issue.
    -   If it shows an IP address but then says "Request timed out" or "0 packets received," DNS worked, but ICMP (ping) packets are being blocked by a firewall somewhere between your machine and the Supabase server. This is not strictly a DNS issue but a connectivity one.

### Step 4: Check Local DNS Cache
Your OS and even some applications cache DNS results to speed up lookups. If an incorrect entry is cached, it can cause persistent issues.
-   **How to flush DNS cache**:
    -   **Windows**: Open Command Prompt as Administrator and run `ipconfig /flushdns`.
    -   **macOS**: Open Terminal and run `sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder`.
    -   **Linux**: The command depends on your Linux distribution and the DNS service it uses.
        -   For `systemd-resolved`: `sudo systemd-resolve --flush-caches`.
        -   For `nscd` (Name Service Cache Daemon): `sudo /etc/init.d/nscd restart`.
-   After flushing, retry the `nslookup`, `dig`, or `ping` commands.

### Step 5: Check Your System's DNS Configuration
Your computer uses configured DNS servers to perform lookups. These are often automatically assigned by your ISP.
-   You can temporarily switch to well-known public DNS servers to see if your default ones are the problem.
    -   Google Public DNS: `8.8.8.8` and `8.8.4.4`
    -   Cloudflare DNS: `1.1.1.1` and `1.0.0.1`
-   *Disclaimer*: Be cautious when changing network settings. Note your current DNS settings before making any modifications so you can revert if needed. Consult your operating system's documentation for how to change DNS server settings.

### Step 6: Firewall and Security Software
Local firewalls (like Windows Firewall, macOS Firewall, `ufw` on Linux) or third-party antivirus/security suites can sometimes interfere with DNS queries or block connections to specific IP ranges.
-   Temporarily disable these (if it's safe to do so in your current environment and you understand the risks) to test if they are causing the block.
-   Remember to re-enable them immediately after testing.
-   If disabling one of these resolves the issue, you'll need to configure an exception for your Supabase hostname or the application making the connection.

### Step 7: Check `hosts` File
The `hosts` file on your computer allows you to manually map hostnames to IP addresses, overriding DNS server responses.
-   **Location**:
    -   **Windows**: `C:\Windows\System32\drivers\etc\hosts` (requires administrator privileges to edit).
    -   **macOS/Linux**: `/etc/hosts` (requires `sudo` or root privileges to edit).
-   Open this file in a text editor. Look for any lines containing `supabase.co` or your specific project hostname. If you find any, and you don't know why they are there, you can try commenting them out by adding a `#` at the beginning of the line. Be very careful when editing this file.

### Step 8: Test from a Different Network or Device
This is a crucial step to isolate the problem:
-   **Different Device, Same Network**: Try connecting from another computer or smartphone connected to the same Wi-Fi/local network. If it works on another device, the issue is likely specific to your original machine's configuration.
-   **Different Network**: Try connecting your machine to a completely different network (e.g., a mobile hotspot, a friend's Wi-Fi). If it works on a different network, the problem is likely with your primary local network configuration or your ISP.

### Step 9: Environment-Specific Issues
If you are experiencing connection problems in a specific environment:
-   **Corporate Network/VPN**: Businesses often have strict firewalls, proxy servers, and custom DNS configurations. You may need to contact your IT department to allowlist Supabase hostnames or configure proxy settings.
-   **CI/CD Pipelines (e.g., GitHub Actions, GitLab CI)**: Runners for these services might have restricted outbound network access. You may need to configure firewall rules or use service connectors if provided by your CI/CD platform.
-   **Sandboxed Environments (e.g., Docker, virtual machines, automated testing tools)**:
    -   Ensure your Docker container has network configured correctly (e.g., not using `--network none` unless intended, DNS configured within the container).
    -   Virtual machines need their network adapters configured correctly.
    -   Some automated tools or sandboxes might run with highly restricted network permissions, preventing DNS lookups or external connections. This was observed in some diagnostic steps where `ping` failed with "Address family for hostname not supported" or Python scripts failed with "[Errno -2] Name or service not known" for Supabase database hostnames, while `curl` to a general Supabase project URL worked, indicating nuanced network restrictions.

## When to Contact Supabase Support
-   If you have diligently tried the troubleshooting steps above and are confident the issue is not with your local machine, network, or environment configuration.
-   If the official Supabase status page (status.supabase.com) indicates an ongoing incident that might be related to your issue.
-   When contacting support, provide them with a clear description of the problem, the exact Supabase hostname you are trying to connect to, and the troubleshooting steps you have already performed, including the output of commands like `nslookup`, `dig`, and `ping`.

## Conclusion
Most DNS and initial connection issues when working with Supabase are typically rooted in the client-side environment (your machine, local network, or specific execution context). By systematically working through these troubleshooting steps, you can often identify and resolve the problem. Remember to verify connection details meticulously and use command-line tools to get more precise diagnostics.
---
