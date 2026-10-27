const hotelModel = require('../models/hotelModel');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');

const SECRET_KEY = 'CLAVE_SECRETA_LEYTON';

// LISTAR USUARIOS
const listarUsuarios = async (req, res) => {
    try {
        const usuarios = await hotelModel.listarUsuarios();
        res.status(200).json({ mensaje: 'Usuarios obtenidos correctamente', usuarios });
    } catch (error) {
        console.error(error);
        res.status(500).json({ mensaje: 'Error al listar los usuarios' });
    }
};

// CONSULTAR USUARIO POR ID
const obtenerUsuarioPorId = async (req, res) => {
    try {
        const { id } = req.params;
        const esAdmin = req.usuario.rol && req.usuario.rol.toLowerCase() === 'admin';

        if (!esAdmin && Number(id) !== Number(req.usuario.idUsuario)) {
            return res.status(403).json({ mensaje: 'No tienes permisos para consultar este usuario' });
        }

        const usuario = await hotelModel.obtenerUsuarioPorId(id);
        if (!usuario) return res.status(404).json({ mensaje: 'Usuario no encontrado' });

        res.status(200).json(usuario);
    } catch (error) {
        console.error(error);
        res.status(500).json({ mensaje: 'Error al consultar el usuario' });
    }
};

// CONSULTAR USUARIO POR DOCUMENTO
const obtenerUsuarioPorDocumento = async (req, res) => {
    try {
        const { documento } = req.params;
        const usuarioSolicitante = await hotelModel.obtenerUsuarioPorId(req.usuario.idUsuario);

        if (!usuarioSolicitante) return res.status(404).json({ mensaje: 'Usuario autenticado no encontrado' });

        const esAdmin = req.usuario.rol && req.usuario.rol.toLowerCase() === 'admin';
        if (!esAdmin && documento !== usuarioSolicitante.documento) {
            return res.status(403).json({ mensaje: 'No tienes permisos para consultar este usuario' });
        }

        const usuario = await hotelModel.obtenerUsuarioPorDocumento(documento);
        if (!usuario) return res.status(404).json({ mensaje: 'Usuario no encontrado' });

        res.status(200).json(usuario);
    } catch (error) {
        console.error(error);
        res.status(500).json({ mensaje: 'Error al consultar el usuario' });
    }
};

// ACTUALIZAR USUARIO
const actualizarUsuario = async (req, res) => {
    try {
        const { id } = req.params;
        const usuarioExistente = await hotelModel.obtenerUsuarioPorId(id);

        if (!usuarioExistente) return res.status(404).json({ mensaje: 'Usuario no encontrado' });

        const resultado = await hotelModel.actualizarUsuario(id, req.body);
        if (resultado.affectedRows === 0) return res.status(400).json({ mensaje: 'No se pudo actualizar el usuario' });

        const usuarioActualizado = await hotelModel.obtenerUsuarioPorId(id);
        res.status(200).json({ mensaje: 'Usuario actualizado correctamente', usuario: usuarioActualizado });
    } catch (error) {
        console.error(error);
        res.status(500).json({ mensaje: 'Error al actualizar el usuario' });
    }
};

// CREAR USUARIO (REGISTRO)
const crearUsuario = async (req, res) => {
    try {
        const resultado = await hotelModel.crearUsuario(req.body);
        res.status(201).json({ mensaje: 'Usuario creado correctamente', idUsuario: resultado.insertId });
    } catch (error) {
        console.error(error);
        res.status(500).json({ mensaje: 'Error al crear el usuario' });
    }
};

// INICIAR SESIÓN (LOGIN)
const iniciarSesion = async (req, res) => {
    try {
        const { documento, password } = req.body;

        if (!documento || !password) {
            return res.status(400).json({ mensaje: 'Documento y contraseña son obligatorios' });
        }

        const usuario = await hotelModel.obtenerUsuarioParaLogin(documento);
        if (!usuario) {
            return res.status(401).json({ mensaje: 'Documento o contraseña incorrectos' });
        }

        if (usuario.estado !== 'Activo') {
            return res.status(403).json({ mensaje: 'El usuario se encuentra inactivo' });
        }

        const passwordCorrecta = await bcrypt.compare(password, usuario.password);
        if (!passwordCorrecta) {
            return res.status(401).json({ mensaje: 'Documento o contraseña incorrectos' });
        }

        // Generar Token JWT con la clave compartida
        const token = jwt.sign(
            { idUsuario: usuario.idUsuario, rol: usuario.rol, nombre: usuario.nombreCompleto },
            SECRET_KEY,
            { expiresIn: '24h' }
        );

        res.status(200).json({
            mensaje: 'Inicio de sesión exitoso',
            token,
            usuario: {
                idUsuario: usuario.idUsuario,
                documento: usuario.documento,
                nombre: usuario.nombreCompleto,
                nombreCompleto: usuario.nombreCompleto,
                email: usuario.email,
                correo: usuario.email,
                telefono: usuario.telefono,
                estado: usuario.estado,
                rol: usuario.rol
            }
        });
    } catch (error) {
        console.error(error);
        res.status(500).json({ mensaje: 'Error al iniciar sesión' });
    }
};

// ACTUALIZAR PERFIL
const actualizarMiPerfil = async (req, res) => {
    try {
        const idUsuario = req.usuario.idUsuario;
        const usuarioExistente = await hotelModel.obtenerUsuarioPorId(idUsuario);

        if (!usuarioExistente) return res.status(404).json({ mensaje: 'Usuario no encontrado' });

        const resultado = await hotelModel.actualizarPerfil(idUsuario, req.body);
        if (resultado.error) return res.status(401).json({ mensaje: resultado.error });

        const usuarioActualizado = await hotelModel.obtenerUsuarioPorId(idUsuario);
        res.status(200).json({ mensaje: 'Perfil actualizado correctamente', usuario: usuarioActualizado });
    } catch (error) {
        console.error(error);
        res.status(500).json({ mensaje: 'Error al actualizar el perfil' });
    }
};

module.exports = {
    listarUsuarios,
    obtenerUsuarioPorId,
    obtenerUsuarioPorDocumento,
    crearUsuario,
    actualizarUsuario,
    iniciarSesion,
    actualizarMiPerfil
};
