-- init.sql
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'BookingDB')
BEGIN
    CREATE DATABASE BookingDB;
END
GO

USE BookingDB;
GO

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = N'bookings')
BEGIN
    CREATE TABLE bookings (
        id INT PRIMARY KEY IDENTITY(1,1),
        customer_name NVARCHAR(100) NOT NULL,
        date NVARCHAR(10) NOT NULL
    );
END
GO