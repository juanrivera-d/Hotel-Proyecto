const express = require('express');
const mysql = require('mysql2');

const app = express();
const port = 3005;

const db = mysql.createPool({
    host: 'db-mysql',
    user: 'root',
    password: 'root',
    database: 'bd_analytics',
    waitForConnections: true,
    connectionLimit: 10,
    queueLimit: 0
});

// 1. GET /api/analytics/trafico-logs
app.get('/api/analytics/trafico-logs', (req, res) => {
    db.query('SELECT * FROM resumen_trafico_logs', (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json({ modulo: 'Tráfico Logs', datos: results });
    });
});

// 2. GET /api/analytics/sentimiento-resenas
app.get('/api/analytics/sentimiento-resenas', (req, res) => {
    db.query('SELECT * FROM resumen_sentimiento_resenas', (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json({ modulo: 'Sentimiento Reseñas', datos: results });
    });
});

// 3. GET /api/analytics/ocupacion-mensual
app.get('/api/analytics/ocupacion-mensual', (req, res) => {
    db.query('SELECT * FROM resumen_ocupacion_mensual', (err, results) => {
        if (err) return res.status(500).json({ error: err.message });
        res.json({ modulo: 'Ocupación Mensual', datos: results });
    });
});

app.listen(port, () => {
    console.log(`Microservicio Backend Analítico (Rol 3) escuchando en el puerto ${port}`);
});
