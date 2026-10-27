const axios = require('axios');
const reservaModel = require('../models/reservaModel');

const URL_USUARIOS = process.env.URL_USUARIOS || 'http://backend-usuarios:3001/api/usuarios';
const URL_HABITACIONES = process.env.URL_HABITACIONES || 'http://backend-habitaciones:3002/api/habitaciones';
const URL_SERVICIOS = process.env.URL_SERVICIOS || 'http://backend-servicios:3000/api/servicios';

const calcularNoches = (fEntrada, fSalida) => {
    const inicio = new Date(fEntrada);
    const fin = new Date(fSalida);
    const diffTiempo = fin.getTime() - inicio.getTime();
    const noches = Math.ceil(diffTiempo / (1000 * 3600 * 24));
    return noches > 0 ? noches : 1;
};

const crearReserva = async (req, res) => {
    try {
        let { fechaEntrada, fechaSalida, idUsuario, idHabitacion, precioTotal, servicios } = req.body;
        const authHeader = req.headers.authorization;
        const config = authHeader ? { headers: { Authorization: authHeader } } : {};

        // Si el servicio de usuarios falla, la reserva continúa igual
        try {
            await axios.get(`${URL_USUARIOS}/${idUsuario}`, config);
        } catch (errUser) {
            console.warn('No se pudo verificar el usuario:', errUser.message);
        }

        // Se fuerza a número para que las sumas posteriores no concatenen strings
        precioTotal = Number(precioTotal) || 0;

        // Sin precio del cliente, se calcula con el precio por noche de la habitación
        if (precioTotal <= 0) {
            try {
                const resHab = await axios.get(`${URL_HABITACIONES}/${idHabitacion}`, config);
                const habitacion = resHab.data;
                const precioNoche = Number(habitacion.precioNoche || habitacion.precio || 0) || 0;

                const noches = calcularNoches(fechaEntrada, fechaSalida);
                precioTotal = noches * precioNoche;
            } catch (errHab) {
                console.warn('No se pudo obtener el precio de la habitación:', errHab.message);
                precioTotal = 0;
            }
        }

        // Los servicios pueden llegar como ids o como objetos con precioUnitario
        let serviciosDetalle = [];
        if (Array.isArray(servicios) && servicios.length > 0) {
            if (servicios[0] && typeof servicios[0] === 'object' && servicios[0].precioUnitario !== undefined) {
                serviciosDetalle = servicios;
            } else {
                try {
                    const resServ = await axios.get(URL_SERVICIOS, config);
                    const catalogoServicios = resServ.data;

                    serviciosDetalle = servicios.map(id => {
                        const servEncontrado = catalogoServicios.find(s => (s.idServicio || s.id) == id);
                        const precio = servEncontrado ? (Number(servEncontrado.precio || servEncontrado.precioUnitario || 0) || 0) : 0;
                        precioTotal += precio;

                        return {
                            idServicio: id,
                            precioUnitario: precio
                        };
                    });
                } catch (errServ) {
                    console.warn('No se pudo obtener el catálogo de servicios:', errServ.message);
                }
            }
        }

        let result;
        if (serviciosDetalle.length > 0) {
            result = await reservaModel.crearReservaConServicios(
                fechaEntrada,
                fechaSalida,
                precioTotal,
                idUsuario,
                idHabitacion,
                serviciosDetalle
            );
        } else {
            result = await reservaModel.crearReserva(
                fechaEntrada,
                fechaSalida,
                precioTotal,
                idUsuario,
                idHabitacion
            );
        }

        return res.status(201).json({
            mensaje: 'Reserva creada exitosamente',
            idReserva: result ? (result.insertId || result.idReserva) : null,
            precioTotal
        });
    } catch (error) {
        console.error('Error al insertar reserva:', error);
        if (error.codigo === 'CONFLICTO_FECHAS' || (error.message && error.message.includes('ya está reservada'))) {
            return res.status(400).json({ error: error.message });
        }
        return res.status(500).json({ error: 'Error del servidor al insertar la reserva' });
    }
};

const consultarDisponibilidad = async (req, res) => {
    try {
        const { fechaEntrada, fechaSalida } = req.query;
        const authHeader = req.headers.authorization;
        const config = authHeader ? { headers: { Authorization: authHeader } } : {};

        const resHab = await axios.get(URL_HABITACIONES, config);
        const todasHabitaciones = resHab.data;

        const habitaciones = await reservaModel.obtenerDisponibilidad(fechaEntrada, fechaSalida, todasHabitaciones);
        return res.json(habitaciones);
    } catch (error) {
        console.error('Error al consultar disponibilidad:', error);
        return res.status(500).json({ error: 'Error al consultar disponibilidad' });
    }
};

const obtenerReserva = async (req, res) => {
    try {
        const { id } = req.params;
        const reserva = await reservaModel.obtenerReservaPorId(id);
        return res.json(reserva);
    } catch (error) {
        console.error('Error al obtener reserva:', error);
        return res.status(500).json({ error: 'Error al obtener reserva' });
    }
};

const obtenerReservasUsuario = async (req, res) => {
    try {
        const idUsuario = req.params.idUsuario || req.query.idUsuario;

        if (!idUsuario) {
            const todas = await reservaModel.obtenerReservas();
            return res.json(todas);
        }

        const reservas = await reservaModel.obtenerReservasPorUsuario(idUsuario);
        return res.json(reservas);
    } catch (error) {
        console.error('Error al obtener reservas del usuario:', error);
        return res.status(500).json({ error: 'Error al obtener reservas del usuario' });
    }
};

const obtenerTodasLasReservas = async (req, res) => {
    try {
        const reservas = await reservaModel.obtenerReservas();
        return res.json(reservas);
    } catch (error) {
        console.error('Error al obtener todas las reservas:', error);
        return res.status(500).json({ error: 'Error al obtener reservas' });
    }
};

const cancelarReserva = async (req, res) => {
    try {
        const { idReserva } = req.params;
        await reservaModel.cancelarReserva(idReserva);
        return res.json({ mensaje: 'Reserva cancelada con éxito' });
    } catch (error) {
        console.error('Error al cancelar reserva:', error);
        return res.status(500).json({ error: 'Error al cancelar la reserva' });
    }
};

module.exports = {
    crearReserva,
    consultarDisponibilidad,
    obtenerReserva,
    obtenerReservasPorUsuario: obtenerReservasUsuario,
    obtenerTodasLasReservas,
    obtenerReservas: obtenerTodasLasReservas,
    cancelarReserva
};
