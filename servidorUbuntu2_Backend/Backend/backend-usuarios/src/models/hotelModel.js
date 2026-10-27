const mysql = require('mysql2/promise');
const bcrypt = require('bcryptjs');

const pool = mysql.createPool({
    host: process.env.DB_HOST || '192.168.100.3',
    user: 'root',
    password: 'root',
    database: process.env.DB_NAME || 'bd_usuarios',
    waitForConnections: true,
    connectionLimit: 10,
    queueLimit: 0
});

// Obtener todos los usuarios
const listarUsuarios = async () => {
    const [rows] = await pool.query(
        `SELECT idUsuario, documento, nombreCompleto, email, telefono, estado, rol FROM usuario`
    );
    return rows;
};

// Obtener usuario por ID
const obtenerUsuarioPorId = async (idUsuario) => {
    const [rows] = await pool.query(
        `SELECT idUsuario, documento, nombreCompleto, email, telefono, estado, rol FROM usuario WHERE idUsuario = ?`,
        [idUsuario]
    );
    return rows[0];
};

// Obtener usuario por documento
const obtenerUsuarioPorDocumento = async (documento) => {
    const [rows] = await pool.query(
        `SELECT idUsuario, documento, nombreCompleto, email, telefono, estado, rol FROM usuario WHERE documento = ?`,
        [documento]
    );
    return rows[0];
};

// Obtener usuario para login (incluye hash de contraseña)
const obtenerUsuarioParaLogin = async (documento) => {
    const [rows] = await pool.query(
        `SELECT idUsuario, documento, nombreCompleto, email, telefono, password, estado, rol FROM usuario WHERE documento = ?`,
        [documento]
    );
    return rows[0];
};

// Actualizar usuario
const actualizarUsuario = async (idUsuario, usuario) => {
    const { documento, nombreCompleto, email, telefono, password, estado, rol } = usuario;

    if (password && password.trim() !== "") {
        const [resultado] = await pool.query(
            `UPDATE usuario SET documento = ?, nombreCompleto = ?, email = ?, telefono = ?, password = ?, estado = ?, rol = ? WHERE idUsuario = ?`,
            [documento, nombreCompleto, email, telefono, await bcrypt.hash(password, 10), estado, rol, idUsuario]
        );
        return resultado;
    } else {
        const [resultado] = await pool.query(
            `UPDATE usuario SET documento = ?, nombreCompleto = ?, email = ?, telefono = ?, estado = ?, rol = ? WHERE idUsuario = ?`,
            [documento, nombreCompleto, email, telefono, estado, rol, idUsuario]
        );
        return resultado;
    }
};

// Actualizar perfil
const actualizarPerfil = async (idUsuario, usuario) => {
    const { documento, nombreCompleto, email, telefono, passwordActual, passwordNueva } = usuario;

    const [usuarios] = await pool.query(`SELECT password FROM usuario WHERE idUsuario = ?`, [idUsuario]);
    if (usuarios.length === 0) return { error: 'Usuario no encontrado' };

    const passwordCorrecta = await bcrypt.compare(passwordActual, usuarios[0].password);
    if (!passwordCorrecta) return { error: 'Contraseña actual incorrecta' };

    if (passwordNueva && passwordNueva.trim() !== "") {
        const passwordHash = await bcrypt.hash(passwordNueva, 10);
        const [resultado] = await pool.query(
            `UPDATE usuario SET documento = ?, nombreCompleto = ?, email = ?, telefono = ?, password = ? WHERE idUsuario = ?`,
            [documento, nombreCompleto, email, telefono, passwordHash, idUsuario]
        );
        return resultado;
    } else {
        const [resultado] = await pool.query(
            `UPDATE usuario SET documento = ?, nombreCompleto = ?, email = ?, telefono = ? WHERE idUsuario = ?`,
            [documento, nombreCompleto, email, telefono, idUsuario]
        );
        return resultado;
    }
};

// Crear usuario
const crearUsuario = async (usuario) => {
    const { documento, nombreCompleto, email, telefono, password } = usuario;
    const passwordHash = await bcrypt.hash(password, 10);

    const [result] = await pool.query(
        `INSERT INTO usuario (documento, nombreCompleto, email, telefono, password, estado, rol) VALUES (?, ?, ?, ?, ?, 'Activo', 'Cliente')`,
        [documento, nombreCompleto, email, telefono, passwordHash]
    );
    return result;
};

module.exports = {
    listarUsuarios,
    obtenerUsuarioPorId,
    obtenerUsuarioPorDocumento,
    obtenerUsuarioParaLogin,
    crearUsuario,
    actualizarUsuario,
    actualizarPerfil
};
