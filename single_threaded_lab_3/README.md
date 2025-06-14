# Building a Single-Threaded TCP Server for Redis from Scratch with Command Parser and RESP Protocol

In this lab, we implement a basic single-threaded TCP server that mimics Redis functionality with a focus on integrating a **Command Parser** and **RESP Protocol**. The server handles one client at a time, processes REPL-like commands (SET, GET, EXPIRE), and includes an in-memory key-value store with expiration logic.

## Objectives

- Implement a **Command Parser** to process REPL-like commands for `SET`, `GET`, and `EXPIRE`.
- Integrate **RESP Protocol** for command and response formatting.

## Workflow Diagram

## Systme Diagram


## Project Structure

```
RedisFromScratch/TCP_Server/
├── server.py       # TCP server implementation with Command Parser and RESP
├── client.py       # Client script for testing
├── images/         # Directory for diagrams
```

## Key Concepts

### Command Parser

**Definition**: A system that breaks down and interprets client-sent commands.

- **Example**: For `SET key value`, the parser identifies:
  - `SET` → Command
  - `key` → Key
  - `value` → Value
- **Role**: Extracts meaningful parts from a string for processing.

### RESP Protocol (Redis Serialization Protocol)

**Definition**: Redis’s custom protocol for sending commands and receiving responses.

- **Format**: Text-based, lightweight, easy to parse.
- **Example**: `*3\r\n$3\r\nSET\r\n$3\r\nkey\r\n$5\r\nvalue\r\n`
  - `*3` → 3 parts
  - `$3` → Next part length is 3 (`SET`)
  - `$3` → Next part length is 3 (`key`)
  - `$5` → Next part length is 5 (`value`)
- **Purpose**: Standardizes communication between client and server.

| Component          | Responsibility                                      |
|--------------------|----------------------------------------------------|
| **Command Parser** | Parses RESP-formatted commands into actionable parts |
| **RESP Protocol**  | Defines the structure for commands and responses    |


## Implementation Details


### 4. Command Parsing with RESP
```python
def parse_resp(self, data: bytes) -> List[str]:
    # Parse RESP array (e.g., *3\r\n$3\r\nSET\r\n...)
    parts = []
    i = 0
    while i < len(data):
        if data[i] == ord('*'):
            i += 2  # Skip * and \n
            count = int(data[i:data.index(b'\r\n', i)])
            i += len(str(count)) + 2
            for _ in range(count):
                i = self.parse_bulk_string(data, i, parts)
        i += 2  # Skip \r\n
    return parts

def parse_bulk_string(self, data: bytes, start: int, parts: List[str]) -> int:
    if data[start] == ord('$'):
        start += 2  # Skip $ and \n
        length = int(data[start:data.index(b'\r\n', start)])
        start += len(str(length)) + 2
        parts.append(data[start:start + length].decode())
        return start + length + 2
    return start
```

**Purpose**: Parses RESP-formatted commands into a list of arguments.

### 5. Command Processing
```python
def process_command(self, command: List[str]) -> str:
    cmd = command[0].upper()
    if cmd == "SET": return self.handle_set(command[1:])
    elif cmd == "GET": return self.handle_get(command[1:])
    return "-ERR unknown command\r\n"
```


## Testing the TCP Server


## Flame Graph Generation & Analysis

### Prerequisites
```bash
sudo apt update
sudo apt install python3-pip
pip install py-spy
```

### Step-by-Step: Generate Flame Graph
1. Start server: `python3 server.py &`
2. Find PID: `pidof python3`
3. Record: `py-spy record -p <PID> -o profile.svg`
4. View: Open `profile.svg` in a browser.


## Conclusion

This project implements a single-threaded TCP server with **Command Parser** and **RESP Protocol**, mimicking Redis. Key features include:
- TCP server with sequential client handling.
- RESP-based command and response handling.
- In-memory store with expiration logic.
- Performance benchmarking and flame graph analysis.
- Verified single-threaded behavior with `strace`.

---