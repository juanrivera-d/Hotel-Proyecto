const express = require('express');
const cors = require('cors');
const morgan = require('morgan');
const jwt = require('jsonwebtoken');

const hotelController = require('./controllers/hotelController');

const app = express();
const PORT = 3001;
const SECRET_KEY = 'CLAVE_SECRETA_LEYTON';

app.use(cors({ origin: '*' }));
app.use(morgan('dev'));
app.use(express.json());

function verificarToken(req, res, next) {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ mensaje: 'Token no proporcionado' });
  }

  const token = authHeader.split(' ')[1];
  jwt.verify(token, SECRET_KEY, (err, decoded) => {
    if (err) return res.status(401).json({ mensaje: 'Token inválido o expirado' });
    req.usuario = decoded;
    next();
  });
}

function verificarRolAdmin(req, res, next) {
  if (!req.usuario || !req.usuario.rol || req.usuario.rol.toLowerCase() !== 'admin') {
    return res.status(403).json({ mensaje: 'No tienes permisos para realizar esta acción' });
  }
  next();
}

app.post('/api/login', hotelController.iniciarSesion);
app.post('/api/usuarios', hotelController.crearUsuario);

app.get('/api/usuarios', verificarToken, verificarRolAdmin, hotelController.listarUsuarios);
app.get('/api/usuarios/documento/:documento', verificarToken, hotelController.obtenerUsuarioPorDocumento);
app.get('/api/usuarios/:id', verificarToken, hotelController.obtenerUsuarioPorId);
app.put('/api/usuarios/:id', verificarToken, verificarRolAdmin, hotelController.actualizarUsuario);
app.put('/api/perfil', verificarToken, hotelController.actualizarMiPerfil);

app.get('/', (req, res) => {
  res.json({ mensaje: 'API de Usuarios y Autenticación activa' });
});

// Evita que el proceso se caiga por errores no controlados
process.on('uncaughtException', (err) => {
  console.error('Excepción no controlada:', err);
});

process.on('unhandledRejection', (reason) => {
  console.error('Promesa rechazada sin manejar:', reason);
});

const server = app.listen(PORT, '0.0.0.0', () => {
  console.log(`Usuarios escuchando en el puerto ${PORT}`);
});

server.on('error', (err) => {
  if (err.code === 'EADDRINUSE') {
    console.error(`El puerto ${PORT} ya está en uso`);
  } else {
    console.error('Error al iniciar el servidor:', err);
  }
});
