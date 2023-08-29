# Project Setup

## Prerequisites

Make sure you have Google Chrome installed on your server when running in production.

### Installing Google Chrome

1. If `wget` is not installed, install it:
   ```
   sudo apt install wget
   ```
2. Download the latest stable version of Google Chrome:
   ```
   wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
   ```
3. Install Google Chrome:
   ```
   sudo dpkg -i google-chrome-stable_current_amd64.deb
   ```
4. If any errors occur during installation, run this command to repair:
   ```
   sudo apt-get install -f
   ```
5. Check if Chrome is installed correctly:
   ```
   google-chrome --version
   ```
   or
   ```
   google-chrome-stable --version
   ```

## Configuration

You will need to update the variable values in `settings.py`:

- `DATABASE_URL`: Set this to the proper database URL.
- `PROXY_LIST`: Provide a list of proxies.

## Setting Up Virtual Environment

1. Create a virtual environment:
   ```
   python3 -m venv env
   ```
2. Activate the virtual environment:
   ```
   source env/bin/activate
   ```
3. Install required packages:
   ```
   pip install -r requirements.txt
   ```

## Main Files

The main files for this project are `main_copart.py` and `main_iaai.py`. You can test them by running them directly.

### Scheduling with Cron Jobs

When using on a server or at the production level, you can set up cron jobs to run them periodically.

1. Open the crontab configuration:
   ```
   crontab -e
   ```
2. Add these lines to schedule the scripts:

   - For `main_copart.py` (Every 30 minutes):
     ```
     */30 * * * * python3 /path/to/main_copart.py
     ```
   - For `main_iaai.py` (Every 2 hours between 1:00 AM and 4:00 AM):
     ```
     0 1-4/2 * * * python3 /path/to/main_iaai.py
     ```

Make sure to replace `/path/to/main_*.py` with the appropriate paths.
