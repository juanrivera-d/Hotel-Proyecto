const { Router } = require('express');
const router = Router();
const hotelModel = require('../models/hotelModel');

// RUTA PÚBLICA (Corresponde a /api/servicios)
router.get('/', async (req, res) => {
    try {
        const servicios = await hotelModel.obtenerServicios();
        res.status(200).json(servicios);
    } catch (error) {
        console.error(">>> ERROR MYSQL DETALLADO:", error);
        res.status(500).json({ error: "Error al obtener servicios" });
    }
});

// RUTAS PROTEGIDAS (Corresponden a /api/servicios y /api/servicios/:id)
router.post('/', async (req, res) => {
    try {
        const { nombre, descripcion, precio, estado } = req.body;
        await hotelModel.crearServicio(nombre, descripcion, precio, estado);
        res.status(201).json({ mensaje: "Servicio creado con éxito" });
    } catch (error) {
        res.status(500).json({ error: "Error al crear el servicio" });
    }
});

router.put('/:id', async (req, res) => {
    try {
        const { id } = req.params;
        const { nombre, descripcion, precio, estado } = req.body;
        await hotelModel.actualizarServicio(id, nombre, descripcion, precio, estado);
        res.status(200).json({ mensaje: "Servicio actualizado con éxito" });
    } catch (error) {
        res.status(500).json({ error: "Error al actualizar el servicio" });
    }
});

router.delete('/:id', async (req, res) => {
    try {
        const { id } = req.params;
        await hotelModel.eliminarServicio(id);
        res.status(200).json({ mensaje: "Servicio eliminado con éxito" });
    } catch (error) {
        res.status(500).json({ error: "Error al eliminar el servicio" });
    }
});

module.exports = router;
