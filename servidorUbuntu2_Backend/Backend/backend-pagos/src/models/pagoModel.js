const mysql = require('mysql2/promise');

const pool = mysql.createPool({
    host: process.env.DB_HOST || '192.168.100.3',
    user: 'root',
    password: 'root',
    database: process.env.DB_NAME || 'bd_pagos',
    waitForConnections: true,
    connectionLimit: 10,
    queueLimit: 0
});

// Obtener pagos (si recibe lista de idReservas, filtra por ellas)
async function obtenerPagosPorReservas(listaIdsReservas) {
    if (!listaIdsReservas || listaIdsReservas.length === 0) return [];
    const placeholders = listaIdsReservas.map(() => '?').join(',');
    const [rows] = await pool.query(
        `SELECT * FROM pago WHERE idReserva IN (${placeholders}) ORDER BY idPago DESC`,
        listaIdsReservas
    );
    return rows;
}

// Obtener todos los pagos (para uso administrativo)
async function obtenerTodosLosPagos() {
    const [rows] = await pool.query('SELECT * FROM pago ORDER BY idPago DESC');
    return rows;
}

// Obtener pago por ID
async function obtenerPagoPorId(idPago) {
    const [rows] = await pool.query('SELECT * FROM pago WHERE idPago = ?', [idPago]);
    return rows[0];
}

// Calcular cuánto dinero se ha abonado a una reserva
async function obtenerTotalAbonado(idReserva) {
    const [rows] = await pool.query(
        "SELECT IFNULL(SUM(monto), 0) AS totalAbonado FROM pago WHERE idReserva = ? AND estado = 'Exitoso'",
        [idReserva]
    );
    return Number(rows[0].totalAbonado);
}

// Registrar un nuevo pago
async function crearPago(monto, metodoPago, idReserva, estado = 'Exitoso') {
    const [result] = await pool.query(
        'INSERT INTO pago (monto, metodoPago, estado, idReserva) VALUES (?, ?, ?, ?)',
        [monto, metodoPago, estado, idReserva]
    );
    return {
        idPago: result.insertId,
        monto,
        metodoPago,
        estado,
        idReserva
    };
}

module.exports = {
    obtenerPagosPorReservas,
    obtenerTodosLosPagos,
    obtenerPagoPorId,
    obtenerTotalAbonado,
    crearPago
};
