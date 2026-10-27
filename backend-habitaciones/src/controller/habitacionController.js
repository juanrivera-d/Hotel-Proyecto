const express = require('express');
const router = express.Router();
const ModelHabitacion = require('../model/habitacionModel');

// Obtener todas las habitaciones o filtrar por tipo
router.get('/', async (req, res) => {
    try {
        const { tipo } = req.query;
        const todas = await ModelHabitacion.getAll();

        let habitaciones = todas;
        if (tipo) {
            habitaciones = todas.filter(h => h.tipo.toLowerCase() === tipo.toLowerCase());
        }

        res.json(habitaciones);
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: 'Error al consultar las habitaciones' });
    }
});

// GET: Obtener una habitación por ID (Requerido por Reservas)
router.get('/:id', async (req, res) => {
    try {
        const { id } = req.params;
        const todas = await ModelHabitacion.getAll();
        const habitacion = todas.find(h => Number(h.idHabitacion || h.id) === Number(id));

        if (!habitacion) {
            return res.status(404).json({ error: 'Habitación no encontrada' });
        }

        res.json(habitacion);
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: 'Error al obtener la habitación' });
    }
});

// Actualizar habitación (Por PUT)
router.put('/:id', async (req, res) => {
    try {
        const { id } = req.params;
        await ModelHabitacion.update(id, req.body);
        res.json({ message: 'Habitación y tarifas actualizadas correctamente' });
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: 'Error al actualizar la habitación' });
    }
});

// Eliminar habitación
router.delete('/:id', async (req, res) => {
    try {
        const { id } = req.params;
        await ModelHabitacion.delete(id);
        res.json({ message: 'Habitación eliminada correctamente' });
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: 'Error al eliminar la habitación' });
    }
});

module.exports = router;
