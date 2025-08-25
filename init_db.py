from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timedelta

# Create SQLite database
engine = create_engine('sqlite:///ecommerce.db')
Base = declarative_base()

# Define models
class Customer(Base):
    __tablename__ = 'customers'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    orders = relationship('Order', back_populates='customer')

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)
    category = Column(String(50))
    
    # Relationships
    orders = relationship('Order', back_populates='product')

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    order_date = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    customer = relationship('Customer', back_populates='orders')
    product = relationship('Product', back_populates='orders')

def create_sample_data(session):
    # Create sample customers
    customers = [
        Customer(name='John Doe', email='john@example.com'),
        Customer(name='Jane Smith', email='jane@example.com'),
        Customer(name='Bob Johnson', email='bob@example.com'),
    ]
    
    # Create sample products
    products = [
        Product(name='Laptop', price=1200.00, category='Electronics'),
        Product(name='Smartphone', price=800.00, category='Electronics'),
        Product(name='Headphones', price=150.00, category='Accessories'),
        Product(name='Mouse', price=50.00, category='Accessories'),
    ]
    
    # Add customers and products to session
    session.add_all(customers + products)
    session.commit()
    
    # Create sample orders
    orders = [
        Order(customer_id=1, product_id=1, quantity=1, order_date=datetime.utcnow() - timedelta(days=5)),
        Order(customer_id=1, product_id=3, quantity=2, order_date=datetime.utcnow() - timedelta(days=3)),
        Order(customer_id=2, product_id=2, quantity=1, order_date=datetime.utcnow() - timedelta(days=2)),
        Order(customer_id=3, product_id=4, quantity=3, order_date=datetime.utcnow() - timedelta(days=1)),
        Order(customer_id=2, product_id=1, quantity=1, order_date=datetime.utcnow()),
    ]
    
    session.add_all(orders)
    session.commit()

def init_db():
    # Create all tables
    Base.metadata.create_all(engine)
    
    # Create a new session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Check if we already have data
        if not session.query(Customer).first():
            create_sample_data(session)
            print("Database initialized with sample data!")
        else:
            print("Database already contains data.")
    except Exception as e:
        print(f"Error initializing database: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    init_db()
