const express = require('express');
const cors = require('cors');
const morgan = require('morgan');
const jwt = require('jsonwebtoken');

const habitacionRouter = require('./controller/habitacionController');

const app = express();
const PORT = 3002;

app.use(morgan('dev'));
app.use(cors());
app.use(express.json());

const SECRET_KEY = 'CLAVE_SECRETA_LEYTON';


function verificarToken(req, res, next) {
  const bearerHeader = req.headers['authorization'];
  if (!bearerHeader) return res.status(401).json({ error: 'Token no proporcionado' });

  const token = bearerHeader.split(' ')[1];
  jwt.verify(token, SECRET_KEY, (err, decoded) => {
    if (err) return res.status(403).json({ error: 'Token inválido o expirado' });
    req.usuario = decoded;
    next();
  });
}

app.use('/api/habitaciones', habitacionRouter);

app.get('/', (req, res) => {
  res.json({ mensaje: 'API de Habitaciones funcionando correctamente' });
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Microservicio de Habitaciones ejecutándose en http://192.168.100.3:${PORT}`);
});
