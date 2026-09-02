import subprocess
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed

from pymongo import MongoClient
from pymongo.errors import (
    ConnectionFailure,
    OperationFailure,
    ServerSelectionTimeoutError,
)


MONGODB_PORT = 27017
TIMEOUT_MS = 3000
MAX_WORKERS = 16


def run_nmap_scan(subnet):
    """
    Scan a subnet for hosts with MongoDB's default port open.

    Uses Nmap XML output instead of scraping human-readable text.
    """
    print(f"[+] Scanning {subnet} for MongoDB instances...")

    command = [
        "nmap",
        "-n",
        "-p", str(MONGODB_PORT),
        "--open",
        "-oX", "-",
        subnet,
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
        )

        root = ET.fromstring(result.stdout)
        hosts = []

        for host in root.findall("host"):
            address = host.find("address")

            if address is None:
                continue

            ip = address.get("addr")

            for port in host.findall("./ports/port"):
                state = port.find("state")

                if (
                    port.get("portid") == str(MONGODB_PORT)
                    and state is not None
                    and state.get("state") == "open"
                ):
                    hosts.append(f"mongodb://{ip}:{MONGODB_PORT}")

        hosts = sorted(set(hosts))

        print(f"[+] Found {len(hosts)} candidate MongoDB host(s)")
        return hosts

    except FileNotFoundError:
        print("[-] Nmap is not installed or not in PATH.")
    except subprocess.CalledProcessError as exc:
        print(f"[-] Nmap failed: {exc.stderr.strip()}")
    except ET.ParseError as exc:
        print(f"[-] Could not parse Nmap output: {exc}")

    return []


def detect_topology(hello):
    if hello.get("msg") == "isdbgrid":
        return "mongos"

    if hello.get("setName"):
        return f"Replica Set ({hello['setName']})"

    return "Standalone"


def inspect_mongodb(uri):
    result = {
        "uri": uri,
        "edition": "Unknown",
        "version": "Unknown",
        "topology": "Unknown",
        "modules": [],
        "error": None,
    }

    client = None

    try:
        client = MongoClient(
            uri,
            serverSelectionTimeoutMS=TIMEOUT_MS,
            connectTimeoutMS=TIMEOUT_MS,
            socketTimeoutMS=TIMEOUT_MS,
            directConnection=True,
        )

        admin = client.admin

        # Confirm MongoDB and determine topology
        hello = admin.command("hello")
        result["topology"] = detect_topology(hello)

        # Direct edition detection
        build_info = admin.command("buildInfo")

        result["version"] = build_info.get("version", "Unknown")
        result["modules"] = build_info.get("modules", [])

        if "enterprise" in result["modules"]:
            result["edition"] = "MongoDB Enterprise"
        else:
            result["edition"] = "MongoDB Community"

    except OperationFailure as exc:
        if exc.code == 13:
            result["edition"] = "Unknown (authentication required)"
            result["error"] = "Authorization required"
        else:
            result["error"] = str(exc)

    except (
        ConnectionFailure,
        ServerSelectionTimeoutError,
    ) as exc:
        result["error"] = f"Connection failed: {exc}"

    except Exception as exc:
        result["error"] = str(exc)

    finally:
        if client:
            client.close()

    return result


def print_result(result):
    print()
    print(f"Host:     {result['uri']}")
    print(f"Edition:  {result['edition']}")
    print(f"Version:  {result['version']}")
    print(f"Topology: {result['topology']}")

    if result["modules"]:
        print(f"Modules:  {', '.join(result['modules'])}")

    if result["error"]:
        print(f"Status:   {result['error']}")


def scan_hosts(hosts):
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(inspect_mongodb, host): host
            for host in hosts
        }

        for future in as_completed(futures):
            print_result(future.result())


def main():
    subnet = input(
        "Enter subnet "
        "(example: 192.168.1.0/24 or localhost): "
    ).strip()

    if subnet.lower() in {"localhost", "127.0.0.1"}:
        hosts = [f"mongodb://127.0.0.1:{MONGODB_PORT}"]
    else:
        hosts = run_nmap_scan(subnet)

    if not hosts:
        print("[-] No MongoDB instances detected.")
        return

    print()
    print("[+] Inspecting MongoDB deployments...")

    scan_hosts(hosts)


if __name__ == "__main__":
    main()
