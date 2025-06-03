
#### **Step 1: Start the Server**
- Command: `python3 server.py &`
  - Starts the server in the background on `localhost:6379`.
  - The `&` allows the terminal to remain usable.

#### **Step 2: Use `strace` to Log Server Activity**
- **Install `strace` (if not installed):**
  - Commands:
    ```bash
    sudo apt update
    sudo apt install strace
    ```
  - Updates package lists and installs `strace` to trace system calls.
- **Find Server PID:**
  - Commands:
    ```bash
    ps aux | grep python3
    # or
    pidof python3
    ```
  - Identifies the process ID (PID) of the running server (e.g., `38872`).
- **Run `strace`:**
  - Command:
    ```bash
    sudo strace -p 38872 -e trace=accept4,recvmsg,sendmsg -tt
    ```
  - Traces `accept4` (new connection), `recvmsg` (receive commands), and `sendmsg` (send responses) system calls with timestamps (`-tt`).
  - Output shows when the server accepts connections and processes commands, helping confirm blocking behavior.

#### **Step 3: Test with Multiple Clients**
- Open multiple terminal windows.
- In each terminal, run:
  ```bash
  python3 client.py
  ```
  - Enter commands like `SET key value` and `GET key` in the interactive mode.
  - First client connects and holds the server. Subsequent clients will wait (block) until the first client's session ends (e.g., after typing `exit`).
- Check `strace` output:
  - First `accept4` for the initial client, followed by `recvmsg` and `sendmsg`.
  - Next `accept4` appears only after the first client disconnects, proving single-threaded blocking.

#### **Step 4: Handle Port Conflicts**
- **Check if Port 6379 is in Use:**
  - Command:
    ```bash
    sudo netstat -tulnp | grep 6379
    ```
  - Lists processes using port 6379 (shows PID if active).
- **Kill the Conflicting Process:**
  - Command:
    ```bash
    sudo kill -9 <PID>
    ```
  - Replaces `<PID>` with the process ID from the previous step.
- **Restart the Server:**
  - Command:
    ```bash
    python3 server.py &
    ```
  - Starts a fresh server instance.

![alt text](images/image.png)

This image shows a **single-threaded TCP server** where only **one client is served at a time**:

* In the **left terminal**, `strace` shows the server:

  * Accepts one client (`accept4`)
  * Handles `SET` and `GET` commands
  * Only **after** the first client disconnects, it accepts the **next** one

* In the **middle and right terminals**, two clients connect:

  * The **second client (right)** is **blocked** until the **first one (middle)** exits

This proves the server uses a **blocking, single-threaded request-response loop**.


