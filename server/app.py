#!/usr/bin/env python3
from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask import Flask, request, make_response, jsonify, abort
from flask_restful import Api, Resource
import os



BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False


migrate = Migrate(app, db)

db.init_app(app)

# Initialize Flask-RESTful
api = Api(app)



# Define resources
class RestaurantResource(Resource):
    def get(self, restaurant_id):
        restaurant = db.session.get(Restaurant, restaurant_id)
        if not restaurant:
            return jsonify({"error": "Restaurant not found"}), 404

        restaurant_pizzas = RestaurantPizza.query.filter_by(restaurant_id=restaurant_id).all()
        restaurant_pizzas_list = []
        for rp in restaurant_pizzas:
            pizza = db.session.get(Pizza, rp.pizza_id)
            if pizza:
                restaurant_pizzas_list.append({
                    "id": rp.id,
                    "pizza": pizza.to_dict(only=('id', 'name', 'ingredients')),
                    "pizza_id": rp.pizza_id,
                    "price": rp.price,
                    "restaurant_id": rp.restaurant_id
                })

        response = {
            "address": restaurant.address,
            "id": restaurant.id,
            "name": restaurant.name,
            "restaurant_pizzas": restaurant_pizzas_list
        }

        return jsonify(response), 200

    def delete(self, restaurant_id):
        restaurant = db.session.get(Restaurant, restaurant_id)
        if not restaurant:
            return jsonify({"error": "Restaurant not found"}), 404

        RestaurantPizza.query.filter_by(restaurant_id=restaurant_id).delete()
        db.session.delete(restaurant)
        db.session.commit()

        return '', 204

class RestaurantListResource(Resource):
    def get(self):
        restaurants = Restaurant.query.all()
        return [restaurant.to_dict(only=('id', 'name', 'address')) for restaurant in restaurants], 200

class PizzaResource(Resource):
    def get(self, pizza_id):
        pizza = db.session.get(Pizza, pizza_id)
        if not pizza:
            abort(404)
        return pizza.to_dict(only=('id', 'name', 'ingredients')), 200

    def delete(self, pizza_id):
        pizza = db.session.get(Pizza, pizza_id)
        if not pizza:
            abort(404)
        db.session.delete(pizza)
        db.session.commit()
        return '', 204

class PizzaListResource(Resource):
    def get(self):
        pizzas = Pizza.query.all()
        return [pizza.to_dict(only=('id', 'name', 'ingredients')) for pizza in pizzas], 200

class RestaurantPizzaResource(Resource):
    def get(self, restaurant_pizza_id):
        restaurant_pizza = db.session.get(RestaurantPizza, restaurant_pizza_id)
        if not restaurant_pizza:
            abort(404)
        return restaurant_pizza.to_dict(only=('id', 'price')), 200

    def delete(self, restaurant_pizza_id):
        restaurant_pizza = db.session.get(RestaurantPizza, restaurant_pizza_id)
        if not restaurant_pizza:
            abort(404)
        db.session.delete(restaurant_pizza)
        db.session.commit()
        return '', 204

class RestaurantPizzaCreateResource(Resource):
    def post(self):
        data = request.get_json()
    
        # Validate request data
        if not data or not all(key in data for key in ('price', 'pizza_id', 'restaurant_id')):
            return jsonify({"errors": ["Invalid request data"]}), 400
    
        price = data.get('price')
        pizza_id = data.get('pizza_id')
        restaurant_id = data.get('restaurant_id')

        try:
            # Validate price
            if not (1 <= price <= 30):
                raise ValueError("Price must be between 1 and 30")

            # Validate existence of pizza and restaurant
            pizza = db.session.get(Pizza, pizza_id)
            restaurant = db.session.get(Restaurant, restaurant_id)

            if not pizza:
                return jsonify({"errors": ["Pizza not found"]}), 404
            if not restaurant:
                return jsonify({"errors": ["Restaurant not found"]}), 404

            # Create and save RestaurantPizza
            restaurant_pizza = RestaurantPizza(price=price, pizza_id=pizza_id, restaurant_id=restaurant_id)
            db.session.add(restaurant_pizza)
            db.session.commit()

            # Prepare the response data
            response = {
                'id': restaurant_pizza.id,
                'price': restaurant_pizza.price,
                'pizza_id': restaurant_pizza.pizza_id,
                'restaurant_id': restaurant_pizza.restaurant_id,
                'pizza': pizza.to_dict(only=('id', 'name', 'ingredients')),
                'restaurant': restaurant.to_dict(only=('id', 'name', 'address'))
            }
            return jsonify(response), 201

        except ValueError:
            return jsonify({"errors": ["validation errors"]}), 400
    
# Define index route
@app.route("/")
def index():
    return "<h1>Code challenge</h1>"

@app.route('/restaurant_pizzas', methods=['POST'])
def create_restaurant_pizza():
    data = request.get_json()
    errors = []

    # Validate the input
    if not all(key in data for key in ('price', 'pizza_id', 'restaurant_id')):
        errors.append('Missing data')
    
    if errors:
        return jsonify({'errors': errors}), 400

    try:
        price = data['price']
        pizza_id = data['pizza_id']
        restaurant_id = data['restaurant_id']

        # Check if the pizza and restaurant exist
        pizza = Pizza.query.get(pizza_id)
        restaurant = Restaurant.query.get(restaurant_id)

        if not pizza or not restaurant:
            errors.append('Pizza or Restaurant not found')
            return jsonify({'errors': errors}), 404

        # Create a new RestaurantPizza instance
        new_restaurant_pizza = RestaurantPizza(
            price=price,
            pizza_id=pizza_id,
            restaurant_id=restaurant_id
        )

        db.session.add(new_restaurant_pizza)
        db.session.commit()

        # Construct the response data
        response_data = {
            "id": new_restaurant_pizza.id,
            "pizza": {
                "id": pizza.id,
                "name": pizza.name,
                "ingredients": pizza.ingredients
            },
            "pizza_id": new_restaurant_pizza.pizza_id,
            "price": new_restaurant_pizza.price,
            "restaurant": {
                "id": restaurant.id,
                "name": restaurant.name,
                "address": restaurant.address
            },
            "restaurant_id": new_restaurant_pizza.restaurant_id
        }

        return jsonify(response_data), 201

    except ValueError as e:
        errors.append('validation errors')
        return jsonify({'errors': errors}), 400
    
@app.route('/restaurants/<int:id>', methods=['GET'])
def get_restaurant(id):
    restaurant = db.session.get(Restaurant, id)
    if restaurant is None:
        return jsonify({"error": "Restaurant not found"}), 404
    return jsonify(restaurant.to_dict())
    
    
@app.route('/restaurants/<int:id>', methods=['DELETE'])
def delete_restaurant(id):
    restaurant = db.session.get(Restaurant, id)
    if not restaurant:
        return jsonify({"error": "Restaurant not found"}), 404
    
    RestaurantPizza.query.filter_by(restaurant_id=id).delete()
    db.session.delete(restaurant)
    db.session.commit()
    return '', 204

# Add resource routes
api.add_resource(RestaurantListResource, '/restaurants')
api.add_resource(PizzaListResource, '/pizzas')
api.add_resource(PizzaResource, '/pizzas/<int:pizza_id>')
api.add_resource(RestaurantPizzaResource, '/restaurant_pizzas/<int:restaurant_pizza_id>')
api.add_resource(RestaurantPizzaCreateResource, '/restaurant_pizzas')


# Run Flask application
if __name__ == "__main__":
    app.run(port=5555, debug=True)
