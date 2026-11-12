
/* ==========================================
   HOTEL LEYTON - DASHBOARD ANALÍTICO
   Rol 4: Frontend & Dashboard
   ========================================== */

const API_BASE = "http://192.168.100.3:5080";

const ENDPOINTS = {
  logs: "/api/analytics/trafico-logs",
  sentimiento: "/api/analytics/sentimiento-resenas",
  ocupacion: "/api/analytics/ocupacion-mensual"
};

const COLORES = {
  navy: "#182530",
  gold: "#b68a35",
  goldLight: "rgba(182, 138, 53, 0.16)",
  red: "#e63946",
  green: "#168653",
  gray: "#6d747b"
};

const graficos = {
  logs: null,
  sentimiento: null,
  ocupacion: null
};

const formatoNumero = new Intl.NumberFormat("es-CO");

// ==========================================
// 1. CONTROL DE ACCESO
// ==========================================

function verificarSesion() {
  const token = localStorage.getItem("token");

  let usuario = {};

  try {
    usuario = JSON.parse(
      localStorage.getItem("usuario") || "{}"
    );
  } catch (error) {
    console.error("Sesión inválida:", error);
    window.location.replace("login.html");
    return false;
  }

  if (!token || !usuario.documento) {
    window.location.replace("login.html");
    return false;
  }

  const rol = String(usuario.rol || "").toLowerCase();

  if (!["admin", "administrador"].includes(rol)) {
    window.location.replace("index.html");
    return false;
  }

  return true;
}

// ==========================================
// 2. ESTADO DE CONEXIÓN
// ==========================================

function mostrarEstado(mensaje, tipo = "info") {
  const elemento = document.getElementById(
    "estado-conexion"
  );

  elemento.className = `alert alert-${tipo}`;
  elemento.textContent = mensaje;
}

// ==========================================
// 3. CONSUMIR API REST
// ==========================================

async function consultarAPI(endpoint) {
  const token = localStorage.getItem("token");

  const respuesta = await fetch(
    `${API_BASE}${endpoint}`,
    {
      method: "GET",
      headers: {
        Accept: "application/json",
        Authorization: `Bearer ${token}`
      }
    }
  );

  if (!respuesta.ok) {
    throw new Error(
      `${endpoint}: HTTP ${respuesta.status}`
    );
  }

  const resultado = await respuesta.json();

  if (!Array.isArray(resultado.datos)) {
    throw new Error(
      `${endpoint}: respuesta sin arreglo "datos"`
    );
  }

  return resultado.datos;
}

// ==========================================
// 4. FUNCIONES AUXILIARES
// ==========================================

function numero(valor) {
  const resultado = Number(valor);
  return Number.isFinite(resultado) ? resultado : 0;
}

function sumar(datos, campo) {
  return datos.reduce(
    (total, fila) => total + numero(fila[campo]),
    0
  );
}

function actualizarKPI(id, valor) {
  document.getElementById(id).textContent = valor;
}

function destruirGrafico(nombre) {
  if (graficos[nombre]) {
    graficos[nombre].destroy();
    graficos[nombre] = null;
  }
}

function limpiarVisualizacion(nombre, idKPI) {
  destruirGrafico(nombre);
  actualizarKPI(idKPI, "--");
}

function opcionesBase() {
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: "bottom",
        labels: {
          usePointStyle: true,
          padding: 18,
          color: COLORES.navy
        }
      }
    }
  };
}

// ==========================================
// 5. GRÁFICO DE TRÁFICO DE LOGS
// ==========================================

function renderizarLogs(datos) {
  destruirGrafico("logs");

  // El KPI incluye todos los eventos procesados.
  const totalEventos = sumar(
    datos,
    "total_interacciones"
  );

  actualizarKPI(
    "kpi-logs",
    formatoNumero.format(totalEventos)
  );

  if (datos.length === 0) return;

  // Seleccionar los 10 endpoints con más interacciones.
  const principales = [...datos]
    .sort(
      (a, b) =>
        numero(b.total_interacciones) -
        numero(a.total_interacciones)
    )
    .slice(0, 10);

  const etiquetas = principales.map(
    fila => fila.endpoint_consultado
  );

  const interacciones = principales.map(
    fila => numero(fila.total_interacciones)
  );

  const errores = principales.map(
    fila => numero(fila.errores_detectados)
  );

  const contexto = document.getElementById(
    "grafico-logs"
  );

  graficos.logs = new Chart(contexto, {
    type: "bar",
    data: {
      labels: etiquetas,
      datasets: [
        {
          label: "Interacciones",
          data: interacciones,
          backgroundColor: COLORES.gold,
          borderRadius: 6
        },
        {
          label: "Errores detectados",
          data: errores,
          backgroundColor: COLORES.red,
          borderRadius: 6
        }
      ]
    },
    options: {
      ...opcionesBase(),
      indexAxis: "y",
      scales: {
        x: {
          beginAtZero: true,
          ticks: {
            precision: 0
          }
        },
        y: {
          ticks: {
            autoSkip: false
          }
        }
      }
    }
  });
}

// ==========================================
// 6. GRÁFICO DE SENTIMIENTO
// ==========================================

function renderizarSentimiento(datos) {
  destruirGrafico("sentimiento");

  const positivas = sumar(
    datos,
    "total_positivas"
  );

  const negativas = sumar(
    datos,
    "total_negativas"
  );

  const total = positivas + negativas;

  actualizarKPI(
    "kpi-resenas",
    formatoNumero.format(total)
  );

  if (datos.length === 0 || total === 0) return;

  const contexto = document.getElementById(
    "grafico-sentimiento"
  );

  graficos.sentimiento = new Chart(contexto, {
    type: "doughnut",
    data: {
      labels: [
        "Reseñas positivas",
        "Reseñas negativas"
      ],
      datasets: [
        {
          data: [positivas, negativas],
          backgroundColor: [
            COLORES.green,
            COLORES.red
          ],
          borderWidth: 3,
          borderColor: "#ffffff",
          hoverOffset: 8
        }
      ]
    },
    options: {
      ...opcionesBase(),
      cutout: "68%"
    }
  });
}

// ==========================================
// 7. GRÁFICO DE OCUPACIÓN MENSUAL
// ==========================================

function renderizarOcupacion(datos) {
  destruirGrafico("ocupacion");

  if (datos.length === 0) {
    actualizarKPI("kpi-ocupacion", "--");
    return;
  }

  const ordenados = [...datos].sort(
    (a, b) =>
      numero(a.anio) - numero(b.anio) ||
      numero(a.mes) - numero(b.mes)
  );

  const promedio = ordenados.reduce(
    (total, fila) =>
      total + numero(fila.porcentaje_ocupacion),
    0
  ) / ordenados.length;

  actualizarKPI(
    "kpi-ocupacion",
    `${promedio.toFixed(1)} %`
  );

  const etiquetas = ordenados.map(fila => {
    const mes = String(fila.mes).padStart(2, "0");
    return `${mes}/${fila.anio}`;
  });

  const porcentajes = ordenados.map(
    fila => numero(fila.porcentaje_ocupacion)
  );

  const contexto = document.getElementById(
    "grafico-ocupacion"
  );

  graficos.ocupacion = new Chart(contexto, {
    type: "line",
    data: {
      labels: etiquetas,
      datasets: [
        {
          label: "Ocupación (%)",
          data: porcentajes,
          borderColor: COLORES.gold,
          backgroundColor: COLORES.goldLight,
          fill: true,
          tension: 0.3,
          pointRadius: 5,
          pointHoverRadius: 7,
          pointBackgroundColor: COLORES.gold
        }
      ]
    },
    options: {
      ...opcionesBase(),
      scales: {
        y: {
          beginAtZero: true,
          max: 100,
          ticks: {
            callback: valor => `${valor}%`
          }
        }
      }
    }
  });
}

// ==========================================
// 8. CARGAR DASHBOARD
// ==========================================

async function cargarDashboard() {
  const boton = document.getElementById(
    "btn-actualizar"
  );

  boton.disabled = true;
  boton.textContent = "Actualizando...";

  mostrarEstado(
    "Consultando datos analíticos...",
    "info"
  );

  const configuraciones = [
    {
      nombre: "logs",
      endpoint: ENDPOINTS.logs,
      renderizar: renderizarLogs,
      kpi: "kpi-logs"
    },
    {
      nombre: "sentimiento",
      endpoint: ENDPOINTS.sentimiento,
      renderizar: renderizarSentimiento,
      kpi: "kpi-resenas"
    },
    {
      nombre: "ocupacion",
      endpoint: ENDPOINTS.ocupacion,
      renderizar: renderizarOcupacion,
      kpi: "kpi-ocupacion"
    }
  ];

  try {
    const resultados = await Promise.allSettled(
      configuraciones.map(config =>
        consultarAPI(config.endpoint)
      )
    );

    let exitosos = 0;
    let conDatos = 0;

    resultados.forEach((resultado, indice) => {
      const config = configuraciones[indice];

      if (resultado.status === "fulfilled") {
        try {
          config.renderizar(resultado.value);
          exitosos++;

          if (resultado.value.length > 0) {
            conDatos++;
          }

          console.log(
            `${config.nombre}:`,
            resultado.value
          );
        } catch (error) {
          console.error(
            `Error al graficar ${config.nombre}:`,
            error
          );
          limpiarVisualizacion(
            config.nombre,
            config.kpi
          );
        }
      } else {
        console.error(
          `Error en ${config.nombre}:`,
          resultado.reason
        );

        limpiarVisualizacion(
          config.nombre,
          config.kpi
        );
      }
    });

    if (exitosos === 3 && conDatos === 3) {
      mostrarEstado(
        "Datos analíticos cargados correctamente.",
        "success"
      );
    } else if (exitosos === 3 && conDatos === 0) {
      mostrarEstado(
        "Conexión exitosa. Las tablas analíticas todavía no contienen registros.",
        "warning"
      );
    } else if (exitosos === 3) {
      mostrarEstado(
        `Conexión exitosa. ${conDatos} de 3 conjuntos contienen datos.`,
        "warning"
      );
    } else if (exitosos > 0) {
      mostrarEstado(
        `Conexión parcial: ${exitosos} de 3 consultas completadas.`,
        "warning"
      );
    } else {
      mostrarEstado(
        "No se pudieron cargar los datos analíticos.",
        "danger"
      );
    }
  } finally {
    boton.disabled = false;
    boton.textContent = "Actualizar datos";
  }
}

// ==========================================
// 9. INICIALIZACIÓN
// ==========================================

const MODO_DESARROLLO = false;
document.addEventListener("DOMContentLoaded", () => {
  if (!MODO_DESARROLLO && !verificarSesion()) return;

  if (typeof Chart === "undefined") {
    mostrarEstado(
      "No se pudo cargar Chart.js. Verifica tu conexión a Internet.",
      "danger"
    );
    return;
  }

  document.getElementById(
    "btn-actualizar"
  ).addEventListener("click", cargarDashboard);

  cargarDashboard();
});
