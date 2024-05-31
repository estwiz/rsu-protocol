# rsu-protocol


## Installation

1. Generate Certificates
    ```bash
    sh ./certs/generate.sh
    ```

2. Create a virtual environment
    ```bash
    python3 -m venv .venv
    ```
3. Activate the virtual environment
    ```bash
    source ./.venv/bin/activate
    ```
4. Install the requirements
    ```bash
    pip install -r requirements.txt
    ```
5. Generate requirements.txt
    ```bash
    pip freeze > requirements.txt
    ```
