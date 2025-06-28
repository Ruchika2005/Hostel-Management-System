-- STUDENTS TABLE
CREATE TABLE students (
    roll_no VARCHAR(20) PRIMARY KEY,     -- e.g., CS23A001
    name VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(15) UNIQUE,
    branch VARCHAR(50),
    year INT,
    gender ENUM('Male', 'Female')
);

-- ROOMS TABLE
CREATE TABLE rooms (
    room_id INT AUTO_INCREMENT PRIMARY KEY,
    room_number VARCHAR(10) UNIQUE,
    capacity INT DEFAULT 3,
    occupants INT DEFAULT 0,
    gender ENUM('Male', 'Female') -- Room gender restriction
);

-- APPLICATIONS TABLE
CREATE TABLE applications (
    application_id INT AUTO_INCREMENT PRIMARY KEY,
    roll_no VARCHAR(20),
    application_date DATE,
    status ENUM('Pending', 'Allocated', 'Waitlisted', 'Declined') DEFAULT 'Pending',
    priority_level INT,
    FOREIGN KEY (roll_no) REFERENCES students(roll_no)
);

-- ALLOCATIONS TABLE
CREATE TABLE allocations (
    allocation_id INT AUTO_INCREMENT PRIMARY KEY,
    roll_no VARCHAR(20),
    room_id INT,
    allocated_on DATE,
    accepted ENUM('Pending', 'Accepted', 'Declined') DEFAULT 'Pending',
    FOREIGN KEY (roll_no) REFERENCES students(roll_no),
    FOREIGN KEY (room_id) REFERENCES rooms(room_id)
);
