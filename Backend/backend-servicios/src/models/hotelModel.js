const mysql = require('mysql2/promise');

const connection = mysql.createPool({
    host: process.env.DB_HOST || '192.168.100.3',
    user: 'root',
    port: 3306,
    password: 'root',
    database: process.env.DB_NAME || 'bd_servicios'
});

async function obtenerServicios() {
    const query = 'SELECT * FROM servicio';
    const result = await connection.query(query);
    return result[0];
}

// Recibe 4 parámetros según el router.post
async function crearServicio(nombre, descripcion, precio, estado) {
    const query = `
        INSERT INTO servicio (nombre, descripcion, precio, estado)
        VALUES (?, ?, ?, ?)
    `;
    const result = await connection.query(query, [nombre, descripcion, precio, estado || 'Disponible']);
    return result[0];
}

// Función requerida por el router.put
async function actualizarServicio(id, nombre, descripcion, precio, estado) {
    const query = `
        UPDATE servicio 
        SET nombre = ?, descripcion = ?, precio = ?, estado = ?
        WHERE idServicio = ?
    `;
    const result = await connection.query(query, [nombre, descripcion, precio, estado, id]);
    return result[0];
}

async function eliminarServicio(idServicio) {
    const query = 'DELETE FROM servicio WHERE idServicio = ?';
    const result = await connection.query(query, [idServicio]);
    return result[0];
}

module.exports = {
    obtenerServicios,
    crearServicio,
    actualizarServicio,
    eliminarServicio
};
