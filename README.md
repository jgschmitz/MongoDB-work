# 🍃 MongoDB README

Welcome to **MongoDB** — the document database built for modern applications!

---

## 🧩 Components

- `mongod` – The **database server**
- `mongos` – The **sharding router**
- `mongo` – The **database shell** (interactive JavaScript)

---

## 🛠️ Utilities

- `mongodump` – Create a binary dump of the database  
- `mongorestore` – Restore data from a `mongodump`  
- `mongoexport` – Export a collection to JSON or CSV  
- `mongoimport` – Import JSON, CSV, or TSV data  
- `mongofiles` – Put/get/delete files from **GridFS**  
- `mongostat` – View real-time server stats  
- `bsondump` – Convert BSON files to human-readable output  
- `mongoreplay` – Traffic capture & replay tool  
- `mongotop` – Track read/write time per collection  
- `install_compass` – Installs **MongoDB Compass**

---

## 🏗️ Building from Source

See [docs/building.md](docs/building.md)

---

## 🚀 Running MongoDB

Start the server:

```bash
$ sudo mkdir -p /data/db
$ ./mongod
Launch the shell:

bash
Copy
Edit
$ ./mongo
> help
For more options:

bash
Copy
Edit
$ ./mongod --help
🧭 Installing Compass
Run the script to install Compass:

bash
Copy
Edit
$ ./install_compass
This will download and install MongoDB Compass for your platform.

🔌 Drivers
Find drivers for most languages: 
👉 MongoDB Drivers https://www.mongodb.com/docs/drivers/
Use the mongo shell for administrative tasks.

🐞 Bug Reports
Submit bugs here:
👉 Submit Bug Reports -> https://github.com/mongodb/mongo/wiki/Submit-Bug-Reports

📦 Packaging
Use the package.py script in buildscripts/ to generate RPM or Debian packages.

📚 Documentation
User Manual: https://docs.mongodb.com/manual/

Cloud Hosted (Atlas): https://www.mongodb.com/cloud/atlas

📬 Community & Support
MongoDB Users Google Group

MongoDB Dev Google Group

🎓 Learn MongoDB
Free courses at:
👉 MongoDB University

📄 License
MongoDB is free and open-source.

Releases before Oct 16, 2018: AGPL

Releases after Oct 16, 2018: SSPL v1

See individual source files for license details.
