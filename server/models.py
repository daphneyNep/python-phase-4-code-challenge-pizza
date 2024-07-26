from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from sqlalchemy.orm import validates, relationship
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy_serializer import SerializerMixin

metadata = MetaData(
    naming_convention={
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    }
)

db = SQLAlchemy(metadata=metadata)


class Restaurant(db.Model, SerializerMixin):
    __tablename__ = "restaurants"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    
    # Establish relationship to RestaurantPizza with cascade delete
    restaurant_pizzas = db.relationship('RestaurantPizza', back_populates='restaurant', cascade='all, delete-orphan')
    # Many-to-many relationship through RestaurantPizza
    pizzas = db.relationship('Pizza', secondary='restaurant_pizzas', back_populates='restaurants')

    serialize_rules = ('-restaurant_pizzas.pizza',)  # Exclude nested pizza information
    serialize_depth = 1  # Set the depth of serialization

    def __repr__(self):
        return f"<Restaurant {self.id}, {self.name}, {self.address}>"

class Pizza(db.Model, SerializerMixin):
    __tablename__ = "pizzas"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    ingredients = db.Column(db.String(255), nullable=False)
    
    # Establish relationship to RestaurantPizza with cascade delete
    restaurant_pizzas = db.relationship('RestaurantPizza', back_populates='pizza', cascade='all, delete-orphan')
    # Many-to-many relationship through RestaurantPizza
    restaurants = db.relationship('Restaurant', secondary='restaurant_pizzas', back_populates='pizzas')

    serialize_rules = ('-restaurant_pizzas.restaurant',)  # Exclude nested restaurant information
    serialize_depth = 1  # Set the depth of serialization

    def __repr__(self):
        return f"<Pizza {self.id}, {self.name}, {self.ingredients}>"

class RestaurantPizza(db.Model, SerializerMixin):
    __tablename__ = "restaurant_pizzas"

    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False)
    pizza_id = db.Column(db.Integer, db.ForeignKey('pizzas.id'), nullable=False)
    price = db.Column(db.Float, nullable=False)

    # Relationships
    restaurant = db.relationship('Restaurant', back_populates='restaurant_pizzas')
    pizza = db.relationship('Pizza', back_populates='restaurant_pizzas')

    serialize_rules = ('-restaurant.restaurant_pizzas', '-pizza.restaurant_pizzas')
    serialize_depth = 1

    @validates('price')
    def validate_price(self, key, value):
        if not (1 <= value <= 30):
            raise ValueError("Price must be between 1 and 30")
        return value

    def __repr__(self):
        return f"<RestaurantPizza {self.id}, {self.price}, {self.restaurant_id}, {self.pizza_id}>"
