import mysql.connector

db_name = "hnsdb111"
#connecting with database
try:
  mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="",
  database=db_name
  )
  mycursor = mydb.cursor()
except:
  mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="",
  )
  mycursor = mydb.cursor()
  mycursor.execute("CREATE DATABASE "+ db_name)
  mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="",
  database=db_name,
  )
  mycursor = mydb.cursor()
mycursor.execute("SHOW TABLES")
#printing database names
list_of_tables = []
for x in mycursor:
  list_of_tables.append(str(x))
  print(x)
if(len(list_of_tables) == 0):
  mycursor.execute("CREATE TABLE Domains(Name VARCHAR(255),Status VARCHAR(255))")





#stub to check if record exist or not
"""
sql = "SELECT * FROM Domains WHERE Name ='Johny sins'"

mycursor.execute(sql)

myresult = mycursor.fetchall()
print("myresult:  ",myresult)
for x in myresult:
  print(x)

"""


#stub to update certain value

mycursor = mydb.cursor()

sql = "UPDATE Domains SET Status = 'Canyon 123' WHERE Name = 'John'"

mycursor.execute(sql)

mydb.commit()

print(mycursor.rowcount, "record(s) affected")

y = input("this")






sql = "INSERT INTO Domains(Name, Status) VALUES (%s, %s)"
val = ("John", "Not for sale")
mycursor.execute(sql, val)
mydb.commit()
print(mycursor.rowcount, "record inserted.")


#creating cursor to execute queries
#  mycursor = mydb.cursor()

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

