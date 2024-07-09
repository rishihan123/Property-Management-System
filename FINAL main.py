from flask import Flask, redirect, render_template, request, url_for, session
from SPARQLWrapper import SPARQLWrapper, JSON
import smtplib
from email.mime.text import MIMEText
import mysql.connector
import random
import time
import requests
import hashlib
from datetime import datetime, timedelta


### CLASSES ###


class Array(object):
	#A simulated Array in Python because Python does not have arrays
	def __init__(self, size):
		self.__size = size
		self.__array = []
		for i in range(size):
			self.__array.append(None)

	def getSize(self):
		#Returns the size of the array
		return self.__size

	def get(self, n):
		#Returns the value in index n
		if n>= self.__size or n<0:
			raise AppException("Index "+str(n)+" out of bounds.")
		return self.__array[n]

	def assign(self, n, value):
		#Sets element n to value
		if n>= self.__size or n<0:
			raise AppException("Index "+str(n)+" out of bounds.")
		self.__array[n] = value

class Database(object): #class which contains all functions which utilise the database
    def __init__(self):
        self.customer_details = mysql.connector.connect(
        host="localhost",
        user="root",
        password="RoomierCanine24!",
        database = "customer_details"
        )
        self.__cd_cursor = self.customer_details.cursor()

    def insertUserDetails(self, username, password, forename, surname, address, number, mobile, email): #function to insert records into the user details database
        sql = "INSERT INTO details (user_id, password, forename, surname, address, number, mobile, email) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        val = (username, password, forename, surname, address, number, mobile, email)
        self.__cd_cursor.execute(sql,val)
        self.customer_details.commit()
        print(self.__cd_cursor.rowcount, "was inserted")
    
    def insertPurchasedProperty(self, username, propertyid, address, city, county, postcode, longitude, latitude, price, date): #function to insert records into the user details database
        propertylist = self.getPurchasedPropertyAddresses(username)
        for i in range(len(propertylist)):
            property = str(propertylist[i])
            property = property.replace(")", "")
            property = property.replace(",", "")
            property = property.replace("(", "")
            property = property.replace("'", "")
            propertylist[i] = property
        for i in propertylist:
            if address == i: #checks if the properties already existing in the database are the same as the property which is being added
                raise AppException("CANNOT ADD PROPERTY! PROPERTY ALREADY EXISTS IN THE PURCHASED PROPERTY LIST")
            else:
                pass
        sql = "INSERT INTO purchased (user_id, property_id, address, city, county, postcode, longitude, latitude, price, date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        val = (username, propertyid, address, city, county, postcode, longitude, latitude, price, date)
        self.__cd_cursor.execute(sql,val)
        self.customer_details.commit()
        print(self.__cd_cursor.rowcount, "was inserted")
    
    def insertWatchlistProperty(self, username, propertyid, address, city, county, postcode, longitude, latitude): #function to insert records into the user details database
        sql = "INSERT INTO watchlist (user_id, property_id, address, city, county, postcode, longitude, latitude) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        val = (username, propertyid, address, city, county, postcode, longitude, latitude)
        self.__cd_cursor.execute(sql,val)
        self.customer_details.commit()
        print(self.__cd_cursor.rowcount, "was inserted")
    
    def insertValuation(self, propertyid, valuation):
        sql = "INSERT INTO valuation (property_id, valuation) VALUES (%s, %s)"
        val = (propertyid, valuation)
        self.__cd_cursor.execute(sql,val)
        self.customer_details.commit()
        print(self.__cd_cursor.rowcount, "was inserted")
    
    def insertWatchlistPriceDetails(self, propertyid, price, date):
        sql = "INSERT INTO watchlistpricedetails (property_id, price, date) VALUES (%s, %s, %s)"
        val = (propertyid, price, date)
        self.__cd_cursor.execute(sql,val)
        self.customer_details.commit()
        print(self.__cd_cursor.rowcount, "was inserted")
    
    def insertWatchlistValuation(self, propertyid, valuation):
        sql = "INSERT INTO watchlistvaluation (property_id, valuation) VALUES (%s, %s)"
        val = (propertyid, valuation)
        self.__cd_cursor.execute(sql,val)
        self.customer_details.commit()
        print(self.__cd_cursor.rowcount, "was inserted")
    
    def updateUserDetails(self, username, password, forename, surname, address, number, mobile): #function to update a user record if they decide to update their profile
        sql = "UPDATE details SET password = %s, forename = %s, surname = %s, address = %s, number = %s, mobile = %s WHERE user_id = %s"
        val = (password,forename,surname,address,number,mobile,username)
        self.__cd_cursor.execute(sql,val)
        self.customer_details.commit()
        print("Records updated")

    def clearUserDetails(self): #function to clear the entire user details database
        sql = "DELETE FROM details"
        self.__cd_cursor.execute(sql)
        self.customer_details.commit()
        print("Records deleted")
    
    def clearAllPurchasedPropertiesDetails(self, username):
        sql = f"DELETE FROM purchased WHERE user_id = {username}"
        self.__cd_cursor.execute(sql)
        self.customer_details.commit()
        print("Records deleted")
    
    def clearSinglePurchasedPropertyDetails(self, username, propertyid):
        sql = f"DELETE FROM purchased WHERE user_id = {username} and property_id = {propertyid}"
        self.__cd_cursor.execute(sql)
        self.customer_details.commit()
        print("Records deleted")
    
    def clearAllWatchlistProperties(self, username):
        sql = f"DELETE FROM watchlist WHERE user_id = {username}"
        self.__cd_cursor.execute(sql)
        self.customer_details.commit()
        print("Records deleted")
    
    def clearSingleWatchlistProperty(self, username, propertyid):
        sql = f"DELETE FROM watchlist WHERE user_id = {username} and property_id = {propertyid}"
        self.__cd_cursor.execute(sql)
        self.customer_details.commit()
        print("Records deleted")
    
    def clearAllValuation(self, username):
        sql = f"DELETE valuation FROM valuation LEFT JOIN purchased ON valuation.property_id = purchased.property_id WHERE purchased.user_id = {username}"
        self.__cd_cursor.execute(sql)
        self.customer_details.commit()
        print("Records deleted")

    def clearSingleValuation(self, username, propertyid):
        sql = f"DELETE valuation FROM valuation LEFT JOIN purchased ON valuation.property_id = purchased.property_id WHERE purchased.property_id = {propertyid} and purchased.user_id = {username}"
        self.__cd_cursor.execute(sql)
        self.customer_details.commit()
        print("Records deleted")

    def getUsernames(self):
        sql = "SELECT user_id from details"
        try:
            self.__cd_cursor.execute(sql) #tries to execute the sql
        except Exception:
            raise AppException("Username doesn't exist. Please try again") #raises error if wrong details entered
        else:
            result = self.__cd_cursor.fetchall()
            print(result)
            return result
    
    def getPropertyIds(self, username): #function to get property ids of a given user
        sql = f"SELECT property_id from purchased WHERE user_id = {username}"
        try:
            self.__cd_cursor.execute(sql) #tries to execute the sql
        except Exception:
            raise AppException("Property Id doesn't exist. Please try again") #raises error if wrong details entered
        else:
            result = self.__cd_cursor.fetchall()
            print(result)
            return result
    
    def getWatchlistIds(self, username):
        sql = f"SELECT property_id from watchlist WHERE user_id = {username}"
        try:
            self.__cd_cursor.execute(sql) #tries to execute the sql
        except Exception:
            raise AppException("Property Id doesn't exist. Please try again") #raises error if wrong details entered
        else:
            result = self.__cd_cursor.fetchall()
            print(result)
            return result
    
    def getPurchasedPropertyAddresses(self, username):
        sql = f"SELECT address from purchased WHERE user_id = {username}"
        try:
            self.__cd_cursor.execute(sql) #tries to execute the sql
        except Exception:
            raise AppException("Property doesn't exist. Please try again") #raises error if wrong details entered
        else:
            result = self.__cd_cursor.fetchall()
            print(result)
            return result
    
    def getWatchlistAddresses(self, username):
        sql = f"SELECT address from watchlist WHERE user_id = {username}"
        try:
            self.__cd_cursor.execute(sql) #tries to execute the sql
        except Exception:
            raise AppException("Property doesn't exist. Please try again") #raises error if wrong details entered
        else:
            result = self.__cd_cursor.fetchall()
            print(result)
            return result
    
    def getPurchasedPropertyDetails(self, username, propertyid):
        sql = f"SELECT * from purchased WHERE user_id = {username} and property_id = {propertyid}"
        self.__cd_cursor.execute(sql)  #raises error if wrong details entered
        result = self.__cd_cursor.fetchall()
        print(result)
        return result
    
    def getWatchlistPropertyDetails(self, username, propertyid):
        sql = f"SELECT * from watchlist WHERE user_id = {username} and property_id = {propertyid}"
        self.__cd_cursor.execute(sql)  #raises error if wrong details entered
        result = self.__cd_cursor.fetchall()
        print(result)
        return result

    def getPropertyValuation(self, username, propertyid):
        sql = f"SELECT valuation FROM purchased RIGHT JOIN valuation ON valuation.property_id = purchased.property_id WHERE purchased.property_id = {propertyid} and purchased.user_id = {username} "
        self.__cd_cursor.execute(sql)  #raises error if wrong details entered
        result = self.__cd_cursor.fetchall()
        result = result[0]
        result = formatTuple(result)
        return result 
    
    def getAllPropertyValuation(self, username):
        sql = f"SELECT valuation FROM purchased RIGHT JOIN valuation ON valuation.property_id = purchased.property_id WHERE purchased.user_id = {username} "
        self.__cd_cursor.execute(sql)  #raises error if wrong details entered
        result = self.__cd_cursor.fetchall()
        return result 
    
    def getAllPropertyPrice(self, username):
        sql = f"SELECT price FROM purchased WHERE user_id = {username} "
        self.__cd_cursor.execute(sql)  #raises error if wrong details entered
        result = self.__cd_cursor.fetchall()
        return result 

    def getEmails(self):
        sql = "SELECT email from details"
        self.__cd_cursor.execute(sql)
        result = self.__cd_cursor.fetchall()
        return result
    
    def uniqueEmail(self,email):
        for i in AppDatabase.getEmails(): #makes sure that the email entered is unique
            i = formatTuple(i)
            i = i.replace("'", "")
            if email == i:
                return False #if repeated email detected the function returns False
            else:
                pass 
        return True #if uniqueemail is still true after checking all items in the database, the function returns True
    
    def uniqueID(self, id):
        for i in AppDatabase.getUsernames(): #makes sure that the username created is unique
            i = formatTuple(i)
            i = int(i)
            if id == i:
                return False #if repeated id detected the function returns False
            else:
                pass
        return True #if uniqueid is still true after checking all items in the database, the function returns True

    def getPurchasedIds(self): #function to get purchased ids of the entire table (not unique to a given username)
        sql = "SELECT property_id from purchased"
        self.__cd_cursor.execute(sql) #tries to execute the sql
        result = self.__cd_cursor.fetchall()
        return result
    
    def getAllWatchlistIds(self): #function to get watchlist ids of the entire table (not unique to a given username)
        sql = "SELECT property_id from watchlist"
        self.__cd_cursor.execute(sql) #tries to execute the sql
        result = self.__cd_cursor.fetchall()
        return result
    
    def uniquePurchasedPropertyId(self, id):
        for i in AppDatabase.getPurchasedIds(): #makes sure that the property id created is unique
            i = formatTuple(i)
            i = int(i)
            if id == i:
                return False #if repeated id detected the function returns False
            else:
                pass
        return True #if uniqueid is still true after checking all items in the database, the function returns True
    
    def uniqueWatchlistPropertyId(self, id):
        for i in AppDatabase.getAllWatchlistIds(): #makes sure that the property id created is unique
            i = formatTuple(i)
            i = int(i)
            if id == i:
                return False #if repeated id detected the function returns False
            else:
                pass
        return True #if uniqueid is still true after checking all items in the database, the function returns True


    def getForename(self, username): #function to select the forename of the logged in account
        sql = f"SELECT forename FROM details WHERE user_id = {username}"
        self.__cd_cursor.execute(sql)
        result = self.__cd_cursor.fetchall()
        result = str(result[0]).replace("(", "")
        result = result.replace(")", "") #selecting from mysql adds unnecessary punctuation so the replace function gets rid of them
        result = result.replace("'", "")
        result = result.replace(",", "")
        return result
    
    def getSurname(self, username): #function to select the surname of the logged in account
        sql = f"SELECT surname FROM details WHERE user_id = {username}"
        self.__cd_cursor.execute(sql)
        result = self.__cd_cursor.fetchall()
        result = str(result[0]).replace("(", "")
        result = result.replace(")", "")
        result = result.replace("'", "")
        result = result.replace(",", "")
        return result
    
    def getDetails(self, username): #function to select all the details of a user for the profile page of the website
        sql = f"SELECT * FROM details WHERE user_id = {username}"
        self.__cd_cursor.execute(sql)
        result = self.__cd_cursor.fetchall()
        details = [] #makes a list containing all the user details of the currently logged in user so they can be displayed on the profile page
        for i in result:
            details.append(i[1])
            details.append(i[2])
            details.append(i[3])
            details.append(i[4])
            details.append(i[5])
            details.append(i[6])
            details.append(i[7])
        return details

      
    def Login(self, username, password): #function to select the login details of an account
        sql = f"SELECT password FROM details WHERE user_id = {username} "
        try:
            self.__cd_cursor.execute(sql) #tries to execute the sql
        except Exception:
            raise AppException("Incorrect details. Please try again") #raises error if wrong details entered
        else:
            result = self.__cd_cursor.fetchall()
            if len(result) == 0:
                raise AppException("Incorrect details. Please try again")
            else:
                result = str(result[0]).replace("(", "")
                result = result.replace(")", "")
                result = result.replace("'", "")
                result = result.replace(",", "")
                if password == result:
                    return True
                else:
                    return False

class AppException(Exception): #object for exception handling
    def __init__(self, value):
        self.__value = value
    def toString(self):
        return self.__value

class Stack(object):
    def __init__(self, size):
        self.__TOS = 0
        self.__Stack = Array(size) #Makes an array for the stack to be made on top of
    
    def getTOS(self):
        return self.__TOS
    
    #returns true boolean value if the stack is full
    def full(self):
        return self.__TOS == self.__Stack.getSize()
    
    #returns true boolean if the stack is empty
    def empty(self):
        return self.__TOS == 0
    
    #will push a value to the position of the TOS in the stack
    def push(self, value):
        if not self.full():
            self.__Stack.assign(self.__TOS, value)
            self.__TOS += 1
        else:
            raise AppException("Stack Overflow")
    
    #will pop the value on the TOS in the stack and return the popped value
    def pop(self):
        if not(self.empty()):
            self.__TOS -= 1
            return self.__Stack.get(self.__TOS)
        else:
            raise AppException("Stack Empty")
    
    #will display the stack from the highest value at the top to lowest at the bottom
    def displayStack(self):
        if not(self.empty()):
            for i in reversed(range(self.__TOS + 1)):
                if i == self.__TOS:
                    print(" <-- ")
                else:
                    print("{}".format(self.__Stack.get(i)))


### FUNCTIONS ###


def reverseList(alist): #function which returns the reversed list of a list since the in built reversed function returns an iterator rather than a list
    templist = reversed(alist)
    newlist = []
    for i in templist:
        newlist.append(i)
    return newlist

def hashPassword(password): #function to hash the user's password to enter into the database when creating account
    temp = int(hashlib.sha1(password.encode("utf-8")).hexdigest(), 16) % (10 ** 8)
    hashedvalue = str(temp)
    return hashedvalue

def send_email(subject, message, destination): #function to send email
    # This block of code assembles the message
    print(f" HERE {message}")
    msg = MIMEText(message, 'plain')
    msg['Subject'] = subject

    # This block of code logs into the app email and sends the message
    port = 587
    my_mail = 'PropertyManagementSystem123@outlook.com'
    my_password = 'RoomierCanine24!'
    with smtplib.SMTP('smtp.office365.com', port) as server:
        server.starttls()
        server.login(my_mail, my_password)
        server.sendmail(my_mail, destination, msg.as_string())

def getPaonFromAddress(address): #function to pull just the number from an address so it can be used in the SPARQL query
    num = [int(s) for s in address.split() if s.isdigit()]
    if len(num) == 0:
        paon = address.upper()
    else:
        try:
            paon = str(num[0])
        except Exception:
            raise AppException("Invalid Property")
    print(paon)
    return paon

def mergeSort(myList): #function to sort a list of properies to be displayed in the watchlist and purchased property list
    if len(myList) > 1:
        mid = len(myList) // 2
        left = myList[:mid] #Takes all the items from the left of the middle item
        right = myList[mid:] #Takes all the items from the right of the middle item

        # Recursive call on each half
        mergeSort(left)
        mergeSort(right)

        # Two iterators for traversing the two halves
        i = 0
        j = 0
        
        # Iterator for the main list
        k = 0
        
        while i < len(left) and j < len(right):
            if left[i] <= right[j]:
              # The value from the left half has been used
              myList[k] = left[i]
              # Move the iterator forward
              i += 1
            else:
                myList[k] = right[j]
                j += 1
            # Move to the next slot
            k += 1

        # For all the remaining values
        while i < len(left):
            myList[k] = left[i]
            i += 1
            k += 1

        while j < len(right):
            myList[k]=right[j]
            j += 1
            k += 1
    return myList

def findPurchasedPropertyData(postcode, address): #function which finds the price and date of a purhcased property 
    sparql = SPARQLWrapper("http://landregistry.data.gov.uk/landregistry/query")
    sparql.setQuery("""
        prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    prefix owl: <http://www.w3.org/2002/07/owl#>
    prefix xsd: <http://www.w3.org/2001/XMLSchema#>
    prefix sr: <http://data.ordnancesurvey.co.uk/ontology/spatialrelations/>
    prefix ukhpi: <http://landregistry.data.gov.uk/def/ukhpi/>
    prefix lrppi: <http://landregistry.data.gov.uk/def/ppi/>
    prefix skos: <http://www.w3.org/2004/02/skos/core#>
    prefix lrcommon: <http://landregistry.data.gov.uk/def/common/>

    SELECT ?paon ?saon ?street ?town ?county ?postcode ?amount ?date ?category
    WHERE
    {
    VALUES ?postcode {'"""+postcode+"""'^^xsd:string}

    ?addr lrcommon:postcode ?postcode.

    ?transx lrppi:propertyAddress ?addr ;
            lrppi:pricePaid ?amount ;
            lrppi:transactionDate ?date ;
            lrppi:transactionCategory/skos:prefLabel ?category.

    OPTIONAL {?addr lrcommon:county ?county}
    OPTIONAL {?addr lrcommon:paon ?paon}
    OPTIONAL {?addr lrcommon:saon ?saon}
    OPTIONAL {?addr lrcommon:street ?street}
    OPTIONAL {?addr lrcommon:town ?town}
    }
    ORDER BY ?amount""")
    sparql.setReturnFormat(JSON) #converts the result of the query into json
    results = sparql.query().convert()
    data = results["results"] 

    results = []
    houselisttemp = []
    datelisttemp = []
    pricelisttemp = []
    for element in data["bindings"]:
        houselisttemp.append((element["paon"]["value"])) #appends all the paon values to the houselist
        datelisttemp.append((element["date"]["value"])) #appends all the date values to the datelist
        pricelisttemp.append((element["amount"]["value"])) #appends all the price values to the pricelist
    houselist = reverseList(houselisttemp)
    datelist = reverseList(datelisttemp) #reverses all the lists as they are in chronological order and the function wants the most recently purchased property
    pricelist = reverseList(pricelisttemp)
    num = 0
    for i in houselist: #finds the correct house from the list
      if i == address:
        results.append(pricelist[num])
        results.append(datelist[num])
        num += 1
      else:
        num +=1
    if len(results) == 0:
        raise AppException("Property not found in data. Please search for a property purchased after 1995")
    else:
        return results

def estimateValuation(date1, date2): #function which finds the 2 valuation values in a given date range. Only a general UK estimate as exact valuation takes a lot more factors into account 
    sparql = SPARQLWrapper("http://landregistry.data.gov.uk/landregistry/query") #determine SPARQL endpoint
    # House price index for UK  within a given date range
    DateRange1 = date2 #This is as far as the data goes up to
    DateRange2 = date1
    sparql.setQuery('''
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    PREFIX ukhpi: <http://landregistry.data.gov.uk/def/ukhpi/>
    


    SELECT  ?hpi
    {
    ?region ukhpi:refPeriodStart ?date ;
            ukhpi:housePriceIndex ?hpi
    FILTER (
        ?date < "'''+DateRange1+'''"^^xsd:date &&
        ?date > "'''+DateRange2+'''"^^xsd:date &&
        regex(str(?region), "uk")

    
    )
    }
    ''')

    sparql.setReturnFormat(JSON)   # Return format is JSON
    results = sparql.query().convert()   # execute SPARQL query and write result to "results"
    data = results["results"]
    alist = data["bindings"]
    answer = alist[0]["hpi"]["value"]
    print(answer)
    return answer

def mapLists(alist, listtobemapped): #function to map 2 lists together in order for the view property lists to function properly 
    counter = 0
    dictionary = {}
    for i in alist:
        dictionary[i] = [] #makes a dictionary with the keys being the names of the list to be sorted
        dictionary[i].append(listtobemapped[counter]) #appends the property ids to the respeced property names of the dictionary
        counter += 1
    listtobemapped.clear() #clears the property ids list
    alist = mergeSort(alist) #merge Sorts the list of properies
    for i in alist: 
        listtobemapped.append(dictionary[i][0]) #looks through the sorted list and appends the property ids in the sorted order
    return listtobemapped 

def formatTuple(item): #function to convert a tuple item into a string
    item = str(item)
    item = item.replace(")", "")
    item = item.replace(",", "")
    item = item.replace("(", "")
    return item

def validPropertyWatchlistDate(date): #function which takes an input date and compares it to 2014 which is needed to determine whether the property is valid to add to the watchlist or not
    originaldate = "2014-01-01"
    newdate = date
    originaldate = datetime.strptime(originaldate, "%Y-%m-%d")
    newdate = datetime.strptime(newdate, "%Y-%m-%d")
    return newdate > originaldate

def calculateValuation(percentage1, percentage2, price): #function which takes 2 percentage values and calculates the estimated valuation of a property
    calculationpercentage = percentage2 - percentage1
    calculationpercentage = calculationpercentage / 100
    calculationpercentage += 1
    valuation = int(price) * calculationpercentage
    valuation = round(valuation) 
    return valuation

def addDaysToDate(date): #function to add a couple days to a date so it can be used in the estimate valuation function
    date = datetime.strptime(date, "%Y-%m-%d")
    date2 = date + timedelta(days=35)
    date2 = date2.strftime("%Y-%m-%d")
    date = date.strftime("%Y-%m-%d")
    alist = []
    alist.append(date)
    alist.append(date2)
    return alist

def findGasDate(purchaseddate): #function to take the purchased date of a property and compare it to the current date to return a date when the CP12 gas check due date of that property is 
    purchaseddate = datetime.strptime(purchaseddate, "%Y-%m-%d")
    currentdate = datetime.now()
    currentdays = int((currentdate.strftime("%j")))
    purchaseddays = int((purchaseddate.strftime("%j")))
    currentyear = int((currentdate.strftime("%Y")))
    purchasedday = purchaseddate.strftime("%d")
    purchasedmonth = purchaseddate.strftime("%m")
    gasdate = None
    if currentdays <= purchaseddays:
        currentyear = str(currentyear)
        gasdate = f"{currentyear}-{purchasedmonth}-{purchasedday}"
    else:
        currentyear += 1
        currentyear = str(currentyear)
        gasdate = f"{currentyear}-{purchasedmonth}-{purchasedday}"
    return gasdate

### APP ###


AppDatabase = Database()
loggedin = None
username = None

#region Flask
webpage = Flask(__name__)
webpage.secret_key = "pms"

#routes the user to the homepage of the website
@webpage.route('/')
@webpage.route("/home", methods=["GET"])
def home():
    if "customer_name" in session:
        name = session["customer_name"]
        login = session["login"]
        username = session["id"]
        try:
            check = request.args.get("check") #This gets the parameter of the home link after the question mark. Gets the variable called check
            check = str(check)
            if check == "allPurchasedProperties":
                AppDatabase.clearAllValuation(username)
                AppDatabase.clearAllPurchasedPropertiesDetails(username)
                message = "Purchased Property List has been cleared"
            if check == "allWatchlistProperties":
                AppDatabase.clearAllWatchlistProperties(username)
                message = "Property WatchList has been cleared"
            if check[0] == "P": #Checks if the link needs the id from the Purchased Property list or another list
                pid = int(check[-4:]) #Takes the last 4 digits of the homelink which is the id of the property
                AppDatabase.clearSingleValuation(username, pid)
                AppDatabase.clearSinglePurchasedPropertyDetails(username, pid)
                message = "Property Deleted"
            if check[0] == "W": 
                pid = int(check[-4:]) 
                AppDatabase.clearSingleWatchlistProperty(username, pid)
                message = "Watchlist Property Deleted"
            return render_template("homepage.html", name=name, login=login, message=message)

        except Exception:
            return render_template("homepage.html", name=name, login=login) #If user is logged in and no request is made this page is returned

    else:
        if "error" in session:
            session.pop("error", None)
        return render_template("homepage.html", login=loggedin) #If user isn't logged in this page is returned

#routes the user to the login page of the website
@webpage.route("/login", methods=["POST", "GET"])
def login():
    if "customer_name" in session: #checks if the user is already logged into the current session
        name = session["customer_name"]
        login = session["login"]
        return render_template("login.html", name=name, login=login) 

    if request.method == "POST": #login process
        username = request.form["id"]
        password = request.form["password"]
        password = hashPassword(password) #hashes the entered password
        try: 
            match = AppDatabase.Login(username, password) #checks to see if the hashed password matches the hashed password in the database
        except AppException as e:
            session["error"] = e.toString() #error created in the session if incorrect details are entered
        else:
            if match == True:
                session.pop("error", None)
                session["customer_name"] = str(f"{AppDatabase.getForename(username)} {AppDatabase.getSurname(username)}")
                session["login"] = True
                session["id"] = username
                session["email"] = AppDatabase.getDetails(username)[6]
                return redirect(url_for("home")) #if successful session is created and user is routed to homepage
            else:
                session["error"] = "Incorrect details. Please try again"
                return redirect(url_for("login"))

    if "error" in session:
        error = session["error"]    
        return render_template("login.html", error=error, login=loggedin) #error passed over to the html to be displayed

    else:
        return render_template("login.html", login=loggedin) #when there is no session user is routed to the initial login page


#logs out of the current session
@webpage.route("/logout", methods=["POST", "GET"])
def logout():
    session.pop("customer_name", None)  #clears the customer name session variable as it is the one used in all the other functions
    session.clear()
    return redirect(url_for("login"))

#routes the user to the create account page of the website
@webpage.route("/create", methods=["POST", "GET"])
def create():
    session.pop("Email error", None)
    if request.method == "POST":
        email = request.form["email"]
        check = AppDatabase.uniqueEmail(email)
        session["Email error"] = "That email already exists in our database. Please login or use a different email"
        if check == True:
            session.pop("Email error", None)
            session["email"] = email
            code = str(random.randint(100000,999999)) #random 6 digit code generated for email verification
            session["start"] = time.time() #sets a starting time for the generation of the code. Used for the code's expiration 
            session["code"] = code
            message = "Code is " + str(code)
            send_email("PMS verification code",message , email)
            return render_template("verify.html")
    
    if "Email error" in session:
        error = session["Email error"]
        return render_template("create.html", error=error)

    else:
        return render_template("create.html")

#routes the user to the verify email page of the website
@webpage.route("/verify", methods=["POST","GET"])
def verify():
    code = session["code"]
    started_at = session["start"]
    if request.method == "POST":
        verification = request.form["inputcode"]
        time_passed = time.time() - started_at #makes the verification code sent to the email only valid for 5 minutes
        if time_passed > 300:
            code = None
            error = "Verification code has timed out. Please try again"
            return render_template("homepage.html", error=error, login=loggedin)
        if verification == code: #code for the email verification. Records are not inserted into the database unless the email is verified
            return render_template("register.html")
        else:
            session["code error"] = "Incorrect verification code. Email could not be verified. Please try again"
            return redirect(url_for("verifyerror"))

    if "code error" in session:
        return redirect(url_for("verifyerror"))

#routes the user to an error message when verifying email. This is used instead of redirecting back to verify as it means the code and timestamps are kept the same
@webpage.route("/verifyerror")
def verifyerror():
    error = session["code error"]
    return render_template("verify.html", error=error)

#final registration function that routes the user to the form which finishes making the account
@webpage.route("/register", methods=["POST", "GET"])
def register():
    email = session["email"]
    found = False
    while not found:
        id = random.randint(1000,9999) #id created per user for the primary key of the database
        check = AppDatabase.uniqueID(id)
        if check == True:
            found = True
        else:
            pass 
    if request.method == "POST":
        forename = request.form["forename"]
        surname = request.form["surname"]
        address = request.form["address"]
        number = request.form["number"]
        mobile = request.form["mobile"]
        password1 = request.form["password1"]
        password2 = request.form["password2"]
        if password1 == password2:
            welcomemessage = f"Welcome to PMS {forename} {surname}. Your account has now been officially created and has been registered into our system. Your unique PMS username is {id}"
            send_email("PMS Welcome", welcomemessage, email)
            password = hashPassword(password1)
            AppDatabase.insertUserDetails(id, password, forename, surname, address, number, mobile, email)
            error = "Your account has been created and your unique username has been emailed to you . Please sign in"
            session.pop("password error", None)
            return render_template("login.html", error=error, login=loggedin)
        else:
            session["password error"] = "Passwords don't match. Please try again"
            return redirect(url_for("passworderror"))
    
    if "password error" in session:
        return redirect(url_for("passworderror"))

@webpage.route("/passworderror")
def passworderror():
    error = session["password error"]
    return render_template("register.html", error=error)



#routes the user to the profile page of the website
@webpage.route("/profile", methods=["POST", "GET"])
def profile():
    if "customer_name" in session:
        name = session["customer_name"]
        login = session["login"]
        username = session["id"]
        details = AppDatabase.getDetails(username)
        password = details[0]
        forename = details[1]
        surname = details[2]
        address = details[3]
        number = details[4]
        mobile = details[5]
        email = details[6]
        hiddenpassword = ""
        for i in password:
            hiddenpassword += "*"
        if request.method == "POST":
            update = True
            verification = request.form["verify"]
            if password == hashPassword(verification):
                return render_template("register.html", update=update)
            else:
                error = "Incorrect password. Please try again"
                return render_template("profile.html", error=error, name=name, hiddenpassword=hiddenpassword, forename=forename, surname=surname, address=address, number=number, mobile=mobile, email=email, login=login)
        else:
                return render_template("profile.html", name=name, hiddenpassword=hiddenpassword, forename=forename, surname=surname, address=address, number=number, mobile=mobile, email=email, login=login)

    else:
        return render_template("profile.html", login=loggedin)

#routes the user to the updated profile details page of the website
@webpage.route("/updated", methods=["POST","GET"])
def updated():
    if request.method == "POST":
        email = session["email"]
        login = session["login"]
        username = session["id"]
        forename = request.form["forename"]
        surname = request.form["surname"]
        address = request.form["address"]
        number = request.form["number"]
        mobile = request.form["mobile"]
        password1 = request.form["password1"]
        password2 = request.form["password2"]
        if password1 == password2:
            password1 = hashPassword(password1)
            updatemessage = f"{forename} {surname}, Your PMS details have been officially changed."
            send_email("PMS Details Updated", updatemessage, email)
            AppDatabase.updateUserDetails(username, password1, forename, surname, address, number, mobile)
            name = f"{forename} {surname}"
            hiddenpassword = ""
            for i in password1:
                hiddenpassword += "*"
            error = "Details have been changed"
            session["customer_name"] = name
            return render_template("profile.html", error=error, name=name, hiddenpassword=hiddenpassword, forename=forename, surname=surname, address=address, number=number, mobile=mobile, email=email, login=login)

        else:
            return render_template("register.html", update=True, error="Passwords don't match")

#routes the user to the property finder page of the website
@webpage.route("/map", methods=["POST", "GET"])
def map():
    if "tempaddress" in session:
        session.pop("tempaddress", None)
        session.pop("tempcity", None)
        session.pop("tempcounty", None)
        session.pop("temppostcode", None)
        session.pop("longitude", None)
        session.pop("latitude", None)
        session.pop("price", None)
        session.pop("date", None)
        session.pop("error", None)
        session.pop("error2", None)
        return render_template("map.html")
    else:
        if "id" in session:
            return render_template("map.html")
        else:
            error = "Please login to use this feature"
            return render_template("map.html", error=error)

#routes the user to the property decision page of the website
@webpage.route("/decision", methods=["POST", "GET"])
def decision():
    if request.method == "POST":
            if "tempaddress" in session and "longitude" not in session: #checks if the temporary address entered in the Property finder is in the session. If not it will go to else (Page 2 of decision)
                address = session["tempaddress"]
                city = session["tempcity"]
                county = session["tempcounty"]
                postcode = session["temppostcode"]
                longitude = request.form["longitude"]
                latitude = request.form["latitude"]
                session["longitude"] = longitude #adds the longitude and latitude to the session so they can be used in the purchase list maker
                session["latitude"] = latitude
                return render_template("decision.html",longitude=longitude, latitude=latitude, city=city, county=county, postcode=postcode, address=address)
                
            elif "tempaddress" in session and "longitude" in session: #If all the info is ready it will go to the confirmation page (Page 3 of decision)
                address = session["tempaddress"]
                city = session["tempcity"]
                county = session["tempcounty"]
                postcode = session["temppostcode"]
                longitude = session["longitude"]
                latitude = session["latitude"]
                return render_template("purchaselistmaker.html",longitude=longitude, latitude=latitude, city=city, county=county, postcode=postcode, address=address)

            else: #If temporary address is not in session, this block of code is run and the user fills in an address form which will then enter the temporary address (Page 1 of decision)
                address = request.form["address"]
                try:
                    getPaonFromAddress(address)
                except AppException as e:
                    error = e.toString()
                    return render_template("map.html", error = error)
                city = request.form["city"]
                county = request.form["county"]
                postcode = request.form["postcode"]
                session["tempaddress"] = address
                session["tempcity"] = city
                session["tempcounty"] = county
                session["temppostcode"] = postcode
                addresslist = address.split() #turns the user input address into a list without spaces
                citylist = city.split() #does the same for the rest of the inputs
                countylist = county.split()
                postcodelist = postcode.split()
                formatted_address = ""
                for i in addresslist:
                    formatted_address = formatted_address + str(i) + "%20" #formats the address into the type of link that the mapbox api accepts so it can be used as a link
                for i in citylist:
                    formatted_address = formatted_address + str(i) + "%20" #does the same for the rest of the inputs
                for i in countylist:
                    formatted_address = formatted_address + str(i) + "%20"
                for i in postcodelist:
                    formatted_address = formatted_address + str(i) + "%20"
                #mapbox api is then called with the formatted address to retrieve property data
                query = requests.get(f"https://api.mapbox.com/geocoding/v5/mapbox.places/{formatted_address}.json?access_token=pk.eyJ1Ijoicm9vbWllcmNhbmluZTI0IiwiYSI6ImNsNjB6b3BhaTFzYmszam5xNWtzZTBxbDEifQ.BcL7-Ok06Xlo6uc3w6Jsjw")

                data = query.json()["features"] #data is defined as the features dictionary of the json response as it contains the coordinates
                center = [] 
                for i in data:
                    coordinates = i["center"] #defines coordinates as the center list of the features dictionary for every result of the query
                    center.append(coordinates) #appends the coordinates to the center list
                result = center[0] #the result is the first list from the query since the user has already checked for the correct address so it will work with the mapbox api
                longitude = result[0]
                latitude = result[1] #latitude and longitude are defined to be passed to the html page so the desired property can be displayed on a map
                return render_template("decision.html",longitude=longitude, latitude=latitude)

@webpage.route("/watchlistmaker", methods=["POST", "GET"])
def watchlistmaker():
    address = session["tempaddress"]
    city = session["tempcity"]
    county = session["tempcounty"]
    postcode = session["temppostcode"]
    longitude = session["longitude"]
    latitude = session["latitude"]
    return render_template("watchlistmaker.html", address=address, city=city, county=county, postcode=postcode, longitude=longitude, latitude=latitude)

@webpage.route("/purchaselistmaker", methods=["POST", "GET"])
def purchaselistmaker():
    if request.method == "POST":
        if "tempaddress" in session and "price" not in session: #checks if the price has been entered. If not, price is pulled from SPARQL database
            address = session["tempaddress"]
            city = session["tempcity"]
            county = session["tempcounty"]
            postcode = session["temppostcode"]
            longitude = session["longitude"]
            latitude = session["latitude"]
            try:
                paon = getPaonFromAddress(address)
                data = findPurchasedPropertyData(postcode, paon)
            except AppException as e: #If the property is not found in the database an error is raised
                error = e.toString()
                session["error"] = error
            if "error" in session:
                return render_template("purchaselistmaker.html", error=error)
        
            else:
                price = data[0]
                date = data[1]
                session["price"] = price
                session["date"] = date
                price = "{:,}".format(int(price))
                return render_template("purchaselistmaker.html", address=address, city=city, county=county, postcode=postcode, longitude=longitude, latitude=latitude, price=price, date=date)

        elif "tempaddress" in session and "price" in session: #if price is in the session, the user is asked to confirm if everything is right and then taken to a confirmation screen
            address = session["tempaddress"]
            city = session["tempcity"]
            county = session["tempcounty"]
            postcode = session["temppostcode"]
            longitude = session["longitude"]
            latitude = session["latitude"]
            price = session["price"]
            price = "{:,}".format(price)
            date = session["date"]
            return render_template("purchaselistmaker.html", address=address, city=city, county=county, postcode=postcode, longitude=longitude, latitude=latitude, price=price, date=date)

@webpage.route("/purchaseconfirm", methods=["POST", "GET"])
def purchaseconfirm():
    username = session["id"]
    address = session["tempaddress"]
    city = session["tempcity"]
    county = session["tempcounty"]
    postcode = session["temppostcode"]
    longitude = session["longitude"]
    latitude = session["latitude"]
    price = session["price"]
    date = session["date"]
    found = False
    while not found: #while loop to make sure the property id is unique
        propertyid = random.randint(1000,9999) #id created per property for the composite primary key of the 'purchased' database table
        check = AppDatabase.uniquePurchasedPropertyId(propertyid)
        if check == True:
            found = True
        else:
            pass
    
    #Stack made to check if there are too many properties already existing in the database 
    purchasedpropertystack = Stack(5)
    properties = AppDatabase.getPropertyIds(username)
    for i in properties:
        i = formatTuple(i)
        item = int(i)
        purchasedpropertystack.push(item) #Stack pushes the existing properties
    try:
        purchasedpropertystack.push(propertyid) #New property tried to be pushed to stack
    except Exception as e:
        session["error"] = e.toString() #If stack overflow occurs, error is added to session

    if "error" in session:
        error = session["error"]
        session.pop("error", None) #Purchased property in session details are popped
        session.pop("tempaddress", None)
        session.pop("tempcity", None)
        session.pop("tempcounty", None)
        session.pop("temppostcode", None)
        session.pop("longitude", None)
        session.pop("latitude", None)
        session.pop("price", None)
        session.pop("date", None)
        purchasedpropertystack = None
        return render_template("purchaseconfirm.html", error=error)
    
    else: #if no error the property is added to the database

        #Once propertyid is confirmed to be unique insert the details into the property  purchased database table
        try:
            AppDatabase.insertPurchasedProperty(username, propertyid, address, city, county, postcode, longitude, latitude, price, date) #creates a list to be inserted into the database
        except AppException as e:
            error2 = e.toString()
            session["error2"] = error2
        #Then pop all these details from the session as they are not needed anymore and more properties may need to be added
        if "error2" in session:
            return render_template("purchaseconfirm.html", error2=error2)
        else:
            session.pop("tempaddress", None)
            session.pop("tempcity", None)
            session.pop("tempcounty", None)
            session.pop("temppostcode", None)
            session.pop("longitude", None)
            session.pop("latitude", None)
            session.pop("price", None)
            session.pop("date", None)
            purchasedpropertystack = None
            return render_template("purchaseconfirm.html") #Finally let the user know that the property has been added to the database
        
@webpage.route("/watchlistconfirm", methods=["POST", "GET"])
def watchlistconfirm():
    username = session["id"]
    address = session["tempaddress"]
    city = session["tempcity"]
    county = session["tempcounty"]
    postcode = session["temppostcode"]
    longitude = session["longitude"]
    latitude = session["latitude"]
    found = False
    while not found: #while loop to make sure the property id is unique
        propertyid = random.randint(1000,9999) #id created per property for the composite primary key of the 'purchased' database table
        check = AppDatabase.uniqueWatchlistPropertyId(propertyid)
        if check == True:
            found = True
        else:
            pass
    
    #Stack made to check if there are too many properties already existing in the database 
    watchlistpropertystack = Stack(5)
    properties = AppDatabase.getWatchlistIds(username)
    for i in properties:
        i = formatTuple(i)
        item = int(i)
        watchlistpropertystack.push(item) #Stack pushes the existing properties
    try:
        watchlistpropertystack.push(propertyid) #New property tried to be pushed to stack
    except Exception as e:
        session["error"] = e.toString() #If stack overflow occurs, error is added to session

    if "error" in session:
        error = session["error"]
        session.pop("error", None) #Purchased property in session details are popped
        session.pop("tempaddress", None)
        session.pop("tempcity", None)
        session.pop("tempcounty", None)
        session.pop("temppostcode", None)
        session.pop("longitude", None)
        session.pop("latitude", None)
        watchlistpropertystack = None
        return render_template("watchlistconfirm.html", error=error)
    
    else: #if no error the property is added to the database

        #Once propertyid is confirmed to be unique insert the details into the property  purchased database table
        AppDatabase.insertWatchlistProperty(username, propertyid, address, city, county, postcode, longitude, latitude) #creates a list to be inserted into the database
        #Then pop all these details from the session as they are not needed anymore and more properties may need to be added
        session.pop("tempaddress", None)
        session.pop("tempcity", None)
        session.pop("tempcounty", None)
        session.pop("temppostcode", None)
        session.pop("longitude", None)
        session.pop("latitude", None)
        watchlistpropertystack = None
        return render_template("watchlistconfirm.html") #Finally let the user know that the property has been added to the database


@webpage.route("/purchasedpropertylist", methods=["POST", "GET"])
def purchasedpropertylist():
    username = session["id"]
    propertyarray = Array(5) #Array is made as it is static and has a fixed size
    idarray = Array(5)
    alist = AppDatabase.getPurchasedPropertyAddresses(username)
    for i in range(len(alist)):
        property = alist[i]
        property = formatTuple(property)
        property = property.replace("'", "")
        alist[i] = property
    counter = 0
    ids = AppDatabase.getPropertyIds(username)
    sortedids = mapLists(alist, ids)
    for i in sortedids:
        element = sortedids.index(i)
        temp = formatTuple(i)
        sortedids[element] = temp #maps the property id list and then formats each item 
    for i in alist:
        propertyarray.assign(counter, i) #appends the data from the list to the array so the program can find how many Empty slots there are in the property list
        counter += 1
    property1 = propertyarray.get(0) #All the values in the array are assigned to a variable. If the property list isn't full, the excess variables will be None
    property2 = propertyarray.get(1)
    property3 = propertyarray.get(2)
    property4 = propertyarray.get(3)
    property5 = propertyarray.get(4)
    counter = 0
    for i in sortedids:
        idarray.assign(counter, i) #appends the data from the list to the array so the program can find how many Empty slots there are in the property id list
        counter += 1
    id1 = idarray.get(0) #All the values in the array are assigned to a variable. If the property list isn't full, the excess variables will be None
    id2 = idarray.get(1)
    id3 = idarray.get(2)
    id4 = idarray.get(3)
    id5 = idarray.get(4)
    #These are then passed to the render template to be displayed
    property1link = f"viewproperty?id={id1}"
    property2link = f"viewproperty?id={id2}"
    property3link = f"viewproperty?id={id3}"
    property4link = f"viewproperty?id={id4}"
    property5link = f"viewproperty?id={id5}"
    homelink = "home?check=allPurchasedProperties" #Link created to delete all properties from the purchased property list if pressed
    return render_template("purchasedpropertylist.html", property1=property1, property2=property2, property3=property3, property4=property4, property5=property5, property1link=property1link, property2link=property2link, property3link=property3link, property4link=property4link, property5link=property5link, homelink=homelink)

@webpage.route("/watchlist", methods=["POST", "GET"])
def watchlist():
    username = session["id"]
    propertyarray = Array(5) #Array is made as it is static and has a fixed size
    idarray = Array(5)
    alist = AppDatabase.getWatchlistAddresses(username)
    for i in range(len(alist)):
        property = alist[i]
        property = formatTuple(property)
        property = property.replace("'", "")
        alist[i] = property
    counter = 0
    ids = AppDatabase.getWatchlistIds(username)
    sortedids = mapLists(alist, ids)
    for i in sortedids:
        element = sortedids.index(i)
        temp = formatTuple(i)
        sortedids[element] = temp #maps the property id list and then formats each item 
    for i in alist:
        propertyarray.assign(counter, i) #appends the data from the list to the array so the program can find how many Empty slots there are in the property list
        counter += 1
    property1 = propertyarray.get(0) #All the values in the array are assigned to a variable. If the property list isn't full, the excess variables will be None
    property2 = propertyarray.get(1)
    property3 = propertyarray.get(2)
    property4 = propertyarray.get(3)
    property5 = propertyarray.get(4)
    counter = 0
    for i in sortedids:
        idarray.assign(counter, i) #appends the data from the list to the array so the program can find how many Empty slots there are in the property id list
        counter += 1
    id1 = idarray.get(0) #All the values in the array are assigned to a variable. If the property list isn't full, the excess variables will be None
    id2 = idarray.get(1)
    id3 = idarray.get(2)
    id4 = idarray.get(3)
    id5 = idarray.get(4)
    #These are then passed to the render template to be displayed
    property1link = f"viewwatchlistproperty?id={id1}"
    property2link = f"viewwatchlistproperty?id={id2}"
    property3link = f"viewwatchlistproperty?id={id3}"
    property4link = f"viewwatchlistproperty?id={id4}"
    property5link = f"viewwatchlistproperty?id={id5}"
    homelink = "home?check=allWatchlistProperties" #Link created to delete all properties from the property watchlist if pressed
    return render_template("watchlist.html", property1=property1, property2=property2, property3=property3, property4=property4, property5=property5, property1link=property1link, property2link=property2link, property3link=property3link, property4link=property4link, property5link=property5link, homelink=homelink)

@webpage.route("/viewproperty", methods=["POST", "GET"])
def viewproperty():
    id = request.args.get("id") #This gets the parameter of the property link after the question mark. Gets the variable called id
    id = str(id)
    if id == "None":
        error = "Property doesn't exist. Please use the property finder to add properties to your purchased list."
        return render_template("viewproperty.html", error=error)
    else:
        username = int(session["id"])
        id = int(id)
        details = AppDatabase.getPurchasedPropertyDetails(username, id)
        address = details[0][2]
        city = details[0][3]
        county = details[0][4]
        postcode = details[0][5]
        longitude = details[0][6]
        latitude = details[0][7]
        price = details[0][8]
        date = details[0][9]
        try:
            valuation = AppDatabase.getPropertyValuation(username, id)#Checks if the valuation of this property is already in the database. If an error occurs it will calculate it for the first time and store it in the database
            valuation = float(valuation)
            valuation = round(valuation)
            valuation = "{:,}".format(valuation)
        except Exception:
            datelist = addDaysToDate(date)
            temp = estimateValuation(datelist[0], datelist[1]) #this formula is used to estimate the valuation of every property in the uk. Explained in the documentation.
            percentage1 = float(temp)
            percentage2 = 153.21
            valuation = calculateValuation(percentage1,percentage2, price)   
            AppDatabase.insertValuation(id, valuation)
            valuation = "{:,}".format(valuation)
        homelink = f"home?check=Purchased{id}"
        price = "{:,}".format(int(price))
        gasdate = findGasDate(date)
        return render_template("viewproperty.html", address=address, city=city, county=county, postcode=postcode, longitude=longitude, latitude=latitude, price=price, date=date, valuation=valuation, homelink=homelink, gasdate=gasdate)


@webpage.route("/viewwatchlistproperty", methods = ["POST", "GET"])
def viewwatchlistproperty():
    username = int(session["id"])
    id = request.args.get("id") #This gets the parameter of the property link after the question mark. Gets the variable called id
    id = str(id)
    homelink = f"home?check=Watchlist{id}"
    if id == "None":
        error1 = "Property doesn't exist. Please use the property finder to add properties to your property watchlist."
        return render_template("viewwatchlistproperty.html", error1=error1)
    else:
        id = int(id)
        details = AppDatabase.getWatchlistPropertyDetails(username, id) #All the watchlist property details are retrieved from the database
        address = details[0][2]
        city = details[0][3]
        county = details[0][4]
        postcode = details[0][5]
        longitude = details[0][6]
        latitude = details[0][7]
        try:
            paon = getPaonFromAddress(address)
            data = findPurchasedPropertyData(postcode, paon)
        except AppException: #If the property is not found in the database an error is raised
            error2 = "No data of property before 1995! Valuation cannot be calculated"
            return render_template("viewwatchlistproperty.html", error1=error2)
        else:
            if len(data) > 6: #First checks if the length of the data is bigger than 6 as only the 3 most recent purchases are required
                num = len(data)
                delete = num - 6
                data = data[:delete] #deletes the elements of the list after the first 6

            print(data)
            mostrecentdate = data[1]
            mostrecentprice = data[0]
            datelist = addDaysToDate(mostrecentdate)
            temp = estimateValuation(datelist[0], datelist[1])
            percentage1 = float(temp)
            percentage2 = 153.21
            valuation = calculateValuation(percentage1, percentage2, mostrecentprice) #finds the estimated valuation of the property using the most recent details. Valuation will still be displayed even if there are no post 2014 purchases
            valuation = "{:,}".format(valuation)

            if len(data) == 2:
                check1 = validPropertyWatchlistDate(data[1]) #Checks if the date is valid for the watchlist
                if check1 == True:
                    price = data[0] #If the date is valid, the data will be added to the watchlist table in the database and it will be displayed on the webpage
                    date = data[1]
                    price = "{:,}".format(int(price))
                    return render_template("viewwatchlistproperty.html", address=address, city=city, county=county, postcode=postcode, longitude=longitude, latitude=latitude, valuation=valuation, price1=price, date1=date, homelink=homelink)
                else:
                    error3 = "No data of property after and including 2014!" #If the date isn't valid an error is made and the render template is returned with an error. Valuation and other details still shown 
                    return render_template("viewwatchlistproperty.html", address=address, city=city, county=county, postcode=postcode, longitude=longitude, latitude=latitude, error3=error3, valuation=valuation, homelink=homelink)

            elif len(data) == 4:
                check1 = validPropertyWatchlistDate(data[1]) #Checks if the date is valid for the watchlist
                if check1 == True:
                    price1 = data[0] #If the date is valid, the data will be added to the watchlist table in the database and it will be displayed on the webpage
                    date1 = data[1]
                    price1 = "{:,}".format(int(price1))
                    check2 = validPropertyWatchlistDate(data[3])
                    if check2 == True:
                        price2 = data[2] #If the date is valid, the data will be added to the watchlist table in the database and it will be displayed on the webpage
                        date2 = data[3]
                        price2 = "{:,}".format(int(price2))
                        return render_template("viewwatchlistproperty.html", address=address, city=city, county=county, postcode=postcode, longitude=longitude, latitude=latitude, valuation=valuation, price1=price1, date1=date1, price2=price2, date2=date2, homelink=homelink)
                    else:
                        return render_template("viewwatchlistproperty.html", address=address, city=city, county=county, postcode=postcode, longitude=longitude, latitude=latitude, valuation=valuation, price1=price1, date1=date1, homelink=homelink)
                else:
                    error3 = "No data of property after and including 2014!" #If the date isn't valid an error is made and the render template is returned with an error. Valuation and other details still shown 
                    return render_template("viewwatchlistproperty.html", address=address, city=city, county=county, postcode=postcode, longitude=longitude, latitude=latitude, error3=error3, valuation=valuation, homelink=homelink)

            elif len(data) == 6:
                check1 = validPropertyWatchlistDate(data[1]) #Checks if the date is valid for the watchlist
                if check1 == True:
                    price1 = data[0] #If the date is valid, the data will be added to the watchlist table in the database and it will be displayed on the webpage
                    date1 = data[1]
                    price1 = "{:,}".format(int(price1))
                    check2 = validPropertyWatchlistDate(data[3])
                    if check2 == True:
                        price2 = data[2] #If the date is valid, the data will be added to the watchlist table in the database and it will be displayed on the webpage
                        date2 = data[3]
                        price2 = "{:,}".format(int(price2))
                        check3 = validPropertyWatchlistDate(data[5])
                        if check3 == True:
                            price3 = data[4] #If the date is valid, the data will be added to the watchlist table in the database and it will be displayed on the webpage
                            date3 = data[5]
                            price3 = "{:,}".format(int(price3))
                            return render_template("viewwatchlistproperty.html", address=address, city=city, county=county, postcode=postcode, longitude=longitude, latitude=latitude, valuation=valuation, price1=price1, date1=date1, price2=price2, date2=date2, price3=price3, date3=date3, homelink=homelink)
                        else:
                            return render_template("viewwatchlistproperty.html", address=address, city=city, county=county, postcode=postcode, longitude=longitude, latitude=latitude, valuation=valuation, price1=price1, date1=date1, price2=price2, date2=date2, homelink=homelink)
                    else:
                        return render_template("viewwatchlistproperty.html", address=address, city=city, county=county, postcode=postcode, longitude=longitude, latitude=latitude, valuation=valuation, price1=price1, date1=date1, homelink=homelink)
                else:
                    error3 = "No data of property after and including 2014!" #If the date isn't valid an error is made and the render template is returned with an error. Valuation and other details still shown 
                    return render_template("viewwatchlistproperty.html", address=address, city=city, county=county, postcode=postcode, longitude=longitude, latitude=latitude, error3=error3, valuation=valuation, homelink=homelink)
            
        if "error" in session:
            return render_template("purchaselistmaker.html", address=address, city=city, county=county, postcode=postcode, longitude=longitude, latitude=latitude, error2=error2, homelink=homelink)
    
@webpage.route("/propertyportfolio", methods = ["POST", "GET"])
def propertyportfolio():
    username = int(session["id"])
    allwatchlist = AppDatabase.getWatchlistIds(username)
    WatchlistNo = 0
    for i in range(len(allwatchlist)):
        WatchlistNo += 1
    valuationresult = AppDatabase.getAllPropertyValuation(username)
    valuationlist = []
    for i in valuationresult:
        i = formatTuple(i)
        valuationlist.append(i)
    TotalValuation = 0
    for i in range(len(valuationlist)):
        TotalValuation += float(valuationlist[i])
    TotalValuation = round(TotalValuation)
    priceresult = AppDatabase.getAllPropertyPrice(username)
    pricelist = []
    for i in priceresult:
        i = formatTuple(i)
        pricelist.append(i)
    TotalPrice = 0
    PriceNo = 0
    for i in range(len(pricelist)):
        PriceNo += 1
        TotalPrice += float(pricelist[i])
    TotalPrice = round(TotalPrice)
    temp = TotalValuation - TotalPrice
    TotalProfit = None
    TotalLoss = None
    if temp > 0:
        TotalProfit = temp
    else:
        TotalLoss = 0 - temp
    if TotalProfit != None:
        TotalPrice = "{:,}".format(TotalPrice)
        TotalValuation = "{:,}".format(TotalValuation)
        TotalProfit = "{:,}".format(TotalProfit)
        return render_template("propertyportfolio.html", TotalValuation=TotalValuation, TotalPrice=TotalPrice, TotalProfit=TotalProfit, PriceNo=PriceNo, WatchlistNo=WatchlistNo)
    elif TotalLoss != None:
        TotalPrice = "{:,}".format(TotalPrice)
        TotalValuation = "{:,}".format(TotalValuation)
        TotalLoss = "{:,}".format(TotalLoss)
        return render_template("propertyportfolio.html", TotalValuation=TotalValuation, TotalPrice=TotalPrice, TotalLoss=TotalLoss, PriceNo=PriceNo, WatchlistNo=WatchlistNo)


#These are used for testing purposes

#AppDatabase.clearUserDetails()
#AppDatabase.clearAllValuation(3586) #This needs to come before the PurchasedProperties as it uses data from the purchased table
#AppDatabase.clearAllPurchasedPropertiesDetails(3586)
#details = AppDatabase.getWatchlistPropertyDetails(7612, 6495)
#print(details)

#allows the app to be run in python and turns debugging mode on to make it easier to update the webpage
if __name__ == '__main__':
    webpage.run(debug=True)

#endregion




 