-- admins table
CREATE TABLE admins (
    admin_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL
);

-- students table
CREATE TABLE students (
    roll_no VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    phone VARCHAR(15) NOT NULL,
    branch VARCHAR(50) NOT NULL,
    year INT NOT NULL CHECK (year BETWEEN 1 AND 4),
    gender ENUM('Male', 'Female') NOT NULL,
    password VARCHAR(100) NOT NULL,
    room_id VARCHAR(10) NOT NULL,
    FOREIGN KEY (room_id) REFERENCES rooms(room_id) ON DELETE CASCADE
);
-- rooms table
CREATE TABLE rooms (
    room_id VARCHAR(10) PRIMARY KEY,
    capacity INT NOT NULL DEFAULT 3,
    occupants INT NOT NULL DEFAULT 0,
    gender ENUM('Male', 'Female') NOT NULL
);
-- applications table
CREATE TABLE applications (
    application_id INT AUTO_INCREMENT PRIMARY KEY,
    roll_no VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    phone VARCHAR(15) NOT NULL,
    branch VARCHAR(50) NOT NULL,
    year INT NOT NULL CHECK (year BETWEEN 1 AND 4),
    gender ENUM('Male', 'Female') NOT NULL,
    password VARCHAR(100) NOT NULL,
    status ENUM('pending', 'accepted', 'cancelled', 'declined') NOT NULL DEFAULT 'pending'
);



-- Create new allotments table
CREATE TABLE allotments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_roll_no VARCHAR(20),
    room_id VARCHAR(10),
    status ENUM('pending', 'accepted', 'rejected','cancel') DEFAULT 'pending',
    allotted_on DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_roll_no) REFERENCES applications(roll_no) ON DELETE CASCADE,
    FOREIGN KEY (room_id) REFERENCES rooms(room_id) ON DELETE CASCADE
);
