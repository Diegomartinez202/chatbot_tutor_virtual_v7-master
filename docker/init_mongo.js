db = db.getSiblingDB('chatbot_db');

db.createCollection('users');
db.createCollection('logs');
db.createCollection('test_logs');
db.createCollection('statistics');

db.users.insertOne({
    nombre: "Administrador",
    email: "admin@example.com",
    rol: "admin",
    password: "$2b$12$QZD7zHAGzWYEC2jMsOdqVe2kJxAcS/qPZAzZafk7QoUwNlGNTFxqW" // bcrypt real
});
