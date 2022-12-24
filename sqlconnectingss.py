import mysql.connector

#connecting with database
mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="",
  database="mydatabase"
)
#creating cursor to execute queries
mycursor = mydb.cursor()

#creating my first database

"""
mycursor.execute("CREATE DATABASE mydatabase")
"""

#checking the database we have on our sql server
"""
mycursor.execute("SHOW DATABASES")
#to check tables
mycursor.execute("SHOW TABLES")
#printing database names
for x in mycursor:
  print(x)
"""
#creating first table in our database
#mycursor.execute("CREATE TABLE customers (name VARCHAR(255), address VARCHAR(255))")

#creating primary key to previously built customer table
#mycursor.execute("ALTER TABLE customers ADD COLUMN id INT AUTO_INCREMENT PRIMARY KEY")

"""
#inserting data into table
sql = "INSERT INTO customers (name, address) VALUES (%s, %s)"
val = ("John", "Highway 21")
mycursor.execute(sql, val)
mydb.commit()
print(mycursor.rowcount, "record inserted.")
"""

"""
#entering multiple rows into table
sql = "INSERT INTO customers (name, address) VALUES (%s, %s)"
val = [
  ('Peter', 'Lowstreet 4'),
  ('Amy', 'Apple st 652'),
  ('Hannah', 'Mountain 21'),
  ('Michael', 'Valley 345'),
  ('Sandy', 'Ocean blvd 2'),
  ('Betty', 'Green Grass 1'),
  ('Richard', 'Sky st 331'),
  ('Susan', 'One way 98'),
  ('Vicky', 'Yellow Garden 2'),
  ('Ben', 'Park Lane 38'),
  ('William', 'Central st 954'),
  ('Chuck', 'Main Road 989'),
  ('Viola', 'Sideway 1633')
]
mycursor.executemany(sql, val)
mydb.commit()
print(mycursor.rowcount, "was inserted.")
"""

