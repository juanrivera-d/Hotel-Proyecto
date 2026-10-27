const mysql = require('mysql2/promise');

const connection = mysql.createPool({
    host: process.env.DB_HOST || '192.168.100.3',
    port: 3306,
    user: 'root',
    password: 'root',
    database: process.env.DB_NAME || 'db_habitacion'
});

const Habitacion = {
  getAll: async () => {
    const [rows] = await connection.query('SELECT * FROM habitacion');
    return rows;
  },

  update: async (id, data) => {
    const [rows] = await connection.query('SELECT * FROM habitacion WHERE idHabitacion = ?', [id]);
    if (rows.length === 0) throw new Error('Habitación no encontrada');
    const actual = rows[0];

    const numeroHabitacion = data.numeroHabitacion !== undefined ? data.numeroHabitacion : actual.numeroHabitacion;
    const tipo = data.tipo !== undefined ? data.tipo : actual.tipo;
    const capacidad = data.capacidad !== undefined ? data.capacidad : actual.capacidad;
    const precioNoche = data.precioNoche !== undefined ? data.precioNoche : actual.precioNoche;
    const descripcion = data.descripcion !== undefined ? data.descripcion : actual.descripcion;

    const query = `
      UPDATE habitacion 
      SET numeroHabitacion = ?, tipo = ?, capacidad = ?, precioNoche = ?, descripcion = ? 
      WHERE idHabitacion = ?
    `;
    const [result] = await connection.execute(query, [numeroHabitacion, tipo, capacidad, precioNoche, descripcion, id]);
    return result;
  },

  delete: async (id) => {
    const [result] = await connection.execute('DELETE FROM habitacion WHERE idHabitacion = ?', [id]);
    return result;
  }
};

module.exports = Habitacion;
