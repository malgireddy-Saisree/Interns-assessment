import sqlite3

conn = sqlite3.connect("stayease.db")
cur = conn.cursor()
cur.execute("PRAGMA foreign_keys = ON")

cur.executescript("""

CREATE TABLE IF NOT EXISTS hotels (
    hotel_id            TEXT PRIMARY KEY,
    name                TEXT NOT NULL,
    location            TEXT,
    type                TEXT,
    address             TEXT,
    phone               TEXT,
    email               TEXT,
    rating              REAL,
    check_in_time       TEXT,
    check_out_time      TEXT,
    amenities           TEXT,
    free_cancel_hours   INTEGER,
    partial_refund_pct  INTEGER,
    partial_refund_hours INTEGER,
    no_refund_hours     INTEGER
);

CREATE TABLE IF NOT EXISTS room_types (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    hotel_id        TEXT NOT NULL,
    room_type       TEXT NOT NULL,
    description     TEXT,
    max_occupancy   INTEGER,
    price_per_night REAL,
    total_rooms     INTEGER,
    amenities       TEXT,
    FOREIGN KEY (hotel_id) REFERENCES hotels(hotel_id)
);

CREATE TABLE IF NOT EXISTS services (
    service_id  TEXT PRIMARY KEY,
    hotel_id    TEXT NOT NULL,
    name        TEXT NOT NULL,
    price       REAL,
    description TEXT,
    FOREIGN KEY (hotel_id) REFERENCES hotels(hotel_id)
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id     TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    email           TEXT UNIQUE,
    phone           TEXT,
    loyalty_tier    TEXT    DEFAULT 'bronze',
    loyalty_points  INTEGER DEFAULT 0,
    total_stays     INTEGER DEFAULT 0,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bookings (
    booking_id           TEXT PRIMARY KEY,
    customer_id          TEXT NOT NULL,
    hotel_id             TEXT NOT NULL,
    room_type            TEXT NOT NULL,
    check_in             DATE NOT NULL,
    check_out            DATE NOT NULL,
    nights               INTEGER,
    guests               INTEGER,
    room_price_per_night REAL,
    total_room_cost      REAL,
    total_services_cost  REAL    DEFAULT 0,
    grand_total          REAL,
    amount_paid          REAL    DEFAULT 0,
    status               TEXT    DEFAULT 'confirmed',
    payment_method       TEXT,
    payment_status       TEXT    DEFAULT 'pending',
    refund_amount        REAL    DEFAULT 0,
    refund_date          TIMESTAMP,
    special_requests     TEXT,
    created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (hotel_id)    REFERENCES hotels(hotel_id)
);

CREATE TABLE IF NOT EXISTS booking_services (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id  TEXT NOT NULL,
    service_id  TEXT NOT NULL,
    quantity    INTEGER DEFAULT 1,
    cost        REAL,
    FOREIGN KEY (booking_id) REFERENCES bookings(booking_id),
    FOREIGN KEY (service_id) REFERENCES services(service_id)
);

CREATE TABLE IF NOT EXISTS complaints (
    complaint_id    TEXT PRIMARY KEY,
    booking_id      TEXT NOT NULL,
    customer_id     TEXT NOT NULL,
    hotel_id        TEXT NOT NULL,
    type            TEXT,
    description     TEXT,
    status          TEXT DEFAULT 'open',
    priority        TEXT DEFAULT 'medium',
    assigned_to     TEXT,
    resolution_note TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at     TIMESTAMP,
    FOREIGN KEY (booking_id)  REFERENCES bookings(booking_id),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    FOREIGN KEY (hotel_id)    REFERENCES hotels(hotel_id)
);

CREATE TABLE IF NOT EXISTS refunds (
    refund_id    TEXT PRIMARY KEY,
    booking_id   TEXT NOT NULL,
    customer_id  TEXT NOT NULL,
    amount       REAL,
    reason       TEXT,
    status       TEXT DEFAULT 'pending',
    initiated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (booking_id)  REFERENCES bookings(booking_id),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE IF NOT EXISTS escalations (
    escalation_id        TEXT PRIMARY KEY,
    booking_id           TEXT,
    customer_id          TEXT NOT NULL,
    reason               TEXT,
    conversation_summary TEXT,
    status               TEXT DEFAULT 'open',
    assigned_agent       TEXT,
    created_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at          TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE IF NOT EXISTS audit_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name  TEXT,
    record_id   TEXT,
    action      TEXT,
    changed_by  TEXT DEFAULT 'agent',
    old_value   TEXT,
    new_value   TEXT,
    timestamp   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

""")

# HOTELS
cur.executemany("INSERT OR IGNORE INTO hotels VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", [
    ("H001","StayEase City Grand","Hyderabad, Telangana","city",
     "Road No. 12, Banjara Hills, Hyderabad - 500034",
     "+91-40-12345678","citygrand@stayease.com",4.5,"14:00","12:00",
     "Free WiFi,Swimming Pool,Gym,Restaurant,Spa,Airport Transfer,Conference Room,Valet Parking",
     48,50,24,24),
    ("H002","StayEase Beach Resort","Vizag, Andhra Pradesh","beach",
     "Beach Road, Rushikonda, Visakhapatnam - 530045",
     "+91-891-98765432","beachresort@stayease.com",4.7,"15:00","11:00",
     "Free WiFi,Private Beach,Infinity Pool,Gym,Restaurant,Bar,Water Sports,Kids Club",
     72,40,48,48),
])

# ROOM TYPES
cur.executemany(
    "INSERT OR IGNORE INTO room_types (hotel_id,room_type,description,max_occupancy,price_per_night,total_rooms,amenities) VALUES (?,?,?,?,?,?,?)", [
    ("H001","standard","Cozy room with city view, 1 queen bed",2,3500,30,"AC,TV,WiFi,Mini Fridge"),
    ("H001","deluxe","Spacious room with panoramic city view, 1 king bed",2,5500,20,"AC,Smart TV,WiFi,Mini Bar,Bathtub"),
    ("H001","suite","Luxury suite with separate living area, 2 bedrooms",4,9500,10,"AC,Smart TV,WiFi,Mini Bar,Jacuzzi,Butler Service"),
    ("H002","standard","Garden view room, 1 queen bed",2,4500,25,"AC,TV,WiFi,Balcony"),
    ("H002","deluxe","Sea view room with private balcony, 1 king bed",2,7500,20,"AC,Smart TV,WiFi,Mini Bar,Private Balcony,Sea View"),
    ("H002","suite","Beachfront villa with private plunge pool",4,15000,8,"AC,Smart TV,WiFi,Mini Bar,Private Pool,Direct Beach Access,Butler Service"),
])

# SERVICES
cur.executemany("INSERT OR IGNORE INTO services VALUES (?,?,?,?,?)", [
    ("SVC001","H001","Airport Transfer",800,"One-way cab from airport to hotel"),
    ("SVC002","H001","Breakfast Buffet",600,"Per person per day"),
    ("SVC003","H001","Spa Session",2500,"60-minute full body massage"),
    ("SVC004","H001","Late Checkout",1500,"Extend checkout till 6 PM"),
    ("SVC005","H002","Airport Transfer",1200,"One-way cab from Vizag airport"),
    ("SVC006","H002","Breakfast + Dinner",1200,"Per person per day, MAP plan"),
    ("SVC007","H002","Water Sports Package",3000,"Jet ski, banana boat, snorkeling"),
    ("SVC008","H002","Romantic Dinner Setup",3500,"Private beach candlelight dinner"),
])

# CUSTOMERS
cur.executemany(
    "INSERT OR IGNORE INTO customers (customer_id,name,email,phone,loyalty_tier,loyalty_points,total_stays) VALUES (?,?,?,?,?,?,?)", [
    ("C001","Ravi Kumar","ravi.kumar@gmail.com","+91-9876543210","gold",4500,8),
    ("C002","Priya Sharma","priya.sharma@outlook.com","+91-9812345678","silver",1800,3),
    ("C003","Anil Reddy","anil.reddy@yahoo.com","+91-9988776655","bronze",500,1),
    ("C004","Meena Iyer","meena.iyer@gmail.com","+91-9001122334","silver",2200,5),
])

# BOOKINGS
cur.executemany("INSERT OR IGNORE INTO bookings VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", [
    ("BK1001","C001","H001","deluxe","2026-04-15","2026-04-18",3,2,5500,16500,2000,18500,18500,"confirmed","credit_card","paid",0,None,"High floor room preferred","2026-03-20 10:30:00","2026-03-20 10:30:00"),
    ("BK1002","C002","H002","suite","2026-04-20","2026-04-23",3,2,15000,45000,4700,49700,49700,"confirmed","upi","paid",0,None,"Anniversary celebration, need rose petals in room","2026-03-25 14:15:00","2026-03-25 14:15:00"),
    ("BK1003","C003","H001","standard","2026-04-10","2026-04-12",2,1,3500,7000,0,7000,7000,"checked_in","debit_card","paid",0,None,"","2026-04-01 09:00:00","2026-04-10 14:00:00"),
    ("BK1004","C004","H002","deluxe","2026-05-01","2026-05-05",4,2,7500,30000,7800,37800,18900,"confirmed","net_banking","partial",0,None,"Sea facing room, early check-in if possible","2026-04-05 16:45:00","2026-04-05 16:45:00"),
    ("BK1005","C001","H002","standard","2026-03-10","2026-03-12",2,2,4500,9000,2400,11400,11400,"completed","credit_card","paid",0,None,"","2026-02-28 11:00:00","2026-03-12 11:00:00"),
    ("BK1006","C002","H001","deluxe","2026-04-05","2026-04-07",2,2,5500,11000,0,11000,11000,"cancelled","upi","refunded",11000,"2026-04-02 10:00:00","","2026-03-15 08:30:00","2026-04-02 10:00:00"),
])

# BOOKING SERVICES
cur.executemany("INSERT OR IGNORE INTO booking_services (booking_id,service_id,quantity,cost) VALUES (?,?,?,?)", [
    ("BK1001","SVC001",1,800),
    ("BK1001","SVC002",2,1200),
    ("BK1002","SVC005",1,1200),
    ("BK1002","SVC008",1,3500),
    ("BK1004","SVC006",2,4800),
    ("BK1004","SVC007",1,3000),
    ("BK1005","SVC006",2,2400),
])

# COMPLAINTS
cur.executemany("INSERT OR IGNORE INTO complaints VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", [
    ("CMP001","BK1003","C003","H001","maintenance","AC in room not working properly","in_progress","high",None,None,"2026-04-10 15:00:00","2026-04-10 15:00:00",None),
])

# REFUNDS
cur.executemany("INSERT OR IGNORE INTO refunds VALUES (?,?,?,?,?,?,?,?)", [
    ("REF001","BK1006","C002",11000,"Free cancellation applied","completed","2026-04-02 10:00:00","2026-04-02 10:30:00"),
])

conn.commit()
conn.close()
print("Done! stayease.db created.")
