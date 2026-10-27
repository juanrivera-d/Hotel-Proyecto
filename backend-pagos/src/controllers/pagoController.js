const express = require('express');
const router = express.Router();
const axios = require('axios');
const URL_RESERVAS = process.env.URL_RESERVAS || 'http://backend-reservas:3003';
const pagoModel = require('../models/pagoModel');

router.get('/', async (req, res) => {
    try {
        const { idUsuario } = req.query;

        if (idUsuario) {
            const tokenHeader = req.headers['authorization'];
            const resReservas = await axios.get(`${URL_RESERVAS}/api/reservas?idUsuario=${idUsuario}`, {
                headers: { 'Authorization': tokenHeader }
            });

            const reservasUsuario = resReservas.data;
            if (!Array.isArray(reservasUsuario) || reservasUsuario.length === 0) {
                return res.json([]);
            }

            const idsReservas = reservasUsuario.map(r => r.idReserva);
            const pagos = await pagoModel.obtenerPagosPorReservas(idsReservas);
            return res.json(pagos);
        }

        const pagos = await pagoModel.obtenerTodosLosPagos();
        res.json(pagos);
    } catch (error) {
        console.error("Error al obtener pagos:", error.message);
        res.status(500).json({ error: "Error al consultar los pagos." });
    }
});

router.get('/:id', async (req, res) => {
    try {
        const { id } = req.params;
        const pago = await pagoModel.obtenerPagoPorId(id);
        if (!pago) {
            return res.status(404).json({ error: "No se encontró ningún pago con ese ID." });
        }
        res.json(pago);
    } catch (error) {
        console.error("Error al obtener pago por ID:", error);
        res.status(500).json({ error: "Error al consultar la base de datos." });
    }
});

router.post('/', async (req, res) => {
    const { monto, metodoPago, idReserva } = req.body;

    if (!monto || Number(monto) <= 0 || !idReserva) {
        return res.status(400).json({ error: "El monto y el idReserva son obligatorios." });
    }

    try {
        let datosReserva;
        try {
            const respuestaReserva = await axios.get(`${URL_RESERVAS}/api/reservas/${idReserva}`);
            datosReserva = respuestaReserva.data;
        } catch (errorAxios) {
            return res.status(404).json({ error: `La reserva #${idReserva} no existe o no se pudo consultar.` });
        }

        const precioTotal = Number(datosReserva.precioTotal);
        const abonadoPrevio = await pagoModel.obtenerTotalAbonado(idReserva);
        const saldoPendiente = precioTotal - abonadoPrevio;

        if (saldoPendiente <= 0) {
            return res.status(400).json({ error: `La reserva #${idReserva} ya está totalmente pagada.` });
        }

        if (Number(monto) > saldoPendiente) {
            return res.status(400).json({ error: `El monto ($${monto}) excede el saldo pendiente ($${saldoPendiente}).` });
        }

        const nuevoPago = await pagoModel.crearPago(monto, metodoPago, idReserva);
        const nuevoTotalAbonado = abonadoPrevio + Number(monto);
        
        let estadoNuevoReserva = 'Pendiente';
        if (nuevoTotalAbonado >= precioTotal) {
            estadoNuevoReserva = 'Confirmada';
        } else if (nuevoTotalAbonado > 0) {
            estadoNuevoReserva = 'Abonada'; // Cambiado a Abonada formalmente
        }

        try {
            const tokenHeader = req.headers['authorization'];
            await axios.put(`${URL_RESERVAS}/api/reservas/${idReserva}`,
                { estado: estadoNuevoReserva },
                { headers: { 'Authorization': tokenHeader } }
            );
        } catch (errPut) {
            console.warn("No se pudo actualizar el estado de la reserva:", errPut.message);
        }

        const reservaConfirmada = (estadoNuevoReserva === 'Confirmada');

        res.status(201).json({
            mensaje: reservaConfirmada
                ? "¡Pago completado! Su reserva ha sido Confirmada."
                : "¡Abono registrado con éxito! Su reserva ahora está Abonada.",
            pago: nuevoPago,
            resumenFinanciero: {
                precioTotal,
                abonadoPrevio,
                abonoActual: Number(monto),
                nuevoSaldoPendiente: precioTotal - nuevoTotalAbonado,
                estadoReserva: estadoNuevoReserva
            }
        });

    } catch (error) {
        console.error("Error al procesar el pago:", error.message);
        res.status(500).json({ error: "Error interno al procesar el pago." });
    }
});

router.put('/:id', async (req, res) => {
    try {
        const { id } = req.params;
        const { metodoPago, estado } = req.body;

        const pool = require('mysql2/promise').createPool({
            host: 'localhost', user: 'root', password: 'root', database: 'bd_pagos'
        });

        await pool.query('UPDATE pago SET metodoPago = ?, estado = ? WHERE idPago = ?', [metodoPago, estado, id]);
        res.json({ mensaje: "Pago actualizado con éxito" });
    } catch (error) {
        console.error("Error al actualizar pago:", error);
        res.status(500).json({ error: "Error al actualizar el pago" });
    }
});

router.delete('/:id', async (req, res) => {
    try {
        const { id } = req.params;
        const pool = require('mysql2/promise').createPool({
            host: 'localhost', user: 'root', password: 'root', database: 'bd_pagos'
        });

        await pool.query('DELETE FROM pago WHERE idPago = ?', [id]);
        res.json({ mensaje: "Pago eliminado con éxito" });
    } catch (error) {
        console.error("Error al eliminar pago:", error);
        res.status(500).json({ error: "Error al eliminar el pago" });
    }
});

module.exports = router;
