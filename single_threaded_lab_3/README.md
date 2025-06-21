# Building a Single-Threaded TCP Server for Redis from Scratch with Command Parser and RESP Protocol

In this lab, we implement a basic single-threaded TCP server that mimics Redis functionality with a focus on integrating a **Command Parser** and **RESP Protocol**. The server handles one client at a time, processes REPL-like commands (SET, GET, EXPIRE), and includes an in-memory key-value store with expiration logic.

## Objectives

- Implement a **Command Parser** to process REPL-like commands for `SET`, `GET`, and `EXPIRE`.
- Integrate **RESP Protocol** for command and response formatting.

## Workflow Diagram

## Systme Diagram



**Client**: Creates commands in RESP format and sends them to the server, then parses the RESP responses received from the server and displays them to the user.

**Server**: Parses RESP commands, processes `SET`/`GET` operations, and returns responses in RESP format.

**Interactive Mode**: Allows users to easily input commands, which are internally converted into RESP.

**Benchmark Mode**: Tests performance with large data sizes using the RESP protocol.


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

**RESP Protocol Support**:

* A `parse_resp` function has been added to the server, which parses Redis-style RESP commands (e.g., `*3\r\n$3\r\nSET\r\n$3\r\nkey\r\n$5\r\nvalue\r\n`).
* A `serialize_resp` function has been added to the server, which serializes responses into RESP format (e.g., `+OK\r\n`, `$-1\r\n`, or `$5\r\nvalue\r\n`).
* A `serialize_command` function has been added to the client, which serializes commands into RESP format.
* A `parse_response` function has been added to the client, which parses RESP responses received from the server.



## Testing the TCP Server



### Tools:
#### 1. tcpdump:

Install:

```bash
sudo apt update
sudo apt install tcpdump

```

```bash
sudo tcpdump -i lo port 6379 -A

```

The `-A` flag in `tcpdump` means it will display the **payload (data portion)** in a human-readable ASCII format. 

### Output:
#### ➤ TCP Handshake:

```bash
Flags [S] → client → server (SYN)  
Flags [S.] → server → client (SYN-ACK)  
Flags [.] → client → server (ACK)
```

\==> Redis client connection established.

#### ➤ Redis Command (SET with expiry):

```text
$3
SET
$5
value
$1
2
$2
EX
$1
4
```
This is the Redis command in RESP format: `SET value 2 EX 4` → meaning: set key `"value"` to `2`, and expire it after 4 seconds.

---

#### ➤ Redis Response:

```text
+OK
```

RESP string: `+OK` → Redis confirms that the `SET` command was successful.

---

#### ➤ Later, the GET command:

```text
$3
GET
$5
value
```

\==> Redis responds with:

```text
$1
2
```

Meaning: the key `"value"` still exists with value `2`.

---

#### ➤ Another GET after expiry:

```text
$-1
```

Meaning: the key `"value"` **has expired** and is no longer available → in RESP, this indicates a null value.

---



## Tshark 

Install

```bash
sudo apt update
sudo apt install tshark
```
Run: 

```bash
sudo tshark -i lo port 6379
```

* `-i lo` → captures packets from the loopback interface (localhost).
* `port 6379` → filters to capture only packets on Redis server port 6379.


### Output: 
### TCP connection handshake:

```
    1 0.000000000    127.0.0.1 → 127.0.0.1    TCP 74 53680 → 6379 [SYN] Seq=0 Win=65495 Len=0 MSS=65495 SACK_PERM=1 TSval=1031967534 TSecr=0 WS=128
    2 0.000041309    127.0.0.1 → 127.0.0.1    TCP 74 6379 → 53680 [SYN, ACK] Seq=0 Ack=1 Win=65483 Len=0 MSS=65495 SACK_PERM=1 TSval=1031967534 TSecr=1031967534 WS=128
    3 0.000067611    127.0.0.1 → 127.0.0.1    TCP 66 53680 → 6379 [ACK] Seq=1 Ack=1 Win=65536 Len=0 TSval=1031967534 TSecr=1031967534
```
SYN, SYN-ACK, ACK packets establish the TCP connection between client and server.



### SET command:

```
Received RESP: ['SET', 'name', 'Alice', 'EX', '4']
Sent RESP: OK
```
Client sends SET name Alice EX 4 (set key with 4-second expiry).
Server replies OK.

---

Sure! Here’s the English version of your detailed explanation:

---

### TCP Packet Details (SET Command):

```
    4 17.901485811    127.0.0.1 → 127.0.0.1    TCP 115 53680 → 6379 [PSH, ACK] Seq=1 Ack=1 Win=65536 Len=49 TSval=1031985436 TSecr=1031965434
    5 17.901515688    127.0.0.1 → 127.0.0.1    TCP 66 6379 → 53680 [ACK] Seq=1 Ack=50 Win=65536 Len=0 TSval=1031985436 TSecr=1031985436
    6 17.902601618    127.0.0.1 → 127.0.0.1    TCP 71 6379 → 53680 [PSH, ACK] Seq=1 Ack=50 Win=65536 Len=5 TSval=1031985437 TSecr=1031985436
    7 17.902613856    127.0.0.1 → 127.0.0.1    TCP 66 53680 → 6379 [ACK] Seq=50 Ack=6 Win=65536 Len=0 TSval=1031985437 TSecr=1031985437
```

* The `PSH` flag indicates that data is being sent in this packet.
* The `ACK` packets confirm the data was received successfully.

---

### Redis `GET` Command and Response:

```
Received RESP: ['GET', 'name']
Sent RESP: Alice
```

* Client sends `GET name` to retrieve the value for key `"name"`.
* Server responds with `"Alice"`.

---

### TCP Packet Details (GET Command):

```
    8 20.106670452    127.0.0.1 → 127.0.0.1    TCP 89 53680 → 6379 [PSH, ACK] Seq=50 Ack=6 Win=65536 Len=23 TSval=1031987641 TSecr=1031985437
    9 20.106699736    127.0.0.1 → 127.0.0.1    TCP 66 6379 → 53680 [ACK] Seq=6 Ack=73 Win=65536 Len=0 TSval=1031987641 TSecr=1031987641
   10 20.107039422    127.0.0.1 → 127.0.0.1    TCP 77 6379 → 53680 [PSH, ACK] Seq=6 Ack=73 Win=65536 Len=11 TSval=1031987641 TSecr=1031987641
   11 20.107053054    127.0.0.1 → 127.0.0.1    TCP 66 53680 → 6379 [ACK] Seq=73 Ack=17 Win=65536 Len=0 TSval=1031987641 TSecr=1031987641
```

---

### After GET Command, When Key Has Expired:

```
Received RESP: ['GET', 'name']
Key expired and removed: name
Sent RESP: (nil)
```

* After 4 seconds, the key has expired.
* Server responds with `(nil)` indicating the key is no longer available.

---

### TCP Connection Close:

```
   16 29.708155893    127.0.0.1 → 127.0.0.1    TCP 66 53680 → 6379 [FIN, ACK] Seq=96 Ack=22 Win=65536 Len=0 TSval=1031997243 TSecr=1031992711
   17 29.709572356    127.0.0.1 → 127.0.0.1    TCP 66 6379 → 53680 [FIN, ACK] Seq=22 Ack=97 Win=65536 Len=0 TSval=1031997244 TSecr=1031997243
   18 29.709596888    127.0.0.1 → 127.0.0.1    TCP 66 53680 → 6379 [ACK] Seq=97 Ack=23 Win=65536 Len=0 TSval=1031997244 TSecr=1031997244
```

* FIN packets are exchanged to close the TCP connection gracefully.

---


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