from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Configurez la chaîne de connexion pour SQL Server
app.config['SQLALCHEMY_DATABASE_URI'] = 'mssql+pymssql://sa:StrongPassword123!@sqlserver:1433/BookingDB'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialiser SQLAlchemy
db = SQLAlchemy(app)

# Modèle pour la réservation
class Bookings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(10), nullable=False)

    def __repr__(self):
        return f'<Bookings {self.customer_name}>'

# Endpoint pour créer une réservation
@app.route('/bookings', methods=['POST'])
def create_booking():
    data = request.get_json()
    new_booking = Bookings(customer_name=data['customer_name'], date=data['date'])
    db.session.add(new_booking)
    db.session.commit()
    return jsonify({'message': 'Booking created!'}), 201

# Endpoint pour récupérer toutes les réservations
@app.route('/bookings', methods=['GET'])
def get_bookings():
    bookings = Bookings.query.all()
    return jsonify([{'id': b.id, 'customer_name': b.customer_name, 'date': b.date} for b in bookings])

if __name__ == '__main__':
    # Lancer l'application Flask
    app.run(host='0.0.0.0', port=5000)
