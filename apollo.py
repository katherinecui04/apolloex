import sqlite3
from flask import Flask, request, jsonify

#SQLite 
#C library that provides a database, sqlite3 to interact with SQLite databases directly from Python code

#Flask
#when you enter a URL, it goes to a server. use Flask to build back-end server. 
#Flask is better for creating lightweight microservices & Django for creating web apps/websites
#flask.request - request object created when start Flask server, request context stack (to keep track of request data)
#flask.request - 'Remembers the matched endpoint and view arguments'
#flask.jsonify function - return jsonify() = send a JSON response w/ arg detail to the browser

#https://docs.python.org/2/library/sqlite3.html 
#https://stackoverflow.com/questions/15856976/transactions-with-python-sqlite3
#https://blog.miguelgrinberg.com/post/designing-a-restful-api-with-python-and-flask

app = Flask(__name__) #creates a Flask application object 

def init_db():
    #create a Connection object that represents the database 
    #data will be stored in the vehicles.db file 
    conn = sqlite3.connect('vehicles.db')
    conn.isolation_level = None #autocommit mode (each SQL statement = transaction, no explicit commits needed) 
    c = conn.cursor() #create a Cursor object 
        
    try:  
        #clear existing if exists  
        c.execute("DROP TABLE IF EXISTS vehicles")

        #create vehicles table     
        #call execute() method to perform SQL commands
        #primary key uniquely identifies a row (vehicle uniquely identified by VIN)
        #decimal(p, s) - p = precision (total # digits), s = scale (# digits in fractional part)
        c.execute('''CREATE TABLE IF NOT EXISTS vehicles 
                (vin text PRIMARY KEY, 
                  manufacturer_name text, 
                  description text, 
                  horsepower integer, 
                  model_name text, 
                  model_year integer,
                  purchase_price decimal(10, 2),
                  fuel_type text)''') 
        
        #FOR TESTING PURPOSES - 1 row
        c.execute("INSERT INTO vehicles VALUES ('4Y1SL65848Z411439', 'ford', 'long-running muscle car', '435', 'mustang', '2015', '20000.00', 'premium')")
    
    except sqlite3.Error as e:
        print(f"database init error: {e}")
        c.execute("rollback") #back out of the database changes, in case of error 

    finally: 
        c.close() #close cursor 
        conn.close() #close connection

#GET /vehicle endpoint 
#resource exposed by service - vehicles, use HTTP method get (retrieve vehicle data)
#app.route = Flask decorator, bind URL path to function 
#when receive HTTP GET request to the URL, looks for function decorated w/ '@app.route('/vehicle', methods = ['GET'])' 
@app.route('/vehicle', methods = ['GET']) #get_vehicles function mapped with the “/vehicle” path
def get_vehicles():
    try:
        #no need for commits in get_vehicles() - reading from only, not writing to 
        conn = sqlite3.connect('vehicles.db')
        conn.row_factory = sqlite3.Row  #'dictionary cursor' - return 'dictionary' rows after fetchall()
        c = conn.cursor()
        c.execute("SELECT * FROM vehicles") #every row from vehicles table 
        all_vehicles = c.fetchall() #fetches all the rows of query result

        #.upper() to adjust for case insensitivity 
        vehicles_list = [
            {
                'vin': v['vin'].upper(),
                'manufacturer_name': v['manufacturer_name'],
                'description': v['description'],
                'horsepower': v['horsepower'],
                'model_name': v['model_name'],
                'model_year': v['model_year'],
                'purchase_price': v['purchase_price'],
                'fuel_type': v['fuel_type']
            }
            for v in all_vehicles
        ]   
        return jsonify(vehicles_list), 200 #returns JSON response containing fetched vehicle data ('200 OK')

    except sqlite3.Error as e:
        print(f"get vehicles error: {e}")
        return jsonify({"error": "failed to get vehicles"}), 500 #500 - "Internal Server Error"

    finally: 
        c.close() 
        conn.close() 

#POST /vehicle endpoint 
@app.route('/vehicle', methods = ['POST']) 
def add_vehicle():
    try: 
        conn = sqlite3.connect('vehicles.db')
        c = conn.cursor()  
        vehicle_data = request.get_json() #incoming JSON request data 
        #validate incoming request data - ensure all attributes present 
        for attribute in ['vin', 'manufacturer_name', 'description', 'horsepower', 'model_name', 'model_year', 'purchase_price', 'fuel_type']:
            if attribute not in vehicle_data: 
                return jsonify({"error": "missing attribute"}), 400 

        #extract attributes 
        vin = vehicle_data['vin'].upper()
        manufacturer_name = vehicle_data['manufacturer_name']
        description = vehicle_data['description']
        horsepower = vehicle_data['horsepower']
        model_name = vehicle_data['model_name']
        model_year = vehicle_data['model_year']
        purchase_price = vehicle_data['purchase_price']
        fuel_type = vehicle_data['fuel_type']

        ###VALIDATION ERROR CHECK HERE (422) i.e. vin is not 17 characters, negative numbers

        #new row in vehicles tables w/ new vehicle 
        #'?' - when parameters unknown when statement prepared, use '?' placeholder 
        c.execute("""INSERT INTO vehicles (vin, manufacturer_name, description, horsepower, model_name, model_year, purchase_price, fuel_type) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", (vin, manufacturer_name, description, horsepower, model_name, model_year, purchase_price, fuel_type))
        conn.commit()

        new_vehicle = {
            'vin': vin, 
            'manufacturer_name': manufacturer_name, 
            'description': description, 
            'horsepower': horsepower, 
            'model_name': model_name, 
            'model_year': model_year, 
            'purchase_price': purchase_price, 
            'fuel_type': fuel_type
        } 
        return jsonify(new_vehicle), 201 #JSON-formatted representation of the new vehicle, 201 - "Created" 

    except sqlite3.Error as e:
        print(f"post vehicle error: {e}")
        return jsonify({"error": "failed to add vehicle"}), 500 

    finally: 
        c.close() 
        conn.close() 

#GET /vehicle/<vin> endpoint
@app.route('/vehicle/<vin>', methods = ['GET']) 
def get_vehicle(vin):
    try:
        conn = sqlite3.connect('vehicles.db')
        conn.row_factory = sqlite3.Row  
        c = conn.cursor()
        c.execute("SELECT * FROM vehicles WHERE UPPER(vin) = ?", (vin,))
        unique_vehicle = c.fetchone() #fetches the row 

        if unique_vehicle: 
            #https://flask.palletsprojects.com/en/stable/api/#flask.json.jsonify (dict or list to JSON response)
            return jsonify(dict(unique_vehicle)), 200 
        else:
            return jsonify({"error": "vehicle not found"}), 404 #404 - "Not Found Error"

    except sqlite3.Error as e:
        print(f"get vehicle/<vin> error: {e}")
        return jsonify({"error": "failed to get vehicle"}), 500 #500 - "Internal Server Error"

    finally: 
        c.close() 
        conn.close() 

#PUT /vehicle/<vin> endpoint
@app.route('/vehicle/<vin>', methods = ['PUT']) 
def update_vehicle(vin):
    try: 
        conn = sqlite3.connect('vehicles.db')
        c = conn.cursor()  
        vehicle_data = request.get_json() #incoming JSON request data 
        #validate incoming request data - ensure all attributes present 
        for attribute in ['manufacturer_name', 'description', 'horsepower', 'model_name', 'model_year', 'purchase_price', 'fuel_type']:
            if attribute not in vehicle_data: 
                return jsonify({"error": "missing attribute"}), 400 

        #extract attributes & case-insensitivity
        vin = vin.upper() 
        manufacturer_name = vehicle_data['manufacturer_name']
        description = vehicle_data['description']
        horsepower = vehicle_data['horsepower']
        model_name = vehicle_data['model_name']
        model_year = vehicle_data['model_year']
        purchase_price = vehicle_data['purchase_price']
        fuel_type = vehicle_data['fuel_type']

        ###VALIDATION ERROR CHECK HERE (422)

        #ensure vehicle exists 
        c.execute("SELECT * FROM vehicles WHERE UPPER(vin) = ?", (vin,))
        unique_vehicle = c.fetchone() #fetches the row 
        if not unique_vehicle: 
            return jsonify({"error": "vehicle not found"}), 404 #404 - "Not Found Error"

        #update vehicle
        c.execute('''UPDATE vehicles SET manufacturer_name = ?, description = ?, horsepower = ?, model_name = ?, model_year = ?, purchase_price = ?, fuel_type = ? WHERE vin = ?''', 
                  (manufacturer_name, description, horsepower, model_name, model_year, purchase_price, fuel_type, vin))
        conn.commit()

        updated_vehicle = {
            'vin': vin, 
            'manufacturer_name': manufacturer_name, 
            'description': description, 
            'horsepower': horsepower, 
            'model_name': model_name, 
            'model_year': model_year, 
            'purchase_price': purchase_price, 
            'fuel_type': fuel_type
        } 
        return jsonify(updated_vehicle), 200 

    except sqlite3.Error as e:
        print(f"put vehicle/<vin> error: {e}")
        return jsonify({"error": "failed to update vehicle"}), 500 

    finally: 
        c.close() 
        conn.close() 

#DELETE /vehicle/<vin> endpoint
@app.route('/vehicle/<vin>', methods = ['DELETE'])
def delete_vehicle(vin):
    try: 
        conn = sqlite3.connect('vehicles.db')
        c = conn.cursor()  
        vin = vin.upper() 
        c.execute("SELECT * FROM vehicles WHERE vin = ?", (vin,))
        vehicle = c.fetchone() 
        if not vehicle: 
            return jsonify({"error": "vehicle not found"}), 404
        
        #delete vehicle from table 
        c.execute("DELETE FROM vehicles WHERE UPPER(vin) = ?", (vin,))
        conn.commit() 
        return '', 204 #204 - "No Content"
    
    except sqlite3.Error as e:
        print(f"delete vehicles error: {e}")
        return jsonify({"error": "failed to delete vehicle"}), 500 #500 - "Internal Server Error"

if __name__ == '__main__':
    init_db() 
    app.run(debug = True)

#example tests 
'''
http://127.0.0.1:5000/vehicle on browser 
Open second terminal window 
curl -X POST http://127.0.0.1:5000/vehicle -H "Content-Type: application/json" -d '{"vin": "5Y1SL65848Z411441", "manufacturer_name": "toyota", "description": "mid-size sedan", "horsepower": 200, "model_name": "camry", "model_year": 2022, "purchase_price": 18000.00, "fuel_type": "hybrid"}'
http://127.0.0.1:5000/vehicle/4Y1SL65848Z411439 on browser 
curl -X PUT http://127.0.0.1:5000/vehicle/5Y1SL65848Z411441 -H "Content-Type: application/json" -d '{"manufacturer_name": "toyota", "description": "mid-size sedan", "horsepower": 200, "model_name": "camry", "model_year": 2023, "purchase_price": 18000.00, "fuel_type": "hybrid"}'
curl -X DELETE http://127.0.0.1:5000/vehicle/5Y1SL65848Z411441
'''