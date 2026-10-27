const express = require('express');
const morgan = require('morgan');
const cors = require('cors');
const reservaController = require('./controllers/reservaController');
const reservaModel = require('./models/reservaModel');

const app = express();

app.use(morgan('dev'));
app.use(cors());
app.use(express.json());

// Debe ir antes de /api/reservas/:id para que "disponibilidad" no se tome como id
app.get('/api/reservas/disponibilidad', async (req, res) => {
    try {
        const { fechaEntrada, fechaSalida } = req.query;
        if (!fechaEntrada || !fechaSalida) {
            return res.status(400).json({ error: 'Se requieren fechaEntrada y fechaSalida' });
        }

        const resHab = await fetch(process.env.URL_HABITACIONES);
        const todasHabitaciones = await resHab.json();

        const disponibles = await reservaModel.obtenerDisponibilidad(fechaEntrada, fechaSalida, todasHabitaciones);
        res.json(disponibles);
    } catch (error) {
        console.error('Error al consultar disponibilidad:', error);
        res.status(500).json({ error: 'Error del servidor al consultar disponibilidad' });
    }
});

app.get('/api/reservas', async (req, res) => {
    try {
        const { idUsuario } = req.query;
        let reservas;
        if (idUsuario) {
            reservas = await reservaModel.obtenerReservasPorUsuario(idUsuario);
        } else {
            reservas = await reservaModel.obtenerReservas();
        }
        res.json(reservas);
    } catch (error) {
        console.error('Error al obtener reservas:', error);
        res.status(500).json({ error: 'Error del servidor al obtener reservas' });
    }
});

app.post('/api/reservas', reservaController.crearReserva);
app.get('/api/reservas/:id', reservaController.obtenerReserva);

app.put('/api/reservas/:id', async (req, res) => {
    try {
        const { id } = req.params;
        const { estado } = req.body;

        if (!estado) {
            return res.status(400).json({ error: 'Se requiere el campo estado' });
        }

        const resultado = await reservaModel.confirmarReserva(id, estado);

        if (resultado.affectedRows === 0) {
            return res.status(404).json({ error: 'La reserva especificada no existe' });
        }

        res.json({ mensaje: `Reserva #${id} actualizada a '${estado}' con éxito` });
    } catch (error) {
        console.error('Error al actualizar reserva:', error);
        res.status(500).json({ error: 'Error del servidor al actualizar la reserva' });
    }
});

const PORT = 3003;
app.listen(PORT, '0.0.0.0', () => {
    console.log(`Reservas escuchando en el puerto ${PORT}`);
});
