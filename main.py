import sqlite3
import pandas as pd

# Connect to the database
conn = sqlite3.connect('data.sqlite')

pd.read_sql("""SELECT * FROM sqlite_master""", conn)

# STEP 1
# Boston employees: first name, last name, job title
df_boston = pd.read_sql("""
    SELECT
        e.firstName,
        e.lastName,
        e.jobTitle
    FROM employees e
    JOIN offices o ON e.officeCode = o.officeCode
    WHERE o.city = 'Boston';
""", conn)

# STEP 2
# Offices with zero employees
df_zero_emp = pd.read_sql("""
    SELECT
        o.officeCode,
        o.city
    FROM offices o
    LEFT JOIN employees e ON o.officeCode = e.officeCode
    WHERE e.employeeNumber IS NULL;
""", conn)

# STEP 3
# All employees, with office city/state if they have one, ordered by first then last name
df_employee = pd.read_sql("""
    SELECT
        e.firstName,
        e.lastName,
        o.city,
        o.state
    FROM employees e
    LEFT JOIN offices o ON e.officeCode = o.officeCode
    ORDER BY e.firstName, e.lastName;
""", conn)

# STEP 4
# Customers with no orders: contact info + sales rep employee number
df_contacts = pd.read_sql("""
    SELECT
        c.contactFirstName,
        c.contactLastName,
        c.phone,
        c.salesRepEmployeeNumber
    FROM customers c
    LEFT JOIN orders o ON c.customerNumber = o.customerNumber
    WHERE o.orderNumber IS NULL
    ORDER BY c.contactLastName;
""", conn)

# STEP 5
# Customer contacts with payment amount and date, sorted by amount descending
# (cast amount to ensure numeric sort, in case it's stored as text)
df_payment = pd.read_sql("""
    SELECT
        c.contactFirstName,
        c.contactLastName,
        p.amount,
        p.paymentDate
    FROM customers c
    JOIN payments p ON c.customerNumber = p.customerNumber
    ORDER BY CAST(p.amount AS DECIMAL(10,2)) DESC;
""", conn)

# STEP 6
# Employees whose customers have an average credit limit over 90k
df_credit = pd.read_sql("""
    SELECT
        e.employeeNumber,
        e.firstName,
        e.lastName,
        COUNT(c.customerNumber) AS numcustomers
    FROM employees e
    JOIN customers c ON e.employeeNumber = c.salesRepEmployeeNumber
    GROUP BY e.employeeNumber, e.firstName, e.lastName
    HAVING AVG(c.creditLimit) > 90000
    ORDER BY numcustomers DESC;
""", conn)

# STEP 7
# Top-selling products: number of orders and total units sold
df_product_sold = pd.read_sql("""
    SELECT
        p.productName,
        COUNT(od.orderNumber) AS numorders,
        SUM(od.quantityOrdered) AS totalunits
    FROM products p
    JOIN orderdetails od ON p.productCode = od.productCode
    GROUP BY p.productCode, p.productName
    ORDER BY totalunits DESC;
""", conn)

# STEP 8
# Product reach: number of distinct customers who ordered each product
df_total_customers = pd.read_sql("""
    SELECT
        p.productName,
        p.productCode,
        COUNT(DISTINCT o.customerNumber) AS numpurchasers
    FROM products p
    JOIN orderdetails od ON p.productCode = od.productCode
    JOIN orders o ON od.orderNumber = o.orderNumber
    GROUP BY p.productCode, p.productName
    ORDER BY numpurchasers DESC;
""", conn)

# STEP 9
# Number of customers per office
df_customers = pd.read_sql("""
    SELECT
        o.officeCode,
        o.city,
        COUNT(c.customerNumber) AS n_customers
    FROM offices o
    LEFT JOIN employees e ON o.officeCode = e.officeCode
    LEFT JOIN customers c ON e.employeeNumber = c.salesRepEmployeeNumber
    GROUP BY o.officeCode, o.city
    ORDER BY n_customers DESC;
""", conn)

# STEP 10
# Employees who sold products ordered by fewer than 20 customers
df_under_20 = pd.read_sql("""
    WITH underperforming AS (
        SELECT od.productCode
        FROM orderdetails od
        JOIN orders o ON od.orderNumber = o.orderNumber
        GROUP BY od.productCode
        HAVING COUNT(DISTINCT o.customerNumber) < 20
    )
    SELECT DISTINCT
        e.employeeNumber,
        e.firstName,
        e.lastName,
        ofc.city,
        ofc.officeCode
    FROM employees e
    JOIN customers c ON e.employeeNumber = c.salesRepEmployeeNumber
    JOIN orders o ON c.customerNumber = o.customerNumber
    JOIN orderdetails od ON o.orderNumber = od.orderNumber
    JOIN offices ofc ON e.officeCode = ofc.officeCode
    WHERE od.productCode IN (SELECT productCode FROM underperforming);
""", conn)

conn.close()