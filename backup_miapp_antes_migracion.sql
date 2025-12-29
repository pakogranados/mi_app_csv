-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Servidor: 127.0.0.1
-- Tiempo de generaci贸n: 29-12-2025 a las 08:18:38
-- Versi贸n del servidor: 10.4.32-MariaDB
-- Versi贸n de PHP: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de datos: `miapp`
--

DELIMITER $$
--
-- Procedimientos
--
CREATE DEFINER=`root`@`localhost` PROCEDURE `sp_crear_areas_predefinidas`(IN p_empresa_id INT)
BEGIN
    
    IF NOT EXISTS (SELECT 1 FROM areas_sistema WHERE empresa_id = p_empresa_id) THEN
        
        INSERT INTO areas_sistema (empresa_id, codigo, nombre, descripcion, modulo_relacionado, icono, color, orden) VALUES
        
        (p_empresa_id, 'VENTAS', 'Ventas / Punto de Venta', 'Gesti de ventas, caja y atenci al cliente', 'ventas', 'fas fa-cash-register', '#28a745', 1),
        (p_empresa_id, 'INVENTARIO', 'Almac俷 / Inventario', 'Control de mercanc, entradas, salidas y existencias', 'inventario', 'fas fa-boxes', '#ffc107', 2),
        (p_empresa_id, 'COMPRAS', 'Compras', '鄏denes de compra y relaci con proveedores', 'compras', 'fas fa-shopping-cart', '#17a2b8', 3),
        
        
        (p_empresa_id, 'CAJA', 'Caja y Tesorer', 'Manejo de efectivo, cortes y flujo de caja', 'caja', 'fas fa-money-bill-wave', '#20c997', 4),
        (p_empresa_id, 'CXC', 'Cuentas por Cobrar', 'Cartera de clientes y cobranza', 'cxc', 'fas fa-hand-holding-usd', '#28a745', 5),
        (p_empresa_id, 'CXP', 'Cuentas por Pagar', 'Deudas con proveedores y programaci de pagos', 'cxp', 'fas fa-file-invoice-dollar', '#dc3545', 6),
        (p_empresa_id, 'CONTABILIDAD', 'Contabilidad', 'Registros contables, pizas y estados financieros', 'contabilidad', 'fas fa-calculator', '#6f42c1', 7),
        
        
        (p_empresa_id, 'RRHH', 'Recursos Humanos', 'Gesti de personal, nina y prestaciones', 'nomina', 'fas fa-users', '#e83e8c', 8),
        (p_empresa_id, 'GASTOS', 'Control de Gastos', 'Registro y autorizaci de gastos operativos', 'gastos', 'fas fa-receipt', '#fd7e14', 9),
        
        
        (p_empresa_id, 'B2B_CLIENTE', 'B2B Como Cliente', '鄏denes de compra y recepci de mercanc B2B', 'b2b', 'fas fa-building', '#007bff', 10),
        (p_empresa_id, 'B2B_PROVEEDOR', 'B2B Como Proveedor', 'Pedidos, facturaci y entregas B2B', 'b2b', 'fas fa-industry', '#6610f2', 11),
        (p_empresa_id, 'REPARTO', 'Logtica y Reparto', 'Entregas, rutas y distribuci', 'reparto', 'fas fa-truck', '#795548', 12),
        
        
        (p_empresa_id, 'ADMINISTRACION', 'Administraci General', 'Supervisi general y toma de decisiones', 'admin', 'fas fa-cogs', '#343a40', 13),
        (p_empresa_id, 'REPORTES', 'Reportes y An爈isis', 'Generaci de reportes y an爈isis de datos', 'reportes', 'fas fa-chart-bar', '#17a2b8', 14),
        (p_empresa_id, 'AUDITORIA', 'Auditor', 'Revisi de operaciones y cumplimiento', 'auditoria', 'fas fa-search', '#6c757d', 15);
        
    END IF;
END$$

DELIMITER ;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `alertas_b2b`
--

CREATE TABLE `alertas_b2b` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `usuario_id` int(11) DEFAULT NULL,
  `rol_destino` varchar(50) NOT NULL,
  `tipo` varchar(50) NOT NULL,
  `referencia_tipo` varchar(50) DEFAULT NULL,
  `referencia_id` int(11) DEFAULT NULL,
  `titulo` varchar(200) NOT NULL,
  `mensaje` text DEFAULT NULL,
  `leida` tinyint(1) DEFAULT 0,
  `activa` tinyint(1) DEFAULT 1,
  `fecha_creacion` datetime DEFAULT current_timestamp(),
  `fecha_lectura` datetime DEFAULT NULL,
  `fecha_cierre` datetime DEFAULT NULL,
  `whatsapp_enviado` tinyint(1) DEFAULT 0,
  `whatsapp_fecha` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `areas_produccion`
--

CREATE TABLE `areas_produccion` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `descripcion` text DEFAULT NULL,
  `activo` tinyint(1) DEFAULT 1,
  `fecha_creacion` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `areas_produccion`
--

INSERT INTO `areas_produccion` (`id`, `empresa_id`, `nombre`, `descripcion`, `activo`, `fecha_creacion`) VALUES
(11, 1, 'Produccion', 'Area de manufactura y ensamble', 1, '2025-12-19 20:02:46'),
(12, 1, 'Almacen', 'Control de inventarios y materias primas', 1, '2025-12-19 20:02:46'),
(13, 1, 'Ventas', 'Gestion de ventas y facturacion', 1, '2025-12-19 20:02:46'),
(14, 1, 'Compras', 'Adquisicion de materiales y proveedores', 1, '2025-12-19 20:02:46'),
(15, 1, 'Calidad', 'Control de calidad y certificaciones', 1, '2025-12-19 20:02:46');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `areas_sistema`
--

CREATE TABLE `areas_sistema` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) DEFAULT NULL,
  `codigo` varchar(50) DEFAULT NULL,
  `nombre` varchar(100) NOT NULL,
  `descripcion` text DEFAULT NULL,
  `activo` tinyint(1) DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `modulo_relacionado` varchar(50) DEFAULT NULL,
  `icono` varchar(50) DEFAULT 'fas fa-folder',
  `color` varchar(20) DEFAULT '#6c757d',
  `requiere_supervisor` tinyint(1) DEFAULT 1,
  `orden` int(11) DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `areas_sistema`
--

INSERT INTO `areas_sistema` (`id`, `empresa_id`, `codigo`, `nombre`, `descripcion`, `activo`, `created_at`, `modulo_relacionado`, `icono`, `color`, `requiere_supervisor`, `orden`) VALUES
(1, 1, 'VENTAS', 'Ventas / Punto de Venta', 'Gesti贸n de ventas, caja y atenci贸n al cliente', 1, '2025-12-11 17:39:09', 'ventas', 'fas fa-cash-register', '#28a745', 1, 1),
(2, 1, 'INVENTARIO', 'Almac茅n / Inventario', 'Control de mercanc铆a, entradas, salidas y existencias', 1, '2025-12-11 17:39:09', 'inventario', 'fas fa-boxes', '#ffc107', 1, 2),
(3, 1, 'COMPRAS', 'Compras', '脫rdenes de compra y relaci贸n con proveedores', 1, '2025-12-11 17:39:09', 'compras', 'fas fa-shopping-cart', '#17a2b8', 1, 3),
(4, 1, 'CAJA', 'Caja y Tesorer铆a', 'Manejo de efectivo, cortes y flujo de caja', 1, '2025-12-11 17:39:09', 'caja', 'fas fa-money-bill-wave', '#20c997', 1, 4),
(5, 1, 'CXC', 'Cuentas por Cobrar', 'Cartera de clientes y cobranza', 1, '2025-12-11 17:39:09', 'cxc', 'fas fa-hand-holding-usd', '#28a745', 1, 5),
(6, 1, 'CXP', 'Cuentas por Pagar', 'Deudas con proveedores y programaci贸n de pagos', 1, '2025-12-11 17:39:09', 'cxp', 'fas fa-file-invoice-dollar', '#dc3545', 1, 6),
(7, 1, 'CONTABILIDAD', 'Contabilidad', 'Registros contables, p贸lizas y estados financieros', 1, '2025-12-11 17:39:09', 'contabilidad', 'fas fa-calculator', '#6f42c1', 1, 7),
(8, 1, 'RRHH', 'Recursos Humanos', 'Gesti贸n de personal, n贸mina y prestaciones', 1, '2025-12-11 17:39:09', 'nomina', 'fas fa-users', '#e83e8c', 1, 8),
(9, 1, 'GASTOS', 'Control de Gastos', 'Registro y autorizaci贸n de gastos operativos', 1, '2025-12-11 17:39:09', 'gastos', 'fas fa-receipt', '#fd7e14', 1, 9),
(10, 1, 'B2B_CLIENTE', 'B2B Como Cliente', '脫rdenes de compra y recepci贸n de mercanc铆a B2B', 1, '2025-12-11 17:39:09', 'b2b', 'fas fa-building', '#007bff', 1, 10),
(11, 1, 'B2B_PROVEEDOR', 'B2B Como Proveedor', 'Pedidos, facturaci贸n y entregas B2B', 1, '2025-12-11 17:39:09', 'b2b', 'fas fa-industry', '#6610f2', 1, 11),
(12, 1, 'REPARTO', 'Log铆stica y Reparto', 'Entregas, rutas y distribuci贸n', 1, '2025-12-11 17:39:09', 'reparto', 'fas fa-truck', '#795548', 1, 12),
(13, 1, 'ADMINISTRACION', 'Administraci贸n General', 'Supervisi贸n general y toma de decisiones', 1, '2025-12-11 17:39:09', 'admin', 'fas fa-cogs', '#343a40', 1, 13),
(14, 1, 'REPORTES', 'Reportes y An谩lisis', 'Generaci贸n de reportes y an谩lisis de datos', 1, '2025-12-11 17:39:09', 'reportes', 'fas fa-chart-bar', '#17a2b8', 1, 14),
(15, 1, 'AUDITORIA', 'Auditor铆a', 'Revisi贸n de operaciones y cumplimiento', 1, '2025-12-11 17:39:09', 'auditoria', 'fas fa-search', '#6c757d', 1, 15);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `asientos_contables`
--

CREATE TABLE `asientos_contables` (
  `id` int(11) NOT NULL,
  `contratante_id` int(11) NOT NULL,
  `fecha` timestamp NOT NULL DEFAULT current_timestamp(),
  `concepto` varchar(255) NOT NULL,
  `descripcion` varchar(255) DEFAULT NULL,
  `cuenta_debe` int(11) DEFAULT NULL,
  `cuenta_haber` int(11) DEFAULT NULL,
  `monto` decimal(12,2) NOT NULL,
  `producto_id` int(11) DEFAULT NULL,
  `mercancia_id` int(11) DEFAULT NULL,
  `empresa_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `asientos_contables`
--

INSERT INTO `asientos_contables` (`id`, `contratante_id`, `fecha`, `concepto`, `descripcion`, `cuenta_debe`, `cuenta_haber`, `monto`, `producto_id`, `mercancia_id`, `empresa_id`) VALUES
(1, 1, '2025-08-19 16:29:33', '', 'Entrada PT - Producto Terminado Test', NULL, NULL, 1000.00, 3, NULL, NULL),
(3, 1, '2025-08-28 01:29:35', 'Compra 75930', NULL, NULL, NULL, 0.00, NULL, NULL, NULL),
(4, 1, '2025-08-28 01:30:59', 'Compra 45573', NULL, NULL, NULL, 0.00, NULL, NULL, NULL),
(5, 1, '2025-08-28 01:38:33', 'Compra 1708825', NULL, NULL, NULL, 0.00, NULL, NULL, NULL),
(6, 1, '2025-08-28 14:59:24', 'Compra 635', NULL, NULL, NULL, 0.00, NULL, NULL, NULL),
(7, 1, '2025-08-28 15:13:13', 'Compra 51', NULL, NULL, NULL, 0.00, NULL, NULL, NULL),
(8, 1, '2025-08-28 15:14:37', 'Compra 9 14', NULL, NULL, NULL, 0.00, NULL, NULL, NULL),
(9, 1, '2025-08-28 16:04:58', 'Compra 5510', NULL, NULL, NULL, 0.00, NULL, NULL, NULL),
(10, 1, '2025-08-28 16:11:44', 'Compra 15', NULL, NULL, NULL, 0.00, NULL, NULL, NULL),
(11, 1, '2025-08-30 14:48:33', 'Compra 515', NULL, NULL, NULL, 0.00, NULL, NULL, NULL),
(12, 1, '2025-09-01 05:17:35', 'Compra 100103', NULL, NULL, NULL, 0.00, NULL, NULL, NULL),
(13, 1, '2025-09-01 05:18:24', 'Compra 100103', NULL, NULL, NULL, 0.00, NULL, NULL, NULL),
(14, 1, '2025-09-01 05:19:50', 'Compra 100103', NULL, NULL, NULL, 0.00, NULL, NULL, NULL),
(15, 1, '2025-09-01 06:14:50', 'Compra 100103', NULL, NULL, NULL, 0.00, NULL, NULL, NULL),
(16, 1, '2025-09-01 06:25:05', 'Compra 100103', NULL, NULL, NULL, 0.00, NULL, NULL, NULL),
(17, 1, '2025-09-04 02:03:48', 'Compra 5165', NULL, NULL, NULL, 0.00, NULL, NULL, NULL),
(18, 1, '2025-09-04 02:27:04', 'Compra 51', NULL, NULL, NULL, 0.00, NULL, NULL, NULL);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `asientos_detalle`
--

CREATE TABLE `asientos_detalle` (
  `id` int(11) NOT NULL,
  `asiento_id` int(11) NOT NULL,
  `cuenta_id` int(11) NOT NULL,
  `debe` decimal(12,2) DEFAULT 0.00,
  `haber` decimal(12,2) DEFAULT 0.00,
  `empresa_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `asientos_detalle`
--

INSERT INTO `asientos_detalle` (`id`, `asiento_id`, `cuenta_id`, `debe`, `haber`, `empresa_id`) VALUES
(1, 3, 10, 34.00, 0.00, NULL),
(2, 3, 30, 0.00, 34.00, NULL),
(3, 4, 10, 1990.00, 0.00, NULL),
(4, 4, 30, 0.00, 1990.00, NULL),
(5, 5, 10, 379.80, 0.00, NULL),
(6, 5, 30, 0.00, 379.80, NULL),
(7, 6, 10, 212.00, 0.00, NULL),
(8, 6, 30, 0.00, 212.00, NULL),
(9, 7, 10, 212.00, 0.00, NULL),
(10, 7, 30, 0.00, 212.00, NULL),
(11, 8, 10, 212.00, 0.00, NULL),
(12, 8, 30, 0.00, 212.00, NULL),
(13, 9, 10, 51.00, 0.00, NULL),
(14, 9, 30, 0.00, 51.00, NULL),
(15, 10, 10, 212.00, 0.00, NULL),
(16, 10, 30, 0.00, 212.00, NULL),
(17, 11, 10, 0.00, 0.00, NULL),
(18, 11, 30, 0.00, 0.00, NULL),
(19, 12, 10, 384.26, 0.00, NULL),
(20, 12, 30, 0.00, 384.26, NULL),
(21, 13, 10, 584.26, 0.00, NULL),
(22, 13, 30, 0.00, 584.26, NULL),
(23, 14, 10, 615.00, 0.00, NULL),
(24, 14, 30, 0.00, 615.00, NULL),
(25, 15, 10, 615.00, 0.00, NULL),
(26, 15, 30, 0.00, 615.00, NULL),
(27, 16, 10, 615.00, 0.00, NULL),
(28, 16, 30, 0.00, 615.00, NULL),
(29, 17, 10, 212.00, 0.00, NULL),
(30, 17, 30, 0.00, 212.00, NULL),
(31, 18, 10, 615.00, 0.00, NULL),
(32, 18, 30, 0.00, 615.00, NULL);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `cajas`
--

CREATE TABLE `cajas` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `sucursal_id` int(11) DEFAULT NULL,
  `activo` tinyint(1) NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `cajas`
--

INSERT INTO `cajas` (`id`, `empresa_id`, `nombre`, `sucursal_id`, `activo`) VALUES
(1, 1, 'Caja principal', NULL, 1),
(2, 1, 'Caja Principal', NULL, 1);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `caja_botones`
--

CREATE TABLE `caja_botones` (
  `id` int(11) NOT NULL,
  `caja_id` int(11) NOT NULL,
  `fila` int(11) NOT NULL,
  `columna` int(11) NOT NULL,
  `etiqueta` varchar(50) NOT NULL,
  `color` varchar(20) DEFAULT NULL,
  `tipo` enum('producto','combo','categoria') NOT NULL DEFAULT 'producto',
  `producto_id` int(11) DEFAULT NULL,
  `combo_id` int(11) DEFAULT NULL,
  `categoria_id` int(11) DEFAULT NULL,
  `empresa_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `caja_ventas`
--

CREATE TABLE `caja_ventas` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) DEFAULT NULL,
  `turno_id` int(11) DEFAULT NULL,
  `usuario_id` int(11) DEFAULT NULL,
  `folio` varchar(50) DEFAULT NULL,
  `fecha` datetime DEFAULT current_timestamp(),
  `subtotal` decimal(12,2) DEFAULT 0.00,
  `iva` decimal(12,2) DEFAULT 0.00,
  `total` decimal(12,2) DEFAULT 0.00,
  `metodo_pago` varchar(50) DEFAULT 'efectivo',
  `estado` varchar(20) DEFAULT 'completada',
  `cliente_nombre` varchar(200) DEFAULT NULL,
  `notas` text DEFAULT NULL,
  `efectivo_recibido` decimal(12,2) DEFAULT 0.00,
  `cambio` decimal(12,2) DEFAULT 0.00,
  `descuento` decimal(12,2) DEFAULT 0.00,
  `cancelada` tinyint(1) DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `caja_ventas`
--

INSERT INTO `caja_ventas` (`id`, `empresa_id`, `turno_id`, `usuario_id`, `folio`, `fecha`, `subtotal`, `iva`, `total`, `metodo_pago`, `estado`, `cliente_nombre`, `notas`, `efectivo_recibido`, `cambio`, `descuento`, `cancelada`) VALUES
(5, 1, NULL, 13, NULL, '2025-12-04 21:08:44', 0.00, 0.00, 1941.00, 'efectivo', 'completada', NULL, NULL, 0.00, 0.00, 0.00, 0);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `caja_ventas_detalle`
--

CREATE TABLE `caja_ventas_detalle` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) DEFAULT NULL,
  `venta_id` int(11) DEFAULT NULL,
  `producto_id` int(11) DEFAULT NULL,
  `mercancia_id` int(11) DEFAULT NULL,
  `cantidad` decimal(10,3) DEFAULT 1.000,
  `precio_unitario` decimal(12,2) DEFAULT 0.00,
  `subtotal` decimal(12,2) DEFAULT 0.00
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `caja_ventas_detalle`
--

INSERT INTO `caja_ventas_detalle` (`id`, `empresa_id`, `venta_id`, `producto_id`, `mercancia_id`, `cantidad`, `precio_unitario`, `subtotal`) VALUES
(1, 1, 5, NULL, 66, 2.000, 68.00, 136.00),
(2, 1, 5, NULL, 64, 3.000, 68.00, 204.00),
(3, 1, 5, NULL, 55, 25.000, 15.00, 375.00),
(4, 1, 5, NULL, 56, 27.000, 18.00, 486.00),
(5, 1, 5, NULL, 57, 10.000, 16.00, 160.00),
(6, 1, 5, NULL, 58, 7.000, 27.00, 189.00),
(7, 1, 5, NULL, 59, 1.000, 42.00, 42.00),
(8, 1, 5, NULL, 60, 1.000, 65.00, 65.00),
(9, 1, 5, NULL, 61, 2.000, 22.00, 44.00),
(10, 1, 5, NULL, 62, 1.000, 8.00, 8.00),
(11, 1, 5, NULL, 63, 4.000, 58.00, 232.00);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `catalogo_inventario`
--

CREATE TABLE `catalogo_inventario` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `nombre` varchar(255) NOT NULL,
  `tipo` enum('MP','WIP','PT') DEFAULT 'MP',
  `activo` tinyint(1) DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `catalogo_modulos`
--

CREATE TABLE `catalogo_modulos` (
  `id` int(11) NOT NULL,
  `codigo` varchar(50) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `descripcion` text DEFAULT NULL,
  `precio_mensual` decimal(10,2) NOT NULL DEFAULT 0.00,
  `precio_anual` decimal(10,2) NOT NULL DEFAULT 0.00,
  `activo` tinyint(1) DEFAULT 1,
  `orden` int(11) DEFAULT 0,
  `icono` varchar(50) DEFAULT NULL,
  `color` varchar(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `catalogo_modulos`
--

INSERT INTO `catalogo_modulos` (`id`, `codigo`, `nombre`, `descripcion`, `precio_mensual`, `precio_anual`, `activo`, `orden`, `icono`, `color`) VALUES
(1, 'VENTAS', 'Ventas', 'Gesti?n completa de ventas y cotizaciones', 299.00, 2990.00, 1, 1, 'shopping-cart', '#10b981'),
(2, 'COMPRAS', 'Compras', 'Control de compras y proveedores', 299.00, 2990.00, 1, 2, 'shopping-bag', '#3b82f6'),
(3, 'INVENTARIO', 'Inventario', 'Control de inventarios y almacenes', 399.00, 3990.00, 1, 3, 'package', '#8b5cf6'),
(4, 'CONTABILIDAD', 'Contabilidad', 'Contabilidad y finanzas', 499.00, 4990.00, 1, 4, 'calculator', '#f59e0b'),
(5, 'NOMINA', 'N?mina', 'Gesti?n de n?mina y RRHH', 599.00, 5990.00, 1, 5, 'users', '#ef4444'),
(6, 'CRM', 'CRM', 'Gesti?n de relaciones con clientes', 399.00, 3990.00, 1, 6, 'user-check', '#06b6d4'),
(7, 'PRODUCCION', 'Producci?n', 'Control de producci?n y manufactura', 499.00, 4990.00, 1, 7, 'settings', '#6366f1'),
(8, 'PROYECTOS', 'Proyectos', 'Gesti?n de proyectos', 399.00, 3990.00, 1, 8, 'briefcase', '#ec4899');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `catalogo_mp`
--

CREATE TABLE `catalogo_mp` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `nombre` varchar(255) NOT NULL,
  `unidad_id` int(11) DEFAULT NULL,
  `activo` tinyint(1) DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `cfdi_importados`
--

CREATE TABLE `cfdi_importados` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `uuid` varchar(36) NOT NULL,
  `tipo_comprobante` enum('I','E','P','N','T') DEFAULT 'I',
  `es_emitido` tinyint(1) DEFAULT 0,
  `rfc_emisor` varchar(20) NOT NULL,
  `nombre_emisor` varchar(255) DEFAULT NULL,
  `rfc_receptor` varchar(20) NOT NULL,
  `nombre_receptor` varchar(255) DEFAULT NULL,
  `fecha_emision` date DEFAULT NULL,
  `fecha_timbrado` datetime DEFAULT NULL,
  `subtotal` decimal(12,2) NOT NULL,
  `descuento` decimal(12,2) DEFAULT 0.00,
  `iva` decimal(12,2) DEFAULT 0.00,
  `isr_retenido` decimal(12,2) DEFAULT 0.00,
  `iva_retenido` decimal(12,2) DEFAULT 0.00,
  `total` decimal(12,2) NOT NULL,
  `forma_pago` varchar(10) DEFAULT NULL,
  `metodo_pago` varchar(10) DEFAULT NULL,
  `moneda` varchar(5) DEFAULT 'MXN',
  `tipo_cambio` decimal(12,4) DEFAULT 1.0000,
  `uso_cfdi` varchar(10) DEFAULT NULL,
  `estado_sat` enum('vigente','cancelado') DEFAULT 'vigente',
  `xml_contenido` longtext DEFAULT NULL,
  `pdf_ruta` varchar(500) DEFAULT NULL,
  `conciliado` tinyint(1) DEFAULT 0,
  `compra_id` int(11) DEFAULT NULL,
  `venta_id` int(11) DEFAULT NULL,
  `fecha_creacion` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `cfdi_importados_detalle`
--

CREATE TABLE `cfdi_importados_detalle` (
  `id` int(11) NOT NULL,
  `cfdi_id` int(11) NOT NULL,
  `clave_prod_serv` varchar(20) DEFAULT NULL,
  `clave_unidad` varchar(10) DEFAULT NULL,
  `descripcion` varchar(500) DEFAULT NULL,
  `cantidad` decimal(12,3) NOT NULL,
  `valor_unitario` decimal(12,4) NOT NULL,
  `descuento` decimal(12,2) DEFAULT 0.00,
  `importe` decimal(12,2) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `cfdi_log`
--

CREATE TABLE `cfdi_log` (
  `id` int(11) NOT NULL,
  `venta_id` int(11) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `accion` enum('TIMBRADO','CANCELACION','ERROR') NOT NULL,
  `fecha` timestamp NOT NULL DEFAULT current_timestamp(),
  `uuid` varchar(100) DEFAULT NULL,
  `xml_request` longtext DEFAULT NULL,
  `xml_response` longtext DEFAULT NULL,
  `error_mensaje` text DEFAULT NULL,
  `usuario_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `compras`
--

CREATE TABLE `compras` (
  `id` int(11) NOT NULL,
  `contratante_id` int(11) NOT NULL,
  `fecha` date DEFAULT NULL,
  `proveedor` varchar(255) DEFAULT NULL,
  `numero_factura` varchar(50) DEFAULT NULL,
  `total` decimal(10,2) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `consumos_internos`
--

CREATE TABLE `consumos_internos` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `registro_id` int(11) DEFAULT NULL,
  `fecha` date NOT NULL,
  `producto_id` int(11) NOT NULL,
  `producto_nombre` varchar(255) DEFAULT NULL,
  `cantidad` decimal(10,3) NOT NULL DEFAULT 1.000,
  `costo_unitario` decimal(12,2) DEFAULT 0.00,
  `costo_total` decimal(12,2) DEFAULT 0.00,
  `responsable` varchar(100) DEFAULT NULL,
  `motivo` varchar(255) DEFAULT NULL,
  `usuario_id` int(11) DEFAULT NULL,
  `fecha_registro` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `consumos_propios`
--

CREATE TABLE `consumos_propios` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) DEFAULT NULL,
  `turno_id` int(11) NOT NULL,
  `fecha` datetime NOT NULL,
  `producto_id` int(11) NOT NULL,
  `producto_nombre` varchar(200) DEFAULT NULL,
  `cantidad` decimal(10,3) NOT NULL,
  `precio_unitario` decimal(10,2) NOT NULL,
  `subtotal` decimal(10,2) NOT NULL,
  `usuario_id` int(11) NOT NULL,
  `notas` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `consumos_propios`
--

INSERT INTO `consumos_propios` (`id`, `empresa_id`, `turno_id`, `fecha`, `producto_id`, `producto_nombre`, `cantidad`, `precio_unitario`, `subtotal`, `usuario_id`, `notas`) VALUES
(1, 1, 2, '2025-12-04 21:27:48', 56, 'Cono Galleta', 1.000, 18.00, 18.00, 13, ''),
(2, 1, 2, '2025-12-04 21:28:04', 62, 'Agua 500ml', 2.000, 8.00, 16.00, 13, '');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `contratantes`
--

CREATE TABLE `contratantes` (
  `id` int(11) NOT NULL,
  `razon_social` varchar(255) NOT NULL,
  `tipo_organizacion` enum('grupo','empresa_unica') DEFAULT 'empresa_unica',
  `tipo_industria` enum('manufactura','servicios','retail','distribucion','mixto') DEFAULT 'mixto',
  `rfc` varchar(13) NOT NULL,
  `email_contacto` varchar(255) NOT NULL,
  `telefono` varchar(20) DEFAULT NULL,
  `direccion` text DEFAULT NULL,
  `ciudad` varchar(100) DEFAULT NULL,
  `estado` varchar(100) DEFAULT NULL,
  `cp` varchar(10) DEFAULT NULL,
  `pais` varchar(100) DEFAULT NULL,
  `activo` tinyint(1) DEFAULT 1,
  `fecha_registro` timestamp NOT NULL DEFAULT current_timestamp(),
  `fecha_suspension` timestamp NULL DEFAULT NULL,
  `notas` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `contratantes`
--

INSERT INTO `contratantes` (`id`, `razon_social`, `tipo_organizacion`, `tipo_industria`, `rfc`, `email_contacto`, `telefono`, `direccion`, `ciudad`, `estado`, `cp`, `pais`, `activo`, `fecha_registro`, `fecha_suspension`, `notas`) VALUES
(1, 'Empresa Demo', 'empresa_unica', 'mixto', 'XAXX010101000', 'demo@empresa.com', '0000000000', NULL, NULL, NULL, NULL, 'M?xico', 1, '2025-12-26 05:42:02', NULL, NULL),
(5, 'Yolo Postres ', 'grupo', 'mixto', 'GAEF760207I26', 'pakogranados1@hotmail.com', '6567921773', 'Avenida 2da de Ugarte 574 local 16', 'Ciudad Juarez', 'Chihuahua', '32130', NULL, 1, '2025-12-28 09:59:09', NULL, NULL);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `cuentas_contables`
--

CREATE TABLE `cuentas_contables` (
  `id` int(11) NOT NULL,
  `contratante_id` int(11) NOT NULL,
  `codigo` varchar(20) NOT NULL,
  `nombre` varchar(255) NOT NULL,
  `tipo` enum('Activo','Pasivo','Patrimonio','Ingresos','Gastos') NOT NULL,
  `naturaleza` enum('Deudora','Acreedora') NOT NULL,
  `nivel` tinyint(4) NOT NULL,
  `padre_id` int(11) DEFAULT NULL,
  `permite_subcuentas` tinyint(1) NOT NULL DEFAULT 0,
  `empresa_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `cuentas_contables`
--

INSERT INTO `cuentas_contables` (`id`, `contratante_id`, `codigo`, `nombre`, `tipo`, `naturaleza`, `nivel`, `padre_id`, `permite_subcuentas`, `empresa_id`) VALUES
(1, 1, '100-000-000', 'ACTIVO', 'Activo', 'Deudora', 1, NULL, 0, NULL),
(2, 1, '200-000-000', 'PASIVO', 'Pasivo', 'Acreedora', 1, NULL, 0, NULL),
(3, 1, '300-000-000', 'PATRIMONIO', 'Patrimonio', 'Acreedora', 1, NULL, 0, NULL),
(4, 1, '110-000-000', 'ACTIVO CIRCULANTE', 'Activo', 'Deudora', 1, 1, 0, NULL),
(5, 1, '112-000-000', 'INVENTARIOS', 'Activo', 'Deudora', 1, 4, 0, NULL),
(6, 1, '112-001-000', 'MERCANC脥AS', 'Activo', 'Deudora', 2, 5, 1, NULL),
(7, 1, '112-001-001', 'AZUCAR 2KG', 'Activo', 'Deudora', 3, 6, 0, NULL),
(8, 1, '111-000-000', 'EFECTIVO Y EQUIVALENTES', 'Activo', 'Deudora', 1, 4, 0, NULL),
(9, 1, '111-001-000', 'CAJA', 'Activo', 'Deudora', 2, 8, 0, NULL),
(10, 1, '111-002-000', 'BANCOS', 'Activo', 'Deudora', 2, 8, 0, NULL),
(11, 1, '111-003-000', 'CUENTAS DE TERCEROS', 'Activo', 'Deudora', 2, 8, 1, NULL),
(12, 1, '111-004-000', 'OTROS EFECTIVOS', 'Activo', 'Deudora', 2, 8, 0, NULL),
(13, 1, '112-002-000', 'MATERIAS PRIMAS', 'Activo', 'Deudora', 2, 5, 1, NULL),
(14, 1, '112-003-000', 'PRODUCTOS EN PROCESO', 'Activo', 'Deudora', 2, 5, 1, NULL),
(15, 1, '113-000-000', 'CUENTAS POR COBRAR', 'Activo', 'Deudora', 1, 4, 0, NULL),
(16, 1, '113-001-000', 'CLIENTES', 'Activo', 'Deudora', 2, 15, 1, NULL),
(17, 1, '113-002-000', 'DEUDORES DIVERSOS', 'Activo', 'Deudora', 2, 15, 1, NULL),
(18, 1, '114-000-000', 'OTROS ACTIVOS CIRCULANTES', 'Activo', 'Deudora', 1, 4, 0, NULL),
(19, 1, '114-001-000', 'ANTICIPOS', 'Activo', 'Deudora', 2, 18, 1, NULL),
(20, 1, '114-002-000', 'IMPUESTOS A FAVOR', 'Activo', 'Deudora', 2, 18, 1, NULL),
(21, 1, '130-000-000', 'INVENTARIOS (ALTERNOS)', 'Activo', 'Deudora', 1, 1, 0, NULL),
(22, 1, '130-001-000', 'MERCANC脥AS A', 'Activo', 'Deudora', 2, 21, 1, NULL),
(23, 1, '130-002-000', 'MERCANC脥AS B', 'Activo', 'Deudora', 2, 21, 1, NULL),
(24, 1, '130-003-000', 'MERCANC脥AS C', 'Activo', 'Deudora', 2, 21, 1, NULL),
(25, 1, '130-004-000', 'MERCANC脥AS D', 'Activo', 'Deudora', 2, 21, 1, NULL),
(26, 1, '130-005-000', 'MERCANC脥AS E', 'Activo', 'Deudora', 2, 21, 1, NULL),
(27, 1, '130-006-000', 'MERCANC脥AS F', 'Activo', 'Deudora', 2, 21, 1, NULL),
(28, 1, '130-007-000', 'MERCANC脥AS G', 'Activo', 'Deudora', 2, 21, 1, NULL),
(29, 1, '130-008-000', 'MERCANC脥AS H', 'Activo', 'Deudora', 2, 21, 1, NULL),
(30, 1, '150-000-000', 'ACTIVO NO CIRCULANTE', 'Activo', 'Deudora', 1, 1, 0, NULL),
(31, 1, '151-000-000', 'ACTIVOS FIJOS', 'Activo', 'Deudora', 1, 30, 0, NULL),
(32, 1, '151-001-000', 'MOBILIARIO Y EQUIPO', 'Activo', 'Deudora', 2, 31, 1, NULL),
(33, 1, '151-002-000', 'EQUIPO DE C脫MPUTO', 'Activo', 'Deudora', 2, 31, 1, NULL),
(34, 1, '151-003-000', 'EQUIPO DE TRANSPORTE', 'Activo', 'Deudora', 2, 31, 1, NULL),
(35, 1, '151-004-000', 'OTROS ACTIVOS FIJOS', 'Activo', 'Deudora', 2, 31, 1, NULL),
(36, 1, '210-000-000', 'PASIVO CIRCULANTE', 'Pasivo', 'Acreedora', 1, 2, 0, NULL),
(37, 1, '211-000-000', 'PROVEEDORES Y ACREEDORES', 'Pasivo', 'Acreedora', 1, 36, 0, NULL),
(38, 1, '211-001-000', 'PROVEEDORES', 'Pasivo', 'Acreedora', 2, 37, 1, NULL),
(39, 1, '211-002-000', 'ACREEDORES', 'Pasivo', 'Acreedora', 2, 37, 1, NULL),
(40, 1, '212-000-000', 'PASIVOS ACUMULADOS', 'Pasivo', 'Acreedora', 1, 36, 0, NULL),
(41, 1, '212-001-000', 'IMPUESTOS POR PAGAR', 'Pasivo', 'Acreedora', 2, 40, 1, NULL),
(42, 1, '212-002-000', 'OTROS PASIVOS', 'Pasivo', 'Acreedora', 2, 40, 0, NULL),
(43, 1, '220-000-000', 'PASIVO A LARGO PLAZO', 'Pasivo', 'Acreedora', 1, 2, 0, NULL),
(44, 1, '221-000-000', 'CR脡DITOS DE LARGO PLAZO', 'Pasivo', 'Acreedora', 1, 43, 0, NULL),
(45, 1, '221-001-000', 'CR脡DITOS BANCARIOS', 'Pasivo', 'Acreedora', 2, 44, 1, NULL),
(46, 1, '301-000-000', 'CAPITAL SOCIAL Y RESULTADOS', 'Patrimonio', 'Acreedora', 1, 3, 0, NULL),
(47, 1, '301-001-000', 'CAPITAL SOCIAL', 'Patrimonio', 'Acreedora', 2, 46, 0, NULL),
(48, 1, '301-002-000', 'RESERVAS', 'Patrimonio', 'Acreedora', 2, 46, 0, NULL),
(49, 1, '301-003-000', 'RESULTADOS ACUMULADOS', 'Patrimonio', 'Acreedora', 2, 46, 0, NULL),
(50, 1, '301-004-000', 'RESULTADO DEL EJERCICIO', 'Patrimonio', 'Acreedora', 2, 46, 0, NULL),
(51, 1, '400-000-000', 'INGRESOS', 'Ingresos', 'Acreedora', 1, NULL, 0, NULL),
(52, 1, '401-000-000', 'INGRESOS ORDINARIOS', 'Ingresos', 'Acreedora', 1, 51, 0, NULL),
(53, 1, '401-001-000', 'VENTAS', 'Ingresos', 'Acreedora', 2, 52, 1, NULL),
(54, 1, '402-000-000', 'OTROS INGRESOS', 'Ingresos', 'Acreedora', 1, 51, 0, NULL),
(55, 1, '402-001-000', 'OTROS PRODUCTOS', 'Ingresos', 'Acreedora', 2, 54, 1, NULL),
(56, 1, '500-000-000', 'COSTOS Y CUENTAS RELACIONADAS', 'Gastos', 'Deudora', 1, NULL, 0, NULL),
(57, 1, '501-000-000', 'COSTO DE VENTAS', 'Gastos', 'Deudora', 1, 56, 0, NULL),
(58, 1, '501-001-000', 'COSTO MERCANC脥AS', 'Gastos', 'Deudora', 2, 57, 1, NULL),
(59, 1, '501-002-000', 'OTROS COSTOS', 'Gastos', 'Deudora', 2, 57, 1, NULL),
(60, 1, '502-000-000', 'CLIENTES / CUENTAS RELACIONADAS', 'Gastos', 'Deudora', 1, 56, 1, NULL),
(61, 1, '600-000-000', 'GASTOS', 'Gastos', 'Deudora', 1, NULL, 1, NULL),
(62, 1, '600-001-001', 'Sueldos y Salarios', 'Gastos', 'Deudora', 3, 108, 0, NULL),
(63, 1, '600-001-002', 'Horas Extras', 'Gastos', 'Deudora', 3, 108, 0, NULL),
(64, 1, '600-001-003', 'Comisiones de venta', 'Gastos', 'Deudora', 3, 108, 0, NULL),
(65, 1, '600-001-004', 'Renta', 'Gastos', 'Deudora', 3, 108, 0, NULL),
(66, 1, '600-001-005', 'Mejoras en Imagen', 'Gastos', 'Deudora', 3, 108, 0, NULL),
(67, 1, '600-001-006', 'Luz', 'Gastos', 'Deudora', 3, 108, 0, NULL),
(68, 1, '600-001-007', 'Agua', 'Gastos', 'Deudora', 3, 108, 0, NULL),
(69, 1, '600-001-008', 'Gas', 'Gastos', 'Deudora', 3, 108, 0, NULL),
(70, 1, '600-001-009', 'Aseguranza', 'Gastos', 'Deudora', 3, 108, 0, NULL),
(71, 1, '600-001-010', 'Articulos de limpieza', 'Gastos', 'Deudora', 3, 108, 0, NULL),
(72, 1, '600-001-011', 'Mantenimiento de equipo', 'Gastos', 'Deudora', 3, 108, 0, NULL),
(73, 1, '600-001-012', 'Suministro de oficina', 'Gastos', 'Deudora', 3, 108, 0, NULL),
(74, 1, '600-001-013', 'Gasolina', 'Gastos', 'Deudora', 3, 108, 0, NULL),
(75, 1, '600-001-014', 'Publicidad', 'Gastos', 'Deudora', 3, 108, 0, NULL),
(76, 1, '600-001-015', 'Reclutamiento', 'Gastos', 'Deudora', 3, 108, 0, NULL),
(77, 1, '600-001-016', 'Capacitaci?n', 'Gastos', 'Deudora', 3, 108, 0, NULL),
(78, 1, '600-001-017', 'Gastos de Transporte', 'Gastos', 'Deudora', 3, 108, 0, NULL),
(79, 1, '600-001-018', 'Comida empleados', 'Gastos', 'Deudora', 3, 108, 0, NULL),
(80, 1, '600-001-019', 'Cortesias empleados', 'Gastos', 'Deudora', 3, 108, 0, NULL),
(81, 1, '600-001-020', 'Gastos Varios', 'Gastos', 'Deudora', 3, 108, 0, NULL),
(82, 1, '600-001-021', 'Gastos Corporativos', 'Gastos', 'Deudora', 3, 108, 0, NULL),
(83, 1, '600-001-022', 'Intereses financieros', 'Gastos', 'Deudora', 3, 108, 0, NULL),
(84, 1, '600-001-023', 'Comisiones bancarias', 'Gastos', 'Deudora', 3, 108, 0, NULL),
(85, 1, '600-001-024', 'ISR', 'Gastos', 'Deudora', 3, 108, 0, NULL),
(86, 1, '600-001-025', 'IEPS', 'Gastos', 'Deudora', 3, 108, 0, NULL),
(87, 1, '212-002-001', 'OTRO PASIVO 001', 'Pasivo', 'Acreedora', 3, 42, 0, NULL),
(88, 1, '212-002-002', 'OTRO PASIVO 002', 'Pasivo', 'Acreedora', 3, 42, 0, NULL),
(89, 1, '212-002-003', 'OTRO PASIVO 003', 'Pasivo', 'Acreedora', 3, 42, 0, NULL),
(90, 1, '212-002-004', 'OTRO PASIVO 004', 'Pasivo', 'Acreedora', 3, 42, 0, NULL),
(91, 1, '212-002-005', 'OTRO PASIVO 005', 'Pasivo', 'Acreedora', 3, 42, 0, NULL),
(92, 1, '212-002-006', 'OTRO PASIVO 006', 'Pasivo', 'Acreedora', 3, 42, 0, NULL),
(93, 1, '212-002-007', 'OTRO PASIVO 007', 'Pasivo', 'Acreedora', 3, 42, 0, NULL),
(94, 1, '212-002-008', 'OTRO PASIVO 008', 'Pasivo', 'Acreedora', 3, 42, 0, NULL),
(95, 1, '212-002-009', 'OTRO PASIVO 009', 'Pasivo', 'Acreedora', 3, 42, 0, NULL),
(96, 1, '212-002-010', 'OTRO PASIVO 010', 'Pasivo', 'Acreedora', 3, 42, 0, NULL),
(97, 1, '301-003-001', 'RESULTADOS ACUMULADOS DETALLE', 'Patrimonio', 'Acreedora', 3, 49, 0, NULL),
(98, 1, '301-004-001', 'RESULTADO 001', 'Patrimonio', 'Acreedora', 3, 50, 0, NULL),
(99, 1, '301-004-002', 'RESULTADO 002', 'Patrimonio', 'Acreedora', 3, 50, 0, NULL),
(100, 1, '301-004-003', 'RESULTADO 003', 'Patrimonio', 'Acreedora', 3, 50, 0, NULL),
(101, 1, '301-004-004', 'RESULTADO 004', 'Patrimonio', 'Acreedora', 3, 50, 0, NULL),
(102, 1, '301-004-005', 'RESULTADO 005', 'Patrimonio', 'Acreedora', 3, 50, 0, NULL),
(103, 1, '301-004-006', 'RESULTADO 006', 'Patrimonio', 'Acreedora', 3, 50, 0, NULL),
(104, 1, '301-004-007', 'RESULTADO 007', 'Patrimonio', 'Acreedora', 3, 50, 0, NULL),
(105, 1, '301-004-008', 'RESULTADO 008', 'Patrimonio', 'Acreedora', 3, 50, 0, NULL),
(106, 1, '301-004-009', 'RESULTADO 009', 'Patrimonio', 'Acreedora', 3, 50, 0, NULL),
(107, 1, '112-001-002', 'AZUCAR 5KG', 'Activo', 'Deudora', 3, 6, 0, NULL),
(108, 1, '600-001-000', 'GASTOS OPERATIVOS', 'Gastos', 'Deudora', 2, 61, 1, NULL),
(109, 1, '600-001-026', 'IVA', 'Gastos', 'Deudora', 3, 108, 0, NULL),
(110, 1, '112-001-003', 'HIELO', 'Activo', 'Deudora', 3, 6, 0, NULL),
(111, 1, '112-001-004', 'GASOLINA', 'Activo', 'Deudora', 3, 6, 0, NULL),
(112, 1, '112-001-005', 'AZUCAR 1 KG', 'Activo', 'Deudora', 3, 6, 0, NULL),
(113, 1, '112-001-006', 'CACAHUATE', 'Activo', 'Deudora', 3, 6, 0, NULL),
(114, 1, '112-001-007', 'CAJETA 1KG', 'Activo', 'Deudora', 3, 6, 0, NULL),
(115, 1, '112-001-008', 'CAJETA 5KG', 'Activo', 'Deudora', 3, 6, 0, NULL),
(116, 1, '112-001-009', 'CONO WAFFLE', 'Activo', 'Deudora', 3, 6, 0, NULL),
(117, 1, '112-001-010', 'CONO CHOCOLATE', 'Activo', 'Deudora', 3, 6, 0, NULL),
(118, 1, '112-001-011', 'IEPS', 'Activo', 'Deudora', 3, 6, 0, NULL),
(119, 1, '112-001-012', 'IVA', 'Activo', 'Deudora', 3, 6, 0, NULL),
(120, 1, '112-001-013', 'HARINA PARA BROWNIES 3.4KG', 'Activo', 'Deudora', 3, 6, 0, NULL),
(121, 1, '112-001-014', 'HARINA PARA BROWNIES 2.26KG', 'Activo', 'Deudora', 3, 6, 0, NULL),
(122, 1, '112-001-015', 'FRESA 1KG', 'Activo', 'Deudora', 3, 6, 0, NULL);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `cuentas_por_cobrar`
--

CREATE TABLE `cuentas_por_cobrar` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `factura_b2b_id` int(11) DEFAULT NULL,
  `cfdi_id` int(11) DEFAULT NULL,
  `venta_id` int(11) DEFAULT NULL,
  `cliente_empresa_id` int(11) DEFAULT NULL,
  `cliente_nombre` varchar(255) DEFAULT NULL,
  `cliente_rfc` varchar(20) DEFAULT NULL,
  `tipo_documento` enum('factura_b2b','cfdi','venta_manual') NOT NULL,
  `numero_documento` varchar(50) DEFAULT NULL,
  `fecha_documento` date DEFAULT NULL,
  `fecha_vencimiento` date DEFAULT NULL,
  `monto_original` decimal(12,2) NOT NULL,
  `monto_cobrado` decimal(12,2) DEFAULT 0.00,
  `saldo` decimal(12,2) NOT NULL,
  `estado` enum('pendiente','parcial','cobrada','cancelada') DEFAULT 'pendiente',
  `autorizado_por_usuario_id` int(11) DEFAULT NULL,
  `fecha_autorizacion` datetime DEFAULT NULL,
  `fecha_creacion` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `cuentas_por_pagar`
--

CREATE TABLE `cuentas_por_pagar` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `factura_b2b_id` int(11) DEFAULT NULL,
  `cfdi_id` int(11) DEFAULT NULL,
  `compra_id` int(11) DEFAULT NULL,
  `proveedor_empresa_id` int(11) DEFAULT NULL,
  `proveedor_nombre` varchar(255) DEFAULT NULL,
  `proveedor_rfc` varchar(20) DEFAULT NULL,
  `tipo_documento` enum('factura_b2b','cfdi','compra_manual') NOT NULL,
  `numero_documento` varchar(50) DEFAULT NULL,
  `fecha_documento` date DEFAULT NULL,
  `fecha_vencimiento` date DEFAULT NULL,
  `monto_original` decimal(12,2) NOT NULL,
  `monto_pagado` decimal(12,2) DEFAULT 0.00,
  `saldo` decimal(12,2) NOT NULL,
  `estado` enum('pendiente','parcial','pagada','cancelada') DEFAULT 'pendiente',
  `autorizado_por_usuario_id` int(11) DEFAULT NULL,
  `fecha_autorizacion` datetime DEFAULT NULL,
  `fecha_creacion` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `detalle_compra`
--

CREATE TABLE `detalle_compra` (
  `id` int(11) NOT NULL,
  `compra_id` int(11) NOT NULL,
  `mercancia_id` int(11) DEFAULT NULL,
  `producto` varchar(255) DEFAULT NULL,
  `unidades` decimal(10,2) DEFAULT NULL,
  `precio_unitario` decimal(10,2) DEFAULT NULL,
  `precio_total` decimal(10,2) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `detalle_compra`
--

INSERT INTO `detalle_compra` (`id`, `compra_id`, `mercancia_id`, `producto`, `unidades`, `precio_unitario`, `precio_total`) VALUES
(6, 37, 38, 'Hielo', 1.00, 34.00, 34.00),
(7, 38, NULL, 'Nieve Chocolate', 1.00, 595.00, 595.00),
(8, 38, NULL, 'Nieve Vainilla', 1.00, 585.00, 585.00),
(9, 38, NULL, 'Cono Chocolate', 1.00, 810.00, 810.00),
(10, 39, 39, 'Gasolina', 1.00, 379.80, 379.80);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `detalle_venta`
--

CREATE TABLE `detalle_venta` (
  `id` int(11) NOT NULL,
  `producto_terminado_id` int(11) DEFAULT NULL,
  `venta_id` int(11) NOT NULL,
  `mercancia_id` int(11) NOT NULL,
  `unidades` decimal(10,2) NOT NULL,
  `precio_unitario` decimal(10,2) NOT NULL,
  `fecha` date NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `empresas`
--

CREATE TABLE `empresas` (
  `id` int(11) NOT NULL,
  `contratante_id` int(11) DEFAULT NULL,
  `nombre` varchar(255) NOT NULL,
  `rfc` varchar(20) DEFAULT NULL,
  `puede_compartir_rfc` tinyint(1) DEFAULT 1,
  `direccion` text DEFAULT NULL,
  `telefono` varchar(20) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `activo` tinyint(1) DEFAULT 1,
  `fecha_creacion` datetime DEFAULT current_timestamp(),
  `fecha_registro` datetime DEFAULT current_timestamp(),
  `logo_url` varchar(500) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `empresas`
--

INSERT INTO `empresas` (`id`, `contratante_id`, `nombre`, `rfc`, `puede_compartir_rfc`, `direccion`, `telefono`, `email`, `activo`, `fecha_creacion`, `fecha_registro`, `logo_url`) VALUES
(1, 1, 'Yolo SA de CV', NULL, 1, NULL, NULL, NULL, 1, '2025-12-02 22:50:02', '2025-12-02 22:50:02', NULL),
(4, 5, 'Yolo Produccion ', 'GAEF760207I26', 1, NULL, NULL, NULL, 1, '2025-12-28 02:59:14', '2025-12-28 02:59:14', NULL),
(5, 5, 'Yolo Pasaje', 'GAEF760207I26', 1, NULL, NULL, NULL, 1, '2025-12-28 21:45:47', '2025-12-28 21:45:47', NULL);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `empresa_configuracion`
--

CREATE TABLE `empresa_configuracion` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `empleados_rango` enum('1-5','6-10','11-25','26-99','100-200','200+') NOT NULL,
  `tipo_comprobantes` enum('solo_facturas','solo_tickets','mixto') NOT NULL,
  `tipo_mercancia` enum('materia_prima','producto_directo') NOT NULL,
  `requiere_manufactura` tinyint(1) DEFAULT 0,
  `requiere_wip` tinyint(1) DEFAULT 0,
  `requiere_recetas` tinyint(1) DEFAULT 0,
  `nivel_complejidad` enum('basico','intermedio','avanzado') DEFAULT 'basico',
  `modulo_compras` tinyint(1) DEFAULT 1,
  `modulo_ventas` tinyint(1) DEFAULT 1,
  `modulo_inventario_mp` tinyint(1) DEFAULT 1,
  `modulo_inventario_wip` tinyint(1) DEFAULT 0,
  `modulo_inventario_pt` tinyint(1) DEFAULT 1,
  `modulo_produccion` tinyint(1) DEFAULT 0,
  `modulo_contabilidad` tinyint(1) DEFAULT 0,
  `frecuencia_inventario` enum('turno','diario','semanal','mensual','anual','otro') DEFAULT 'turno',
  `frecuencia_inventario_desc` varchar(255) DEFAULT NULL,
  `fecha_configuracion` datetime DEFAULT current_timestamp(),
  `configuracion_completada` tinyint(1) DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `empresa_configuracion`
--

INSERT INTO `empresa_configuracion` (`id`, `empresa_id`, `empleados_rango`, `tipo_comprobantes`, `tipo_mercancia`, `requiere_manufactura`, `requiere_wip`, `requiere_recetas`, `nivel_complejidad`, `modulo_compras`, `modulo_ventas`, `modulo_inventario_mp`, `modulo_inventario_wip`, `modulo_inventario_pt`, `modulo_produccion`, `modulo_contabilidad`, `frecuencia_inventario`, `frecuencia_inventario_desc`, `fecha_configuracion`, `configuracion_completada`) VALUES
(1, 1, '1-5', 'mixto', 'producto_directo', 0, 0, 0, 'basico', 1, 1, 1, 0, 1, 0, 1, 'turno', NULL, '2025-12-02 22:50:50', 1);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `empresa_modulos`
--

CREATE TABLE `empresa_modulos` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `modulo_id` int(11) NOT NULL,
  `activo` tinyint(1) DEFAULT 1,
  `fecha_activacion` timestamp NOT NULL DEFAULT current_timestamp(),
  `fecha_desactivacion` timestamp NULL DEFAULT NULL,
  `configuracion` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`configuracion`))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `empresa_modulos`
--

INSERT INTO `empresa_modulos` (`id`, `empresa_id`, `modulo_id`, `activo`, `fecha_activacion`, `fecha_desactivacion`, `configuracion`) VALUES
(3, 4, 1, 1, '2025-12-28 09:59:20', NULL, NULL),
(4, 4, 3, 1, '2025-12-28 09:59:20', NULL, NULL),
(5, 5, 1, 1, '2025-12-29 04:48:00', NULL, NULL),
(6, 5, 3, 1, '2025-12-29 04:48:01', NULL, NULL),
(7, 5, 2, 1, '2025-12-29 04:48:06', NULL, NULL);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `facturas_b2b`
--

CREATE TABLE `facturas_b2b` (
  `id` int(11) NOT NULL,
  `empresa_emisora_id` int(11) NOT NULL,
  `empresa_receptora_id` int(11) NOT NULL,
  `turno_id` int(11) DEFAULT NULL,
  `orden_compra_id` int(11) DEFAULT NULL,
  `folio` varchar(30) NOT NULL,
  `fecha_emision` datetime NOT NULL,
  `fecha_vencimiento` date DEFAULT NULL,
  `subtotal` decimal(12,2) NOT NULL,
  `iva` decimal(12,2) DEFAULT 0.00,
  `total` decimal(12,2) NOT NULL,
  `forma_pago` varchar(50) DEFAULT 'Transferencia',
  `metodo_pago` enum('PUE','PPD') DEFAULT 'PUE',
  `condiciones_pago` varchar(255) DEFAULT NULL,
  `estado` enum('emitida','pendiente','en_revision','recibida','con_diferencias','cancelada') DEFAULT 'emitida',
  `estado_almacen` varchar(30) DEFAULT 'pendiente',
  `estado_reparto` varchar(30) DEFAULT 'pendiente',
  `estado_entrega` varchar(30) DEFAULT 'pendiente',
  `fecha_recepcion` datetime DEFAULT NULL,
  `recibida_por_usuario_id` int(11) DEFAULT NULL,
  `almacen_completado_por` int(11) DEFAULT NULL,
  `almacen_completado_fecha` datetime DEFAULT NULL,
  `reparto_asignado_a` int(11) DEFAULT NULL,
  `reparto_recogido_fecha` datetime DEFAULT NULL,
  `reparto_entregado_fecha` datetime DEFAULT NULL,
  `cliente_almacen_usuario_id` int(11) DEFAULT NULL,
  `cliente_almacen_fecha` datetime DEFAULT NULL,
  `notas_recepcion` text DEFAULT NULL,
  `emitida_por_usuario_id` int(11) DEFAULT NULL,
  `fecha_creacion` datetime DEFAULT current_timestamp(),
  `fecha_actualizacion` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `facturas_b2b_detalle`
--

CREATE TABLE `facturas_b2b_detalle` (
  `id` int(11) NOT NULL,
  `factura_id` int(11) NOT NULL,
  `mercancia_id` int(11) DEFAULT NULL,
  `descripcion` varchar(500) NOT NULL,
  `cantidad_facturada` decimal(12,3) NOT NULL,
  `cantidad_recibida` decimal(12,3) DEFAULT NULL,
  `precio_unitario` decimal(12,2) NOT NULL,
  `descuento` decimal(12,2) DEFAULT 0.00,
  `iva_rate` decimal(5,4) DEFAULT 0.1600,
  `importe` decimal(12,2) NOT NULL,
  `verificado` tinyint(1) DEFAULT 0,
  `verificado_por_usuario_id` int(11) DEFAULT NULL,
  `fecha_verificacion` datetime DEFAULT NULL,
  `tiene_diferencia` tinyint(1) DEFAULT 0,
  `tipo_diferencia` enum('faltante','sobrante','da?ado','otro') DEFAULT NULL,
  `notas_verificacion` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `facturas_notificaciones`
--

CREATE TABLE `facturas_notificaciones` (
  `id` int(11) NOT NULL,
  `empresa_destino_id` int(11) NOT NULL,
  `tipo_origen` enum('b2b','cfdi','cxp','cxc') NOT NULL,
  `origen_id` int(11) NOT NULL,
  `tipo_notificacion` enum('nueva','recibida','diferencia','pago','vencimiento','cancelada') NOT NULL,
  `mensaje` text DEFAULT NULL,
  `leida` tinyint(1) DEFAULT 0,
  `fecha_creacion` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `factura_b2b_checklist`
--

CREATE TABLE `factura_b2b_checklist` (
  `id` int(11) NOT NULL,
  `factura_id` int(11) NOT NULL,
  `detalle_id` int(11) NOT NULL,
  `rol` varchar(50) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `verificado` tinyint(1) DEFAULT 0,
  `cantidad_verificada` decimal(12,3) DEFAULT NULL,
  `usuario_id` int(11) DEFAULT NULL,
  `usuario_nombre` varchar(100) DEFAULT NULL,
  `fecha_verificacion` datetime DEFAULT NULL,
  `tiene_diferencia` tinyint(1) DEFAULT 0,
  `tipo_diferencia` varchar(50) DEFAULT NULL,
  `cantidad_diferencia` decimal(12,3) DEFAULT NULL,
  `notas` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `factura_b2b_tracking`
--

CREATE TABLE `factura_b2b_tracking` (
  `id` int(11) NOT NULL,
  `factura_id` int(11) NOT NULL,
  `estado_anterior` varchar(50) DEFAULT NULL,
  `estado_nuevo` varchar(50) NOT NULL,
  `usuario_id` int(11) NOT NULL,
  `usuario_nombre` varchar(100) DEFAULT NULL,
  `rol` varchar(50) DEFAULT NULL,
  `empresa_id` int(11) DEFAULT NULL,
  `accion` varchar(100) DEFAULT NULL,
  `notas` text DEFAULT NULL,
  `fecha` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `historial_asignaciones_area`
--

CREATE TABLE `historial_asignaciones_area` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `usuario_id` int(11) NOT NULL,
  `area_id` int(11) NOT NULL,
  `rol_anterior` varchar(50) DEFAULT NULL,
  `rol_nuevo` varchar(50) DEFAULT NULL,
  `accion` enum('asignado','modificado','removido') NOT NULL,
  `realizado_por` int(11) NOT NULL,
  `fecha` timestamp NOT NULL DEFAULT current_timestamp(),
  `notas` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `historial_pagos`
--

CREATE TABLE `historial_pagos` (
  `id` int(11) NOT NULL,
  `suscripcion_id` int(11) NOT NULL,
  `contratante_id` int(11) NOT NULL,
  `fecha_pago` timestamp NOT NULL DEFAULT current_timestamp(),
  `monto` decimal(10,2) NOT NULL,
  `metodo_pago` varchar(50) DEFAULT NULL,
  `referencia` varchar(100) DEFAULT NULL,
  `estado` enum('PENDIENTE','COMPLETADO','FALLIDO','REEMBOLSADO') DEFAULT 'PENDIENTE',
  `factura_id` int(11) DEFAULT NULL,
  `notas` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `incidencias`
--

CREATE TABLE `incidencias` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `codigo` varchar(50) DEFAULT NULL,
  `tipo_tarea` enum('produccion','compras','recepcion','almacen','reparto','cobranza','cuentas_pagar','ventas','contabilidad','mantenimiento','general') DEFAULT 'general',
  `categoria` enum('operacional','calidad','seguridad','mejora','reporte','mantenimiento','administrativo','rrhh','sistemas') DEFAULT 'operacional',
  `titulo` varchar(255) NOT NULL,
  `descripcion` text DEFAULT NULL,
  `area_id` int(11) DEFAULT NULL,
  `responsable_id` int(11) NOT NULL,
  `created_by` int(11) DEFAULT NULL,
  `estado` enum('nueva','asignada','en_analisis','en_proceso','en_revision','resuelta','cerrada','reabierta','cancelada') DEFAULT 'nueva',
  `prioridad` enum('baja','normal','alta','urgente') DEFAULT 'normal',
  `severidad` enum('critica','alta','media','baja') DEFAULT 'media',
  `fecha_asignacion` datetime DEFAULT current_timestamp(),
  `fecha_cumplimiento` date DEFAULT NULL,
  `fecha_inicio` datetime DEFAULT NULL,
  `fecha_completado` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `incidencias_bitacora`
--

CREATE TABLE `incidencias_bitacora` (
  `id` int(11) NOT NULL,
  `incidencia_id` int(11) NOT NULL,
  `usuario_id` int(11) NOT NULL,
  `accion` varchar(100) NOT NULL,
  `detalle` text DEFAULT NULL,
  `fecha_accion` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `inventario`
--

CREATE TABLE `inventario` (
  `id` int(11) NOT NULL,
  `mercancia_id` int(11) DEFAULT NULL,
  `producto_id` int(11) DEFAULT NULL,
  `producto` varchar(100) NOT NULL,
  `inventario_inicial` int(11) DEFAULT 0,
  `entradas` int(11) DEFAULT 0,
  `salidas` int(11) DEFAULT 0,
  `aprobado` tinyint(1) DEFAULT 0,
  `empresa_id` int(11) DEFAULT NULL,
  `disponible_base` decimal(12,3) DEFAULT 0.000
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `inventario`
--

INSERT INTO `inventario` (`id`, `mercancia_id`, `producto_id`, `producto`, `inventario_inicial`, `entradas`, `salidas`, `aprobado`, `empresa_id`, `disponible_base`) VALUES
(1, NULL, NULL, 'Hielo', 0, 1, 0, 0, NULL, 0.000),
(2, NULL, NULL, 'Nieve Chocolate', 0, 1, 0, 0, NULL, 0.000),
(3, NULL, NULL, 'Nieve Vainilla', 0, 1, 0, 0, NULL, 0.000),
(4, NULL, NULL, 'Cono Chocolate', 0, 1, 0, 0, NULL, 0.000),
(5, NULL, NULL, 'Gasolina', 0, 1, 0, 0, NULL, 0.000),
(9, 54, NULL, 'Fresa 1kg', 0, 1, 0, 0, NULL, 0.000),
(10, 55, NULL, '', 0, 0, 0, 0, 1, 0.000),
(11, 56, NULL, '', 0, 0, 0, 0, 1, 0.000),
(12, 57, NULL, '', 0, 0, 0, 0, 1, 0.000),
(13, 58, NULL, '', 0, 0, 0, 0, 1, 0.000),
(14, 59, NULL, '', 0, 0, 0, 0, 1, 0.000),
(15, 60, NULL, '', 0, 0, 0, 0, 1, 0.000),
(16, 61, NULL, '', 0, 0, 0, 0, 1, 0.000),
(17, 62, NULL, '', 0, 0, 0, 0, 1, 0.000),
(18, 63, NULL, '', 0, 0, 0, 0, 1, 0.000),
(19, 64, NULL, '', 0, 0, 0, 0, 1, 0.000),
(20, 65, NULL, '', 0, 0, 0, 0, 1, 0.000),
(21, 66, NULL, '', 0, 0, 0, 0, 1, 0.000);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `inventario_movimientos`
--

CREATE TABLE `inventario_movimientos` (
  `id` int(11) NOT NULL,
  `tipo_inventario_id` int(11) NOT NULL,
  `mercancia_id` int(11) NOT NULL,
  `fecha` date NOT NULL,
  `tipo_movimiento` enum('entrada','salida') NOT NULL,
  `unidades` decimal(10,2) NOT NULL,
  `precio_unitario` decimal(10,2) NOT NULL,
  `referencia` varchar(100) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `inventario_movimientos`
--

INSERT INTO `inventario_movimientos` (`id`, `tipo_inventario_id`, `mercancia_id`, `fecha`, `tipo_movimiento`, `unidades`, `precio_unitario`, `referencia`) VALUES
(2, 1, 54, '2025-09-03', '', 1.00, 615.00, '51');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `inventario_mp`
--

CREATE TABLE `inventario_mp` (
  `id` int(11) NOT NULL,
  `mercancia_id` int(11) NOT NULL,
  `producto` varchar(255) NOT NULL,
  `inventario_inicial` decimal(10,2) DEFAULT 0.00,
  `entradas` decimal(10,2) DEFAULT 0.00,
  `salidas` decimal(10,2) DEFAULT 0.00,
  `aprobado` tinyint(4) DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `inventario_pt`
--

CREATE TABLE `inventario_pt` (
  `id` int(11) NOT NULL,
  `producto_id` int(11) NOT NULL,
  `inventario_inicial` decimal(10,2) DEFAULT 0.00,
  `entradas` decimal(10,2) DEFAULT 0.00,
  `precio_unitario` decimal(10,2) DEFAULT NULL,
  `salidas` decimal(10,2) DEFAULT 0.00
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `invitaciones`
--

CREATE TABLE `invitaciones` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `correo` varchar(100) NOT NULL,
  `nombre_sugerido` varchar(100) DEFAULT NULL,
  `rol` varchar(50) DEFAULT 'operador',
  `areas_asignadas` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`areas_asignadas`)),
  `token` varchar(100) NOT NULL,
  `estado` enum('pendiente','aceptada','expirada','cancelada') DEFAULT 'pendiente',
  `creada_por` int(11) NOT NULL,
  `fecha_creacion` timestamp NOT NULL DEFAULT current_timestamp(),
  `fecha_expiracion` datetime DEFAULT NULL,
  `fecha_aceptacion` datetime DEFAULT NULL,
  `usuario_creado_id` int(11) DEFAULT NULL,
  `notas` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `listado_compras`
--

CREATE TABLE `listado_compras` (
  `id` int(11) NOT NULL,
  `fecha` datetime DEFAULT NULL,
  `numero_factura` varchar(50) DEFAULT NULL,
  `proveedor` varchar(255) DEFAULT NULL,
  `total` decimal(10,2) DEFAULT NULL,
  `empresa_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `listado_compras`
--

INSERT INTO `listado_compras` (`id`, `fecha`, `numero_factura`, `proveedor`, `total`, `empresa_id`) VALUES
(37, '2025-08-01 00:00:00', '75930', 'Del Rio', 34.00, NULL),
(38, '2025-08-01 00:00:00', '45573', 'Vani', 1990.00, NULL),
(39, '2025-08-01 00:00:00', '1708825', 'Gazpro', 379.80, NULL);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `mercancia`
--

CREATE TABLE `mercancia` (
  `id` int(11) NOT NULL,
  `nombre` varchar(255) NOT NULL,
  `precio` decimal(10,2) NOT NULL DEFAULT 0.00,
  `unidad_id` int(11) DEFAULT NULL,
  `cont_neto` varchar(50) DEFAULT NULL,
  `cuenta_id` int(11) DEFAULT NULL,
  `subcuenta_id` int(11) DEFAULT NULL,
  `iva` tinyint(1) DEFAULT 0,
  `ieps` tinyint(1) DEFAULT 0,
  `graba_iva` tinyint(1) DEFAULT 0,
  `graba_ieps` tinyint(1) DEFAULT 0,
  `empresa_id` int(11) DEFAULT NULL,
  `tipo` enum('MP','WIP','PT') DEFAULT 'MP',
  `precio_venta` decimal(10,2) DEFAULT 0.00,
  `unidad_base` varchar(20) DEFAULT 'pz',
  `activo` tinyint(1) DEFAULT 1,
  `catalogo_id` int(11) DEFAULT NULL,
  `producto_base_id` int(11) DEFAULT NULL,
  `minimo_existencia` decimal(10,2) DEFAULT 0.00,
  `maximo_existencia` decimal(10,2) DEFAULT 0.00,
  `tipo_inventario_id` int(11) DEFAULT NULL,
  `orden` int(11) DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `mercancia`
--

INSERT INTO `mercancia` (`id`, `nombre`, `precio`, `unidad_id`, `cont_neto`, `cuenta_id`, `subcuenta_id`, `iva`, `ieps`, `graba_iva`, `graba_ieps`, `empresa_id`, `tipo`, `precio_venta`, `unidad_base`, `activo`, `catalogo_id`, `producto_base_id`, `minimo_existencia`, `maximo_existencia`, `tipo_inventario_id`, `orden`) VALUES
(32, 'Azucar 2kg', 0.00, 3, '2000', 6, 7, 0, 0, 0, 0, NULL, 'MP', 0.00, 'pz', 1, NULL, NULL, 0.00, 0.00, NULL, 0),
(33, 'Azucar 5kg', 0.00, 3, '5000', 6, 107, 0, 0, 0, 0, NULL, 'MP', 0.00, 'pz', 1, NULL, NULL, 0.00, 0.00, NULL, 0),
(35, 'Producto Prueba', 0.00, 1, '1.00', NULL, NULL, 0, 0, 0, 0, NULL, 'MP', 0.00, 'pz', 1, NULL, NULL, 0.00, 0.00, NULL, 0),
(36, 'Materia Prima Test', 0.00, 1, '100', NULL, NULL, 0, 0, 0, 0, NULL, 'MP', 0.00, 'pz', 1, NULL, NULL, 0.00, 0.00, NULL, 0),
(38, 'Hielo', 0.00, 3, '5000', 6, 110, 0, 0, 0, 0, NULL, 'MP', 0.00, 'pz', 1, NULL, NULL, 0.00, 0.00, NULL, 0),
(39, 'Gasolina', 0.00, 2, '1', NULL, 74, 0, 0, 0, 0, NULL, 'MP', 0.00, 'pz', 1, NULL, NULL, 0.00, 0.00, NULL, 0),
(40, 'Azucar 1 kg', 0.00, 3, '1000', 6, 112, 0, 0, 0, 0, NULL, 'MP', 0.00, 'pz', 1, NULL, NULL, 0.00, 0.00, NULL, 0),
(41, 'Cacahuate', 0.00, 3, '1000', 6, 113, 0, 0, 0, 0, NULL, 'MP', 0.00, 'pz', 1, NULL, NULL, 0.00, 0.00, NULL, 0),
(42, 'Cajeta 1kg', 0.00, 3, '1000', 6, 114, 0, 0, 0, 0, NULL, 'MP', 0.00, 'pz', 1, NULL, NULL, 0.00, 0.00, NULL, 0),
(43, 'Cajeta 5kg', 0.00, 3, '5000', 6, 115, 0, 0, 0, 0, NULL, 'MP', 0.00, 'pz', 1, NULL, NULL, 0.00, 0.00, NULL, 0),
(47, 'Cono Waffle', 0.00, 1, '125', 6, 116, 0, 1, 0, 0, NULL, 'MP', 0.00, 'pz', 1, NULL, NULL, 0.00, 0.00, NULL, 0),
(48, 'Cono Chocolate', 0.00, 1, '360', 6, 117, 0, 0, 0, 0, NULL, 'MP', 0.00, 'pz', 1, NULL, NULL, 0.00, 0.00, NULL, 0),
(49, 'IEPS', 0.00, 1, '1', NULL, 86, 0, 0, 0, 0, NULL, 'MP', 0.00, 'pz', 1, NULL, NULL, 0.00, 0.00, NULL, 0),
(50, 'IVA', 0.00, 1, '1', NULL, 109, 0, 0, 0, 0, NULL, 'MP', 0.00, 'pz', 1, NULL, NULL, 0.00, 0.00, NULL, 0),
(51, 'Harina para Brownies 3.4kg', 0.00, 3, '3400', 6, 120, 1, 0, 0, 0, NULL, 'MP', 0.00, 'pz', 1, NULL, NULL, 0.00, 0.00, NULL, 0),
(52, 'Harina para Brownies 2.26kg', 0.00, 3, '2260', 6, 121, 1, 0, 0, 0, NULL, 'MP', 0.00, 'pz', 1, NULL, NULL, 0.00, 0.00, NULL, 0),
(53, 'Cacahuate', 0.00, 3, '1000', 6, 113, 0, 0, 0, 0, NULL, 'MP', 0.00, 'pz', 1, NULL, NULL, 0.00, 0.00, NULL, 0),
(54, 'Fresa 1kg', 0.00, 3, '1000', 6, 122, 0, 0, 0, 0, NULL, 'MP', 0.00, 'pz', 1, NULL, NULL, 0.00, 0.00, NULL, 0),
(55, 'Cono Oblea', 0.00, 1, '1', NULL, NULL, 0, 0, 0, 0, 1, 'PT', 0.00, 'pz', 1, NULL, NULL, 0.00, 0.00, 3, 0),
(56, 'Cono Galleta', 0.00, 1, '1', NULL, NULL, 0, 0, 0, 0, 1, 'PT', 0.00, 'pz', 1, NULL, NULL, 0.00, 0.00, 3, 0),
(57, 'Cono Choco', 0.00, 1, '1', NULL, NULL, 0, 0, 0, 0, 1, 'PT', 0.00, 'pz', 1, NULL, NULL, 0.00, 0.00, 3, 0),
(58, 'Cono Wafle', 0.00, 1, '1', NULL, NULL, 0, 0, 0, 0, 1, 'PT', 0.00, 'pz', 1, NULL, NULL, 0.00, 0.00, 3, 0),
(59, 'Vaso Chocoice', 0.00, 1, '1', NULL, NULL, 0, 0, 0, 0, 1, 'PT', 0.00, 'pz', 1, NULL, NULL, 0.00, 0.00, 3, 0),
(60, 'Vaso Frappe', 0.00, 1, '1', NULL, NULL, 0, 0, 0, 0, 1, 'PT', 0.00, 'pz', 1, NULL, NULL, 0.00, 0.00, 3, 0),
(61, 'Sodas', 0.00, 1, '1', NULL, NULL, 0, 0, 0, 0, 1, 'PT', 0.00, 'pz', 1, NULL, NULL, 0.00, 0.00, 3, 0),
(62, 'Agua 500ml', 0.00, 1, '1', NULL, NULL, 0, 0, 0, 0, 1, 'PT', 0.00, 'pz', 1, NULL, NULL, 0.00, 0.00, 3, 0),
(63, 'Brownie', 0.00, 1, '1', NULL, NULL, 0, 0, 0, 0, 1, 'PT', 0.00, 'pz', 1, NULL, NULL, 0.00, 0.00, 3, 0),
(64, 'Vaso Malteada 16oz', 0.00, 1, '1', NULL, NULL, 0, 0, 0, 0, 1, 'PT', 0.00, 'pz', 1, NULL, NULL, 0.00, 0.00, 3, 0),
(65, 'Churro relleno', 0.00, 1, '1', NULL, NULL, 0, 0, 0, 0, 1, 'PT', 0.00, 'pz', 1, NULL, NULL, 0.00, 0.00, 3, 0),
(66, 'Fresa', 0.00, 1, '1', NULL, NULL, 0, 0, 0, 0, 1, 'PT', 0.00, 'pz', 1, NULL, NULL, 0.00, 0.00, 3, 0);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `mermas`
--

CREATE TABLE `mermas` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `registro_id` int(11) DEFAULT NULL,
  `fecha` date NOT NULL,
  `producto_id` int(11) NOT NULL,
  `producto_nombre` varchar(255) DEFAULT NULL,
  `cantidad` decimal(10,3) NOT NULL DEFAULT 1.000,
  `costo_unitario` decimal(12,2) DEFAULT 0.00,
  `costo_total` decimal(12,2) DEFAULT 0.00,
  `motivo` enum('caducado','da?ado','perdido','robo','otro') DEFAULT 'otro',
  `descripcion` varchar(255) DEFAULT NULL,
  `usuario_id` int(11) DEFAULT NULL,
  `fecha_registro` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `movimientos_inventario`
--

CREATE TABLE `movimientos_inventario` (
  `id` int(11) NOT NULL,
  `contratante_id` int(11) NOT NULL,
  `mercancia_id` int(11) DEFAULT NULL,
  `producto_id` int(11) DEFAULT NULL,
  `tipo` enum('entrada','salida') NOT NULL,
  `cantidad` decimal(12,2) NOT NULL,
  `costo_unitario` decimal(12,2) NOT NULL,
  `referencia` varchar(255) DEFAULT NULL,
  `fecha` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `movimientos_inventario`
--

INSERT INTO `movimientos_inventario` (`id`, `contratante_id`, `mercancia_id`, `producto_id`, `tipo`, `cantidad`, `costo_unitario`, `referencia`, `fecha`) VALUES
(4, 1, 35, NULL, 'entrada', 10.00, 0.00, NULL, '2025-08-16 01:26:31'),
(9, 1, 36, NULL, 'entrada', 50.00, 12.50, NULL, '2025-08-17 02:57:31'),
(10, 1, 36, NULL, 'salida', 10.00, 12.50, NULL, '2025-08-17 02:57:47'),
(11, 1, NULL, 3, 'entrada', 20.00, 0.00, NULL, '2025-08-17 02:58:01'),
(12, 1, NULL, 3, 'salida', 5.00, 0.00, NULL, '2025-08-17 02:58:14'),
(13, 1, NULL, 3, 'salida', 5.00, 0.00, NULL, '2025-08-17 03:01:23'),
(14, 1, 36, NULL, 'entrada', 50.00, 12.50, NULL, '2025-08-17 03:01:41'),
(15, 1, 36, NULL, 'salida', 10.00, 12.50, NULL, '2025-08-17 03:01:56'),
(16, 1, NULL, 3, 'entrada', 50.00, 20.00, 'Producci?n Lote 001', '2025-08-18 04:53:21'),
(17, 1, NULL, 3, 'salida', 10.00, 20.00, 'Venta Cliente X', '2025-08-18 04:53:46'),
(18, 1, NULL, 1, 'entrada', 50.00, 20.00, 'Producci?n Lote 001', '2025-08-18 05:03:19'),
(19, 1, NULL, 3, 'entrada', 50.00, 20.00, 'Producci?n Lote Test', '2025-08-19 16:29:33');

--
-- Disparadores `movimientos_inventario`
--
DELIMITER $$
CREATE TRIGGER `trg_contable_pt` AFTER INSERT ON `movimientos_inventario` FOR EACH ROW BEGIN
    
    IF NEW.producto_id IS NOT NULL THEN

        
        IF NEW.tipo = 'entrada' THEN
            INSERT INTO asientos_contables (descripcion, cuenta_debe, cuenta_haber, monto, producto_id)
            SELECT 
                CONCAT('Entrada PT - ', p.nombre),
                p.cuenta_id,      
                p.subcuenta_id,   
                NEW.cantidad * NEW.costo_unitario,
                NEW.producto_id
            FROM productos_terminados p
            WHERE p.id = NEW.producto_id;
        END IF;

        
        IF NEW.tipo = 'salida' THEN
            INSERT INTO asientos_contables (descripcion, cuenta_debe, cuenta_haber, monto, producto_id)
            SELECT 
                CONCAT('Salida PT - ', p.nombre),
                5001,             
                p.cuenta_id,      
                NEW.cantidad * NEW.costo_unitario,
                NEW.producto_id
            FROM productos_terminados p
            WHERE p.id = NEW.producto_id;
        END IF;

    END IF;
END
$$
DELIMITER ;
DELIMITER $$
CREATE TRIGGER `trg_mov_inventario_entrada` AFTER INSERT ON `movimientos_inventario` FOR EACH ROW BEGIN
    
    IF NEW.tipo = 'entrada' AND NEW.mercancia_id IS NOT NULL THEN
        INSERT INTO inventario (mercancia_id, entradas, salidas)
        VALUES (NEW.mercancia_id, NEW.cantidad, 0)
        ON DUPLICATE KEY UPDATE entradas = entradas + NEW.cantidad;
    END IF;

    
    IF NEW.tipo = 'entrada' AND NEW.producto_id IS NOT NULL THEN
        INSERT INTO inventario (producto_id, entradas, salidas)
        VALUES (NEW.producto_id, NEW.cantidad, 0)
        ON DUPLICATE KEY UPDATE entradas = entradas + NEW.cantidad;
    END IF;
END
$$
DELIMITER ;
DELIMITER $$
CREATE TRIGGER `trg_mov_inventario_salida` AFTER INSERT ON `movimientos_inventario` FOR EACH ROW BEGIN
    
    IF NEW.tipo = 'salida' AND NEW.mercancia_id IS NOT NULL THEN
        INSERT INTO inventario (mercancia_id, entradas, salidas)
        VALUES (NEW.mercancia_id, 0, NEW.cantidad)
        ON DUPLICATE KEY UPDATE salidas = salidas + NEW.cantidad;
    END IF;

    
    IF NEW.tipo = 'salida' AND NEW.producto_id IS NOT NULL THEN
        INSERT INTO inventario (producto_id, entradas, salidas)
        VALUES (NEW.producto_id, 0, NEW.cantidad)
        ON DUPLICATE KEY UPDATE salidas = salidas + NEW.cantidad;
    END IF;
END
$$
DELIMITER ;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `notificaciones`
--

CREATE TABLE `notificaciones` (
  `id` int(11) NOT NULL,
  `usuario_id` int(11) NOT NULL,
  `tipo` enum('tarea_asignada','tarea_vencida','tarea_completada','aprobacion_requerida','tarea_rechazada','comentario','otro') NOT NULL,
  `titulo` varchar(255) NOT NULL,
  `mensaje` text NOT NULL,
  `url` varchar(500) DEFAULT NULL,
  `leida` tinyint(1) DEFAULT 0,
  `fecha_creacion` datetime DEFAULT current_timestamp(),
  `fecha_lectura` datetime DEFAULT NULL,
  `referencia_tipo` varchar(50) DEFAULT NULL,
  `referencia_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `notificaciones_usuario`
--

CREATE TABLE `notificaciones_usuario` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `usuario_destino_id` int(11) NOT NULL,
  `usuario_origen_id` int(11) DEFAULT NULL,
  `tipo` enum('bienvenida','asignacion','alerta','mensaje','sistema') DEFAULT 'mensaje',
  `titulo` varchar(200) NOT NULL,
  `mensaje` text DEFAULT NULL,
  `referencia_tipo` varchar(50) DEFAULT NULL,
  `referencia_id` int(11) DEFAULT NULL,
  `leida` tinyint(1) DEFAULT 0,
  `fecha_lectura` datetime DEFAULT NULL,
  `importante` tinyint(1) DEFAULT 0,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `ordenes_compra_automaticas`
--

CREATE TABLE `ordenes_compra_automaticas` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `folio` varchar(30) NOT NULL,
  `fecha_generacion` datetime NOT NULL DEFAULT current_timestamp(),
  `tipo_orden` enum('automatica','manual') DEFAULT 'automatica',
  `estado` varchar(30) DEFAULT 'pendiente_revision',
  `solicitado_por` varchar(50) DEFAULT 'SISTEMA',
  `revisado_por_usuario_id` int(11) DEFAULT NULL,
  `fecha_revision` datetime DEFAULT NULL,
  `aprobado_por_usuario_id` int(11) DEFAULT NULL,
  `fecha_aprobacion` datetime DEFAULT NULL,
  `notas_revision` text DEFAULT NULL,
  `notas_rechazo` text DEFAULT NULL,
  `subtotal` decimal(12,2) DEFAULT 0.00,
  `iva` decimal(12,2) DEFAULT 0.00,
  `total` decimal(12,2) DEFAULT 0.00,
  `fecha_creacion` datetime DEFAULT current_timestamp(),
  `fecha_actualizacion` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `ordenes_compra_automaticas_detalle`
--

CREATE TABLE `ordenes_compra_automaticas_detalle` (
  `id` int(11) NOT NULL,
  `orden_id` int(11) NOT NULL,
  `mercancia_id` int(11) NOT NULL,
  `producto_base_id` int(11) DEFAULT NULL,
  `descripcion` varchar(500) DEFAULT NULL,
  `cantidad_solicitada` decimal(12,3) NOT NULL,
  `cantidad_aprobada` decimal(12,3) DEFAULT NULL,
  `cantidad_recibida` decimal(12,3) DEFAULT 0.000,
  `precio_estimado` decimal(12,2) DEFAULT 0.00,
  `importe` decimal(12,2) DEFAULT 0.00,
  `criterio` varchar(100) DEFAULT NULL,
  `stock_actual` decimal(12,3) DEFAULT NULL,
  `stock_minimo` decimal(12,3) DEFAULT NULL,
  `stock_maximo` decimal(12,3) DEFAULT NULL,
  `fecha_primera_solicitud` datetime DEFAULT NULL,
  `dias_pendiente` int(11) DEFAULT 0,
  `estado` varchar(30) DEFAULT 'pendiente',
  `proveedor_sugerido_id` int(11) DEFAULT NULL,
  `notas` text DEFAULT NULL,
  `fecha_creacion` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `ordenes_compra_b2b`
--

CREATE TABLE `ordenes_compra_b2b` (
  `id` int(11) NOT NULL,
  `empresa_cliente_id` int(11) NOT NULL,
  `empresa_proveedor_id` int(11) NOT NULL,
  `turno_id` int(11) DEFAULT NULL,
  `folio` varchar(30) NOT NULL,
  `fecha_solicitud` datetime NOT NULL DEFAULT current_timestamp(),
  `subtotal` decimal(12,2) DEFAULT 0.00,
  `iva` decimal(12,2) DEFAULT 0.00,
  `total` decimal(12,2) DEFAULT 0.00,
  `estado` varchar(30) DEFAULT 'borrador',
  `solicitado_por_usuario_id` int(11) DEFAULT NULL,
  `aprobado_por_usuario_id` int(11) DEFAULT NULL,
  `fecha_aprobacion` datetime DEFAULT NULL,
  `notas` text DEFAULT NULL,
  `notas_rechazo` text DEFAULT NULL,
  `fecha_creacion` datetime DEFAULT current_timestamp(),
  `fecha_actualizacion` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `ordenes_compra_b2b_detalle`
--

CREATE TABLE `ordenes_compra_b2b_detalle` (
  `id` int(11) NOT NULL,
  `orden_id` int(11) NOT NULL,
  `mercancia_id` int(11) DEFAULT NULL,
  `descripcion` varchar(500) NOT NULL,
  `cantidad_solicitada` decimal(12,3) NOT NULL,
  `cantidad_aprobada` decimal(12,3) DEFAULT NULL,
  `precio_unitario` decimal(12,2) NOT NULL DEFAULT 0.00,
  `importe` decimal(12,2) NOT NULL DEFAULT 0.00,
  `notas` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `ordenes_compra_tracking`
--

CREATE TABLE `ordenes_compra_tracking` (
  `id` int(11) NOT NULL,
  `detalle_id` int(11) NOT NULL,
  `fecha` datetime DEFAULT current_timestamp(),
  `estado_anterior` varchar(30) DEFAULT NULL,
  `estado_nuevo` varchar(30) DEFAULT NULL,
  `cantidad_anterior` decimal(12,3) DEFAULT NULL,
  `cantidad_nueva` decimal(12,3) DEFAULT NULL,
  `usuario_id` int(11) DEFAULT NULL,
  `notas` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `ordenes_produccion`
--

CREATE TABLE `ordenes_produccion` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `proceso_id` int(11) NOT NULL,
  `codigo` varchar(50) DEFAULT NULL,
  `cantidad_solicitada` decimal(10,3) NOT NULL,
  `cantidad_producida` decimal(10,3) DEFAULT 0.000,
  `estado` enum('borrador','pendiente','en_proceso','pausada','completada','cancelada') DEFAULT 'borrador',
  `fecha_solicitud` date DEFAULT NULL,
  `fecha_inicio` datetime DEFAULT NULL,
  `fecha_fin` datetime DEFAULT NULL,
  `prioridad` enum('baja','normal','alta','urgente') DEFAULT 'normal',
  `notas` text DEFAULT NULL,
  `creado_por` int(11) DEFAULT NULL,
  `fecha_creacion` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `orden_mp`
--

CREATE TABLE `orden_mp` (
  `id` bigint(20) NOT NULL,
  `orden_id` bigint(20) NOT NULL,
  `mp_mercancia_id` int(11) NOT NULL,
  `unidades` decimal(14,4) NOT NULL,
  `empresa_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `orden_produccion`
--

CREATE TABLE `orden_produccion` (
  `id` bigint(20) NOT NULL,
  `fecha` datetime NOT NULL DEFAULT current_timestamp(),
  `pt_mercancia_id` int(11) NOT NULL,
  `cantidad` decimal(14,4) NOT NULL,
  `estado` enum('abierta','cerrada') NOT NULL DEFAULT 'abierta',
  `referencia` varchar(100) DEFAULT NULL,
  `empresa_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `pagos_b2b`
--

CREATE TABLE `pagos_b2b` (
  `id` int(11) NOT NULL,
  `tipo` varchar(20) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `cuenta_por_pagar_id` int(11) DEFAULT NULL,
  `cuenta_por_cobrar_id` int(11) DEFAULT NULL,
  `factura_b2b_id` int(11) DEFAULT NULL,
  `monto` decimal(12,2) NOT NULL,
  `metodo_pago` varchar(50) DEFAULT NULL,
  `referencia_pago` varchar(100) DEFAULT NULL,
  `usuario_id` int(11) DEFAULT NULL,
  `fecha_pago` datetime NOT NULL,
  `fecha_registro` datetime DEFAULT current_timestamp(),
  `notas` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `paso_insumos`
--

CREATE TABLE `paso_insumos` (
  `id` int(11) NOT NULL,
  `paso_id` int(11) NOT NULL,
  `mercancia_id` int(11) NOT NULL,
  `cantidad` decimal(12,3) NOT NULL,
  `unidad_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `paso_responsables`
--

CREATE TABLE `paso_responsables` (
  `id` int(11) NOT NULL,
  `paso_id` int(11) NOT NULL,
  `usuario_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `presentaciones`
--

CREATE TABLE `presentaciones` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) DEFAULT NULL,
  `mercancia_id` int(11) DEFAULT NULL,
  `descripcion` varchar(255) DEFAULT NULL,
  `contenido_neto` varchar(50) DEFAULT NULL,
  `unidad` varchar(50) DEFAULT NULL,
  `factor_conversion` decimal(10,4) DEFAULT 1.0000
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `procesos`
--

CREATE TABLE `procesos` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `nombre` varchar(255) NOT NULL,
  `descripcion` text DEFAULT NULL,
  `producto_terminado_id` int(11) DEFAULT NULL,
  `producto_wip_id` int(11) DEFAULT NULL,
  `cantidad_producida` decimal(10,3) DEFAULT 1.000,
  `unidad_produccion_id` int(11) DEFAULT NULL,
  `activo` tinyint(1) DEFAULT 1,
  `areas_involucradas` text DEFAULT NULL,
  `responsables` text DEFAULT NULL,
  `materiales` text DEFAULT NULL,
  `costo_estimado` decimal(12,2) DEFAULT 0.00,
  `fecha_creacion` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `proceso_pasos`
--

CREATE TABLE `proceso_pasos` (
  `id` int(11) NOT NULL,
  `proceso_id` int(11) NOT NULL,
  `numero_paso` int(11) NOT NULL,
  `nombre` varchar(255) NOT NULL,
  `descripcion` text DEFAULT NULL,
  `area_id` int(11) DEFAULT NULL,
  `tiempo_estimado` int(11) DEFAULT 0,
  `costo_mano_obra` decimal(10,2) DEFAULT 0.00,
  `activo` tinyint(1) DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `produccion`
--

CREATE TABLE `produccion` (
  `id` int(11) NOT NULL,
  `fecha` date NOT NULL,
  `producto_terminado_id` int(11) NOT NULL,
  `cantidad_producida` decimal(10,2) NOT NULL,
  `estado` enum('en_proceso','terminado') DEFAULT 'en_proceso',
  `empresa_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `produccion_detalle_mp`
--

CREATE TABLE `produccion_detalle_mp` (
  `id` int(11) NOT NULL,
  `produccion_id` int(11) NOT NULL,
  `mercancia_id` int(11) NOT NULL,
  `cantidad_usada` decimal(10,2) NOT NULL,
  `empresa_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `productos_terminados`
--

CREATE TABLE `productos_terminados` (
  `id` int(11) NOT NULL,
  `nombre` varchar(255) NOT NULL,
  `descripcion` text DEFAULT NULL,
  `unidad_id` int(11) DEFAULT NULL,
  `cont_neto` decimal(10,2) DEFAULT NULL,
  `cuenta_id` int(11) DEFAULT NULL,
  `subcuenta_id` int(11) DEFAULT NULL,
  `unidad_medida` varchar(50) DEFAULT NULL,
  `precio_venta` decimal(10,2) DEFAULT 0.00
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `productos_terminados`
--

INSERT INTO `productos_terminados` (`id`, `nombre`, `descripcion`, `unidad_id`, `cont_neto`, `cuenta_id`, `subcuenta_id`, `unidad_medida`, `precio_venta`) VALUES
(1, 'Producto Trigger Test', 'Verificar inventario', 1, 25.00, NULL, NULL, NULL, 0.00),
(2, 'Producto Trigger Test', 'Creado para prueba de inventario', 1, 25.00, NULL, NULL, NULL, 0.00),
(3, 'Producto Terminado Test', 'Para prueba', 1, 50.00, NULL, NULL, NULL, 0.00);

--
-- Disparadores `productos_terminados`
--
DELIMITER $$
CREATE TRIGGER `trg_pt_to_inventario` AFTER INSERT ON `productos_terminados` FOR EACH ROW BEGIN
     INSERT IGNORE INTO inventario (producto_id, producto, inventario_inicial, entradas, salidas, aprobado)
     VALUES (NEW.id, NEW.nombre, 0, 0, 0, 0);
END
$$
DELIMITER ;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `producto_base`
--

CREATE TABLE `producto_base` (
  `id` int(11) NOT NULL,
  `nombre` varchar(255) NOT NULL,
  `activo` tinyint(1) DEFAULT 1,
  `minimo_existencia` decimal(10,2) DEFAULT 0.00,
  `empresa_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `proveedores`
--

CREATE TABLE `proveedores` (
  `id` int(11) NOT NULL,
  `contratante_id` int(11) NOT NULL,
  `nombre` varchar(255) NOT NULL,
  `direccion` varchar(255) DEFAULT NULL,
  `ciudad` varchar(100) DEFAULT NULL,
  `telefono` varchar(50) DEFAULT NULL,
  `empresa_id` int(11) DEFAULT NULL,
  `activo` tinyint(1) DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `proveedores`
--

INSERT INTO `proveedores` (`id`, `contratante_id`, `nombre`, `direccion`, `ciudad`, `telefono`, `empresa_id`, `activo`) VALUES
(1, 1, 'El Loco Jr', 'Ave Mariscal', 'Ciudad Juarez Chih', '6566121866', NULL, 1),
(2, 1, 'Vani', 'Gral Jose Trinidad', 'Ciudad Juarez Chih', '656 626 9313', NULL, 1),
(3, 1, 'SAMS Juarez', 'Ave Ejercito Nacional', 'Ciudad Juarez Chih', '800', NULL, 1),
(4, 1, 'Trevly', 'Calle Apolo 1050', 'Ciudad Juarez Chih', '656 311 2760', NULL, 1);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `pt_precios`
--

CREATE TABLE `pt_precios` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) DEFAULT NULL,
  `producto_id` int(11) DEFAULT NULL,
  `precio` decimal(10,2) DEFAULT 0.00,
  `precio_especial` decimal(10,2) DEFAULT 0.00,
  `activo` tinyint(1) DEFAULT 1,
  `precio_manual` decimal(10,2) DEFAULT 0.00,
  `mercancia_id` int(11) DEFAULT NULL,
  `modo` varchar(50) DEFAULT 'manual',
  `markup_pct` decimal(5,2) DEFAULT 0.00,
  `costo_base` decimal(10,2) DEFAULT 0.00,
  `precio_calculado` decimal(10,2) DEFAULT 0.00,
  `fecha_actualizacion` datetime DEFAULT current_timestamp(),
  `alias` varchar(100) DEFAULT NULL,
  `orden` int(11) DEFAULT 0,
  `visible` tinyint(1) DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `pt_precios`
--

INSERT INTO `pt_precios` (`id`, `empresa_id`, `producto_id`, `precio`, `precio_especial`, `activo`, `precio_manual`, `mercancia_id`, `modo`, `markup_pct`, `costo_base`, `precio_calculado`, `fecha_actualizacion`, `alias`, `orden`, `visible`) VALUES
(1, NULL, NULL, 0.00, 0.00, 1, 0.00, 55, 'manual', 0.30, 0.00, 0.00, '2025-12-03 22:37:54', NULL, 0, 1),
(2, NULL, NULL, 0.00, 0.00, 1, 0.00, 56, 'manual', 0.30, 0.00, 0.00, '2025-12-03 22:38:01', NULL, 0, 1),
(3, NULL, NULL, 0.00, 0.00, 1, 0.00, 57, 'manual', 0.30, 0.00, 0.00, '2025-12-03 22:38:10', NULL, 0, 1),
(4, NULL, NULL, 0.00, 0.00, 1, 0.00, 58, 'manual', 0.30, 0.00, 0.00, '2025-12-03 22:38:18', NULL, 0, 1),
(5, NULL, NULL, 0.00, 0.00, 1, 0.00, 59, 'manual', 0.30, 0.00, 0.00, '2025-12-03 22:38:32', NULL, 0, 1),
(6, NULL, NULL, 0.00, 0.00, 1, 0.00, 60, 'manual', 0.30, 0.00, 0.00, '2025-12-03 22:38:46', NULL, 0, 1),
(7, NULL, NULL, 0.00, 0.00, 1, 0.00, 61, 'manual', 0.30, 0.00, 0.00, '2025-12-03 22:38:49', NULL, 0, 1),
(8, NULL, NULL, 0.00, 0.00, 1, 0.00, 62, 'manual', 0.30, 0.00, 0.00, '2025-12-03 22:38:55', NULL, 0, 1),
(9, NULL, NULL, 0.00, 0.00, 1, 0.00, 63, 'manual', 0.30, 0.00, 0.00, '2025-12-03 22:39:02', NULL, 0, 1),
(10, NULL, NULL, 0.00, 0.00, 1, 0.00, 64, 'manual', 0.30, 0.00, 0.00, '2025-12-03 22:39:08', NULL, 0, 1),
(11, NULL, NULL, 0.00, 0.00, 1, 0.00, 65, 'manual', 0.30, 0.00, 0.00, '2025-12-03 22:39:17', NULL, 0, 1),
(12, NULL, NULL, 0.00, 0.00, 1, 0.00, 66, 'manual', 0.30, 0.00, 0.00, '2025-12-03 22:39:26', NULL, 0, 1),
(25, 1, NULL, 0.00, 0.00, 1, 8.00, 62, 'manual', 0.30, 0.00, 0.00, '2025-12-03 23:50:01', 'Agua individual', 0, 1),
(26, 1, NULL, 0.00, 0.00, 1, 58.00, 63, 'manual', 0.30, 0.00, 0.00, '2025-12-03 23:50:01', 'Brownie', 0, 1),
(27, 1, NULL, 0.00, 0.00, 1, 22.00, 65, 'manual', 0.30, 0.00, 0.00, '2025-12-03 23:50:01', 'Churro Relleno', 0, 1),
(28, 1, NULL, 0.00, 0.00, 1, 16.00, 57, 'manual', 0.30, 0.00, 0.00, '2025-12-03 23:50:01', 'Cono Choco', 0, 1),
(29, 1, NULL, 0.00, 0.00, 1, 18.00, 56, 'manual', 0.30, 0.00, 0.00, '2025-12-03 23:50:01', 'Cono Galleta', 0, 1),
(30, 1, NULL, 0.00, 0.00, 1, 15.00, 55, 'manual', 0.30, 0.00, 0.00, '2025-12-03 23:50:01', 'Cono Oblea', 0, 1),
(31, 1, NULL, 0.00, 0.00, 1, 27.00, 58, 'manual', 0.30, 0.00, 0.00, '2025-12-03 23:50:01', 'Cono Waffle', 0, 1),
(32, 1, NULL, 0.00, 0.00, 1, 68.00, 66, 'manual', 0.30, 0.00, 0.00, '2025-12-03 23:50:01', 'Fresas Con Crema', 0, 1),
(33, 1, NULL, 0.00, 0.00, 1, 22.00, 61, 'manual', 0.30, 0.00, 0.00, '2025-12-03 23:50:01', 'Soda de Bote', 0, 1),
(34, 1, NULL, 0.00, 0.00, 1, 42.00, 59, 'manual', 0.30, 0.00, 0.00, '2025-12-03 23:50:01', 'Chocoice', 0, 1),
(35, 1, NULL, 0.00, 0.00, 1, 65.00, 60, 'manual', 0.30, 0.00, 0.00, '2025-12-03 23:50:01', 'Frappe', 0, 1),
(36, 1, NULL, 0.00, 0.00, 1, 68.00, 64, 'manual', 0.30, 0.00, 0.00, '2025-12-03 23:50:01', 'Malteada', 0, 1);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `pt_reglas_markup`
--

CREATE TABLE `pt_reglas_markup` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) DEFAULT NULL,
  `costo_min` decimal(12,2) DEFAULT 0.00,
  `costo_max` decimal(12,2) DEFAULT 9999999.00,
  `markup_pct` decimal(5,2) DEFAULT 0.30,
  `descripcion` varchar(100) DEFAULT NULL,
  `activo` tinyint(1) DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `rangos_organizacionales`
--

CREATE TABLE `rangos_organizacionales` (
  `id` int(11) NOT NULL,
  `nombre` varchar(50) NOT NULL,
  `nivel` int(11) NOT NULL,
  `descripcion` text DEFAULT NULL,
  `puede_crear_usuarios` tinyint(1) DEFAULT 0,
  `puede_editar_configuracion` tinyint(1) DEFAULT 0,
  `puede_ver_reportes_consolidados` tinyint(1) DEFAULT 0
) ;

--
-- Volcado de datos para la tabla `rangos_organizacionales`
--

INSERT INTO `rangos_organizacionales` (`id`, `nombre`, `nivel`, `descripcion`, `puede_crear_usuarios`, `puede_editar_configuracion`, `puede_ver_reportes_consolidados`) VALUES
(1, 'Director General', 1, 'M?xima autoridad del contratante', 1, 1, 1),
(2, 'Gerente', 2, 'Gerente de ?rea o sucursal', 1, 1, 1),
(3, 'Jefe de Departamento', 3, 'Jefe de departamento espec?fico', 0, 0, 0),
(4, 'Empleado', 4, 'Personal operativo', 0, 0, 0);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `registros_diarios`
--

CREATE TABLE `registros_diarios` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `fecha` date NOT NULL,
  `usuario_id` int(11) DEFAULT NULL,
  `notas` text DEFAULT NULL,
  `cerrado` tinyint(1) DEFAULT 0,
  `fecha_registro` datetime DEFAULT current_timestamp(),
  `fecha_cierre` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `registros_diarios`
--

INSERT INTO `registros_diarios` (`id`, `empresa_id`, `fecha`, `usuario_id`, `notas`, `cerrado`, `fecha_registro`, `fecha_cierre`) VALUES
(1, 1, '2025-12-01', 13, NULL, 0, '2025-12-03 22:22:58', NULL),
(2, 1, '2025-11-01', 13, NULL, 0, '2025-12-03 22:23:29', NULL),
(3, 1, '2025-12-04', 13, NULL, 0, '2025-12-04 22:00:04', NULL);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `relaciones_b2b`
--

CREATE TABLE `relaciones_b2b` (
  `id` int(11) NOT NULL,
  `empresa_proveedor_id` int(11) NOT NULL,
  `empresa_cliente_id` int(11) NOT NULL,
  `activa` tinyint(1) DEFAULT 1,
  `dias_credito` int(11) DEFAULT 0,
  `limite_credito` decimal(12,2) DEFAULT 0.00,
  `descuento_default` decimal(5,2) DEFAULT 0.00,
  `fecha_inicio` date DEFAULT NULL,
  `fecha_creacion` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `retiros_efectivo`
--

CREATE TABLE `retiros_efectivo` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) DEFAULT NULL,
  `turno_id` int(11) NOT NULL,
  `fecha` datetime NOT NULL,
  `monto` decimal(10,2) NOT NULL,
  `motivo` varchar(255) DEFAULT NULL,
  `usuario_id` int(11) NOT NULL,
  `billetes_20` int(11) DEFAULT 0,
  `billetes_50` int(11) DEFAULT 0,
  `billetes_100` int(11) DEFAULT 0,
  `billetes_200` int(11) DEFAULT 0,
  `billetes_500` int(11) DEFAULT 0,
  `dolares` decimal(10,2) DEFAULT 0.00
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `roles_b2b_empresa`
--

CREATE TABLE `roles_b2b_empresa` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `usuario_id` int(11) NOT NULL,
  `es_supervisor` tinyint(1) DEFAULT 0,
  `es_ventas` tinyint(1) DEFAULT 0,
  `es_cxc` tinyint(1) DEFAULT 0,
  `es_cxp` tinyint(1) DEFAULT 0,
  `es_almacen` tinyint(1) DEFAULT 0,
  `es_reparto` tinyint(1) DEFAULT 0,
  `telefono_whatsapp` varchar(20) DEFAULT NULL,
  `notificar_whatsapp` tinyint(1) DEFAULT 1,
  `activo` tinyint(1) DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `subcuentas_contables`
--

CREATE TABLE `subcuentas_contables` (
  `id` int(11) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `cuenta_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `suscripciones`
--

CREATE TABLE `suscripciones` (
  `id` int(11) NOT NULL,
  `contratante_id` int(11) NOT NULL,
  `tipo_plan` enum('MENSUAL','ANUAL') NOT NULL DEFAULT 'MENSUAL',
  `fecha_inicio` date NOT NULL,
  `fecha_vencimiento` date NOT NULL,
  `fecha_proximo_pago` date NOT NULL,
  `subtotal` decimal(10,2) NOT NULL DEFAULT 0.00,
  `descuento_porcentaje` decimal(5,2) DEFAULT 0.00,
  `descuento_monto` decimal(10,2) DEFAULT 0.00,
  `total` decimal(10,2) NOT NULL DEFAULT 0.00,
  `estado` enum('ACTIVA','VENCIDA','SUSPENDIDA','CANCELADA') DEFAULT 'ACTIVA',
  `metodo_pago` varchar(50) DEFAULT NULL,
  `referencia_pago` varchar(100) DEFAULT NULL,
  `notas` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `suscripciones`
--

INSERT INTO `suscripciones` (`id`, `contratante_id`, `tipo_plan`, `fecha_inicio`, `fecha_vencimiento`, `fecha_proximo_pago`, `subtotal`, `descuento_porcentaje`, `descuento_monto`, `total`, `estado`, `metodo_pago`, `referencia_pago`, `notas`) VALUES
(2, 5, 'ANUAL', '2025-12-28', '2026-12-28', '2026-12-28', 6980.00, 0.00, 0.00, 6980.00, 'ACTIVA', NULL, NULL, NULL);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `tipos_inventario`
--

CREATE TABLE `tipos_inventario` (
  `id` tinyint(4) NOT NULL,
  `clave` enum('MP','WIP','PT') NOT NULL,
  `empresa_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `tipos_inventario`
--

INSERT INTO `tipos_inventario` (`id`, `clave`, `empresa_id`) VALUES
(1, 'MP', NULL),
(2, 'WIP', NULL),
(3, 'PT', NULL);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `tipo_inventario`
--

CREATE TABLE `tipo_inventario` (
  `id` int(11) NOT NULL,
  `nombre` enum('MP','WIP','PT') NOT NULL,
  `empresa_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `tipo_inventario`
--

INSERT INTO `tipo_inventario` (`id`, `nombre`, `empresa_id`) VALUES
(1, 'MP', NULL),
(2, 'WIP', NULL),
(3, 'PT', NULL);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `transferencias_detalle`
--

CREATE TABLE `transferencias_detalle` (
  `id` int(11) NOT NULL,
  `transferencia_id` int(11) NOT NULL,
  `producto_id` int(11) NOT NULL,
  `cantidad` decimal(15,4) NOT NULL,
  `precio_unitario` decimal(15,2) NOT NULL,
  `subtotal` decimal(15,2) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `transferencias_intercompany`
--

CREATE TABLE `transferencias_intercompany` (
  `id` int(11) NOT NULL,
  `contratante_id` int(11) NOT NULL,
  `empresa_origen_id` int(11) NOT NULL,
  `empresa_destino_id` int(11) NOT NULL,
  `folio` varchar(50) NOT NULL,
  `fecha_transferencia` date NOT NULL,
  `usuario_id` int(11) NOT NULL,
  `subtotal` decimal(15,2) NOT NULL DEFAULT 0.00,
  `total` decimal(15,2) NOT NULL DEFAULT 0.00,
  `estado` enum('PENDIENTE','EN_TRANSITO','RECIBIDA','CANCELADA') DEFAULT 'PENDIENTE',
  `fecha_envio` timestamp NULL DEFAULT NULL,
  `fecha_recepcion` timestamp NULL DEFAULT NULL,
  `usuario_recibe_id` int(11) DEFAULT NULL,
  `notas` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `turnos`
--

CREATE TABLE `turnos` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `usuario_id` int(11) NOT NULL,
  `usuario_nombre` varchar(100) NOT NULL,
  `fecha_apertura` datetime NOT NULL,
  `fecha_cierre` datetime DEFAULT NULL,
  `fondo_inicial` decimal(10,2) NOT NULL,
  `tipo_cambio` decimal(10,2) NOT NULL,
  `estado` varchar(20) DEFAULT 'abierto',
  `total_ventas` decimal(10,2) DEFAULT 0.00,
  `total_efectivo` decimal(10,2) DEFAULT 0.00,
  `total_tarjeta` decimal(10,2) DEFAULT 0.00,
  `fondo_final` decimal(10,2) DEFAULT NULL,
  `diferencia` decimal(10,2) DEFAULT NULL,
  `notas` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `turnos`
--

INSERT INTO `turnos` (`id`, `empresa_id`, `usuario_id`, `usuario_nombre`, `fecha_apertura`, `fecha_cierre`, `fondo_inicial`, `tipo_cambio`, `estado`, `total_ventas`, `total_efectivo`, `total_tarjeta`, `fondo_final`, `diferencia`, `notas`) VALUES
(2, 1, 13, 'Luis Juarez', '2025-12-04 20:41:16', NULL, 500.00, 18.00, 'abierto', 0.00, 0.00, 0.00, NULL, NULL, '');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `turno_arqueo`
--

CREATE TABLE `turno_arqueo` (
  `id` int(11) NOT NULL,
  `turno_id` int(11) NOT NULL,
  `billetes_20` int(11) DEFAULT 0,
  `billetes_50` int(11) DEFAULT 0,
  `billetes_100` int(11) DEFAULT 0,
  `billetes_200` int(11) DEFAULT 0,
  `billetes_500` int(11) DEFAULT 0,
  `dolares` decimal(10,2) DEFAULT 0.00,
  `monedas` decimal(10,2) DEFAULT 0.00,
  `total_efectivo` decimal(10,2) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `turno_gastos`
--

CREATE TABLE `turno_gastos` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) DEFAULT NULL,
  `turno_id` int(11) NOT NULL,
  `fecha` datetime NOT NULL,
  `concepto` varchar(255) NOT NULL,
  `monto` decimal(10,2) NOT NULL,
  `tipo` enum('compra','gasto') NOT NULL,
  `notas` text DEFAULT NULL,
  `usuario_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `turno_gastos`
--

INSERT INTO `turno_gastos` (`id`, `empresa_id`, `turno_id`, `fecha`, `concepto`, `monto`, `tipo`, `notas`, `usuario_id`) VALUES
(1, 1, 2, '2025-12-04 21:59:26', 'Ba帽o', 15.00, 'gasto', '', 13),
(2, 1, 2, '2025-12-04 22:01:21', 'Leche', 84.00, 'gasto', '', 13),
(3, 1, 2, '2025-12-04 22:02:30', 'Sueldo Odalis', 500.00, 'gasto', '', 13);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `turno_inventario`
--

CREATE TABLE `turno_inventario` (
  `id` int(11) NOT NULL,
  `turno_id` int(11) NOT NULL,
  `producto_id` int(11) NOT NULL,
  `producto_nombre` varchar(200) NOT NULL,
  `cantidad_inicial` decimal(10,2) NOT NULL,
  `cantidad_final` decimal(10,2) DEFAULT NULL,
  `empresa_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `turno_inventario`
--

INSERT INTO `turno_inventario` (`id`, `turno_id`, `producto_id`, `producto_nombre`, `cantidad_inicial`, `cantidad_final`, `empresa_id`) VALUES
(1, 2, 62, 'Agua 500ml', 5.00, NULL, 1),
(2, 2, 63, 'Brownie', 4.00, NULL, 1),
(3, 2, 65, 'Churro relleno', 0.00, NULL, 1),
(4, 2, 57, 'Cono Choco', 62.00, NULL, 1),
(5, 2, 56, 'Cono Galleta', 137.00, NULL, 1),
(6, 2, 55, 'Cono Oblea', 55.00, NULL, 1),
(7, 2, 58, 'Cono Wafle', 20.00, NULL, 1),
(8, 2, 66, 'Fresa', 9.00, NULL, 1),
(9, 2, 61, 'Sodas', 6.00, NULL, 1),
(10, 2, 59, 'Vaso Chocoice', 11.00, NULL, 1),
(11, 2, 60, 'Vaso Frappe', 21.00, NULL, 1),
(12, 2, 64, 'Vaso Malteada 16oz', 1.00, NULL, 1);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `turno_inventario_final`
--

CREATE TABLE `turno_inventario_final` (
  `id` int(11) NOT NULL,
  `turno_id` int(11) NOT NULL,
  `producto_id` int(11) NOT NULL,
  `producto_nombre` varchar(200) DEFAULT NULL,
  `cantidad_final` decimal(10,3) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `turno_mermas`
--

CREATE TABLE `turno_mermas` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) DEFAULT NULL,
  `turno_id` int(11) NOT NULL,
  `fecha` datetime NOT NULL,
  `producto_id` int(11) NOT NULL,
  `producto_nombre` varchar(200) DEFAULT NULL,
  `cantidad` decimal(10,3) NOT NULL,
  `costo_unitario` decimal(10,2) DEFAULT 0.00,
  `costo_total` decimal(10,2) DEFAULT 0.00,
  `motivo` varchar(100) DEFAULT NULL,
  `notas` varchar(255) DEFAULT NULL,
  `usuario_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `turno_mermas`
--

INSERT INTO `turno_mermas` (`id`, `empresa_id`, `turno_id`, `fecha`, `producto_id`, `producto_nombre`, `cantidad`, `costo_unitario`, `costo_total`, `motivo`, `notas`, `usuario_id`) VALUES
(1, 1, 2, '2025-12-04 21:42:21', 62, 'Agua 500ml', 1.000, 0.00, 0.00, 'roto', NULL, 13);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `ubicaciones_config`
--

CREATE TABLE `ubicaciones_config` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `nivel` int(11) NOT NULL,
  `activo` tinyint(1) DEFAULT 1,
  `nombre_nivel` varchar(50) NOT NULL,
  `nombre_personalizado` varchar(50) DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `ubicaciones_valores`
--

CREATE TABLE `ubicaciones_valores` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `nivel` int(11) NOT NULL,
  `codigo` varchar(50) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `padre_id` int(11) DEFAULT NULL,
  `activo` tinyint(1) DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `unidades_medida`
--

CREATE TABLE `unidades_medida` (
  `id` int(11) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `empresa_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `unidades_medida`
--

INSERT INTO `unidades_medida` (`id`, `nombre`, `empresa_id`) VALUES
(1, 'uds', NULL),
(2, 'mililitro', NULL),
(3, 'gramos', NULL),
(4, 'KG', NULL);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `usuarios`
--

CREATE TABLE `usuarios` (
  `id` int(11) NOT NULL,
  `contratante_id` int(11) DEFAULT NULL,
  `nombre` varchar(100) NOT NULL,
  `usuario` varchar(50) DEFAULT NULL,
  `correo` varchar(100) NOT NULL,
  `contrasena` varchar(255) NOT NULL,
  `rol` enum('admin','editor') NOT NULL,
  `email_confirmado` tinyint(1) DEFAULT 0,
  `token_confirmacion` varchar(100) DEFAULT NULL,
  `token_reset` varchar(100) DEFAULT NULL,
  `token_reset_expira` datetime DEFAULT NULL,
  `fecha_registro` datetime DEFAULT current_timestamp(),
  `empresa_id` int(11) DEFAULT NULL,
  `rango` int(11) DEFAULT 4,
  `empresas_acceso` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`empresas_acceso`)),
  `puede_agregar_usuarios` tinyint(1) DEFAULT 0,
  `tipo_usuario` varchar(50) DEFAULT 'operador',
  `activo` tinyint(1) DEFAULT 1,
  `fecha_ingreso` date DEFAULT NULL,
  `ultimo_acceso` datetime DEFAULT NULL,
  `telefono` varchar(20) DEFAULT NULL,
  `puesto` varchar(100) DEFAULT NULL,
  `estado_registro` enum('pendiente','invitado','activo','inactivo') DEFAULT 'pendiente',
  `token_invitacion` varchar(100) DEFAULT NULL,
  `fecha_invitacion` datetime DEFAULT NULL,
  `invitado_por` int(11) DEFAULT NULL,
  `fecha_token_expira` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `usuarios`
--

INSERT INTO `usuarios` (`id`, `contratante_id`, `nombre`, `usuario`, `correo`, `contrasena`, `rol`, `email_confirmado`, `token_confirmacion`, `token_reset`, `token_reset_expira`, `fecha_registro`, `empresa_id`, `rango`, `empresas_acceso`, `puede_agregar_usuarios`, `tipo_usuario`, `activo`, `fecha_ingreso`, `ultimo_acceso`, `telefono`, `puesto`, `estado_registro`, `token_invitacion`, `fecha_invitacion`, `invitado_por`, `fecha_token_expira`) VALUES
(6, 1, 'Admin Principal', 'admin', 'admin@miapp.com', '$2b$12$VeOkED27Wc7gX2M2IMcNuuia7PfwIe9PsIOu2R0DWGoZNnMORyOrm', 'admin', 0, NULL, NULL, NULL, '2025-12-02 22:41:03', NULL, 4, '[null]', 0, 'operador', 1, NULL, NULL, NULL, NULL, 'pendiente', NULL, NULL, NULL, NULL),
(8, 1, 'Editor Uno', 'editor', 'editor@miapp.com', '$2b$12$pqrosBEHOdv8gB0VavMRi.VfciJJVI.qyKNvOSvSykG/Lh/R36s5W', 'editor', 0, NULL, NULL, NULL, '2025-12-02 22:41:03', NULL, 4, '[null]', 0, 'operador', 1, NULL, NULL, NULL, NULL, 'pendiente', NULL, NULL, NULL, NULL),
(9, 1, 'Pako', 'pako', 'fcogranados@yahoo.com', '$2b$12$hiLNYk5JNDIMiMpz5ykqoujvBf/Hs7vM7aHjcgfaxNx/zaDcT2xti', 'admin', 1, NULL, NULL, NULL, '2025-12-02 22:41:03', 1, 4, '[1]', 0, 'operador', 1, NULL, NULL, NULL, 'Mostrador', 'activo', NULL, NULL, NULL, NULL),
(12, 1, 'Admin', 'admin2', 'admin@local', '$2b$12$abcdefghijklmnopqrstuvCnxm0mVwQ1JxWw1m0Q3v0', 'admin', 0, NULL, NULL, NULL, '2025-12-02 22:41:03', NULL, 4, '[null]', 0, 'operador', 1, NULL, NULL, NULL, NULL, 'pendiente', NULL, NULL, NULL, NULL),
(13, 1, 'Luis Juarez', 'luis', 'yolopostres@gmail.com', '$2b$12$s3Nwh8lMCicAt/w9fcLxkeibv9d.eybZam9awWprFLWDub.NUJaQ.', 'admin', 1, NULL, NULL, NULL, '2025-12-02 22:50:03', 1, 4, '[1]', 0, 'admin_empresa', 1, NULL, NULL, NULL, NULL, 'pendiente', NULL, NULL, NULL, NULL),
(24, 1, 'Pako Usuario', 'pakogranados1', 'pakogranados1@gmail.com', 'scrypt:32768:8:1$IN2LzwOvgNVVpxDI$92ba3020b07b46e7b1616549d35698f6a9ffee3b1f2f6be3b5fc3c202dba0ff8b9', 'editor', 1, NULL, NULL, NULL, '2025-12-12 10:58:15', 1, 4, '[1]', 0, 'operador', 1, NULL, NULL, NULL, 'Mostrador', 'activo', NULL, '2025-12-12 10:58:15', 13, '2025-12-13 10:58:15'),
(28, 5, 'Director General', NULL, 'pakogranados1@hotmail.com', 'scrypt:32768:8:1$xYt5UXpxh7Yvq2oh$93d6280383910ab85e9221ef0cb660f196036e948b4cc32d42682dc43a532f53fca3d2390cf9a64968dd588c6ef794e19af8483e0f507cd23beeb7ef39b7bc3d', 'admin', 0, NULL, NULL, NULL, '2025-12-28 02:58:54', 4, 1, '[4]', 1, 'operador', 1, NULL, NULL, NULL, NULL, 'pendiente', NULL, NULL, NULL, NULL);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `usuario_areas`
--

CREATE TABLE `usuario_areas` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) DEFAULT NULL,
  `usuario_id` int(11) NOT NULL,
  `area_id` int(11) NOT NULL,
  `es_responsable` tinyint(1) DEFAULT 0,
  `fecha_asignacion` timestamp NOT NULL DEFAULT current_timestamp(),
  `rol_area` enum('responsable','supervisor','operador','consulta') DEFAULT 'operador',
  `puede_autorizar` tinyint(1) DEFAULT 0,
  `puede_editar` tinyint(1) DEFAULT 1,
  `puede_eliminar` tinyint(1) DEFAULT 0,
  `notificar_alertas` tinyint(1) DEFAULT 1,
  `asignado_por` int(11) DEFAULT NULL,
  `activo` tinyint(1) DEFAULT 1,
  `notas` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `usuario_areas`
--

INSERT INTO `usuario_areas` (`id`, `empresa_id`, `usuario_id`, `area_id`, `es_responsable`, `fecha_asignacion`, `rol_area`, `puede_autorizar`, `puede_editar`, `puede_eliminar`, `notificar_alertas`, `asignado_por`, `activo`, `notas`) VALUES
(3, 1, 9, 1, 0, '2025-12-12 01:15:30', 'responsable', 0, 1, 0, 1, 9, 0, NULL);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `ventas`
--

CREATE TABLE `ventas` (
  `id` int(11) NOT NULL,
  `contratante_id` int(11) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `turno_id` int(11) DEFAULT NULL,
  `fecha` datetime DEFAULT current_timestamp(),
  `subtotal` decimal(10,2) NOT NULL,
  `iva` decimal(10,2) DEFAULT 0.00,
  `total` decimal(10,2) NOT NULL,
  `metodo_pago` varchar(50) DEFAULT 'efectivo',
  `estado` varchar(20) DEFAULT 'completada',
  `usuario_id` int(11) DEFAULT NULL,
  `tipo_factura` enum('EXTERNA','INTERCOMPANY') DEFAULT 'EXTERNA',
  `empresa_destino_id` int(11) DEFAULT NULL,
  `cfdi_uuid` varchar(100) DEFAULT NULL,
  `cfdi_xml` longtext DEFAULT NULL,
  `cfdi_fecha_timbrado` timestamp NULL DEFAULT NULL,
  `cfdi_estado` enum('SIN_TIMBRAR','TIMBRADO','CANCELADO') DEFAULT 'SIN_TIMBRAR'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `ventas_historicas`
--

CREATE TABLE `ventas_historicas` (
  `id` int(11) NOT NULL,
  `empresa_id` int(11) NOT NULL,
  `registro_id` int(11) DEFAULT NULL,
  `fecha` date NOT NULL,
  `producto_id` int(11) NOT NULL,
  `producto_nombre` varchar(255) DEFAULT NULL,
  `cantidad` decimal(10,3) NOT NULL DEFAULT 1.000,
  `precio_unitario` decimal(12,2) NOT NULL DEFAULT 0.00,
  `subtotal` decimal(12,2) NOT NULL DEFAULT 0.00,
  `metodo_pago` varchar(50) DEFAULT 'efectivo',
  `notas` varchar(255) DEFAULT NULL,
  `usuario_id` int(11) DEFAULT NULL,
  `fecha_registro` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura Stand-in para la vista `vw_cuentas_contables`
-- (V茅ase abajo para la vista actual)
--
CREATE TABLE `vw_cuentas_contables` (
`id` int(11)
,`codigo` varchar(20)
,`nombre` varchar(255)
,`tipo` enum('Activo','Pasivo','Patrimonio','Ingresos','Gastos')
,`naturaleza` enum('Deudora','Acreedora')
,`nivel` tinyint(4)
,`permite_subcuentas` tinyint(1)
,`padre_id` int(11)
,`padre_codigo` varchar(20)
,`padre_nombre` varchar(255)
,`hijos` bigint(21)
);

-- --------------------------------------------------------

--
-- Estructura Stand-in para la vista `v_alertas_activas`
-- (V茅ase abajo para la vista actual)
--
CREATE TABLE `v_alertas_activas` (
`id` int(11)
,`empresa_id` int(11)
,`usuario_id` int(11)
,`rol_destino` varchar(50)
,`tipo` varchar(50)
,`referencia_tipo` varchar(50)
,`referencia_id` int(11)
,`titulo` varchar(200)
,`mensaje` text
,`leida` tinyint(1)
,`activa` tinyint(1)
,`fecha_creacion` datetime
,`fecha_lectura` datetime
,`fecha_cierre` datetime
,`whatsapp_enviado` tinyint(1)
,`whatsapp_fecha` datetime
,`empresa_nombre` varchar(255)
);

-- --------------------------------------------------------

--
-- Estructura Stand-in para la vista `v_areas_responsables`
-- (V茅ase abajo para la vista actual)
--
CREATE TABLE `v_areas_responsables` (
`area_id` int(11)
,`empresa_id` int(11)
,`codigo` varchar(50)
,`area_nombre` varchar(100)
,`descripcion` text
,`modulo_relacionado` varchar(50)
,`icono` varchar(50)
,`color` varchar(20)
,`activa` tinyint(1)
,`asignacion_id` int(11)
,`usuario_id` int(11)
,`usuario_nombre` varchar(100)
,`usuario_puesto` varchar(100)
,`rol_area` enum('responsable','supervisor','operador','consulta')
,`puede_autorizar` tinyint(1)
,`asignacion_activa` tinyint(1)
);

-- --------------------------------------------------------

--
-- Estructura Stand-in para la vista `v_existencias`
-- (V茅ase abajo para la vista actual)
--
CREATE TABLE `v_existencias` (
`mercancia_id` int(11)
,`tipo_inventario_id` int(11)
,`unidades_disponibles` decimal(32,2)
);

-- --------------------------------------------------------

--
-- Estructura Stand-in para la vista `v_facturas_en_proceso`
-- (V茅ase abajo para la vista actual)
--
CREATE TABLE `v_facturas_en_proceso` (
`id` int(11)
,`empresa_emisora_id` int(11)
,`empresa_receptora_id` int(11)
,`turno_id` int(11)
,`orden_compra_id` int(11)
,`folio` varchar(30)
,`fecha_emision` datetime
,`fecha_vencimiento` date
,`subtotal` decimal(12,2)
,`iva` decimal(12,2)
,`total` decimal(12,2)
,`forma_pago` varchar(50)
,`metodo_pago` enum('PUE','PPD')
,`condiciones_pago` varchar(255)
,`estado` enum('emitida','pendiente','en_revision','recibida','con_diferencias','cancelada')
,`estado_almacen` varchar(30)
,`estado_reparto` varchar(30)
,`estado_entrega` varchar(30)
,`fecha_recepcion` datetime
,`recibida_por_usuario_id` int(11)
,`almacen_completado_por` int(11)
,`almacen_completado_fecha` datetime
,`reparto_asignado_a` int(11)
,`reparto_recogido_fecha` datetime
,`reparto_entregado_fecha` datetime
,`cliente_almacen_usuario_id` int(11)
,`cliente_almacen_fecha` datetime
,`notas_recepcion` text
,`emitida_por_usuario_id` int(11)
,`fecha_creacion` datetime
,`fecha_actualizacion` datetime
,`emisor_nombre` varchar(255)
,`receptor_nombre` varchar(255)
);

-- --------------------------------------------------------

--
-- Estructura Stand-in para la vista `v_inventario_consolidado`
-- (V茅ase abajo para la vista actual)
--
CREATE TABLE `v_inventario_consolidado` (
`id` int(11)
,`producto` varchar(255)
,`inventario_inicial` int(11)
,`entradas` int(11)
,`salidas` int(11)
,`disponible` bigint(13)
,`valor_inventario` decimal(22,2)
);

-- --------------------------------------------------------

--
-- Estructura Stand-in para la vista `v_movimientos_inventario`
-- (V茅ase abajo para la vista actual)
--
CREATE TABLE `v_movimientos_inventario` (
`movimiento_id` int(11)
,`producto` varchar(255)
,`tipo` enum('entrada','salida')
,`cantidad` decimal(12,2)
,`costo_unitario` decimal(12,2)
,`total` decimal(24,4)
,`referencia` varchar(255)
,`fecha` timestamp
,`mercancia_id` int(11)
,`producto_id` int(11)
);

-- --------------------------------------------------------

--
-- Estructura Stand-in para la vista `v_ordenes_pendientes`
-- (V茅ase abajo para la vista actual)
--
CREATE TABLE `v_ordenes_pendientes` (
`id` int(11)
,`empresa_cliente_id` int(11)
,`empresa_proveedor_id` int(11)
,`turno_id` int(11)
,`folio` varchar(30)
,`fecha_solicitud` datetime
,`subtotal` decimal(12,2)
,`iva` decimal(12,2)
,`total` decimal(12,2)
,`estado` varchar(30)
,`solicitado_por_usuario_id` int(11)
,`aprobado_por_usuario_id` int(11)
,`fecha_aprobacion` datetime
,`notas` text
,`notas_rechazo` text
,`fecha_creacion` datetime
,`fecha_actualizacion` datetime
,`cliente_nombre` varchar(255)
,`proveedor_nombre` varchar(255)
);

-- --------------------------------------------------------

--
-- Estructura Stand-in para la vista `v_stock`
-- (V茅ase abajo para la vista actual)
--
CREATE TABLE `v_stock` (
`mercancia_id` int(11)
,`producto` varchar(255)
,`fase` enum('MP','WIP','PT')
,`unidades` decimal(32,2)
);

-- --------------------------------------------------------

--
-- Estructura Stand-in para la vista `v_usuarios_registro`
-- (V茅ase abajo para la vista actual)
--
CREATE TABLE `v_usuarios_registro` (
`id` int(11)
,`nombre` varchar(100)
,`correo` varchar(100)
,`puesto` varchar(100)
,`estado_registro` enum('pendiente','invitado','activo','inactivo')
,`empresa_id` int(11)
,`empresa_nombre` varchar(255)
,`fecha_registro` datetime
,`fecha_invitacion` datetime
,`invitado_por_nombre` varchar(100)
,`num_areas_asignadas` bigint(21)
);

-- --------------------------------------------------------

--
-- Estructura Stand-in para la vista `v_usuario_permisos_areas`
-- (V茅ase abajo para la vista actual)
--
CREATE TABLE `v_usuario_permisos_areas` (
`usuario_id` int(11)
,`empresa_id` int(11)
,`usuario_nombre` varchar(100)
,`area_codigo` varchar(50)
,`area_nombre` varchar(100)
,`modulo_relacionado` varchar(50)
,`rol_area` enum('responsable','supervisor','operador','consulta')
,`puede_autorizar` tinyint(1)
,`puede_editar` tinyint(1)
,`puede_eliminar` tinyint(1)
,`notificar_alertas` tinyint(1)
);

-- --------------------------------------------------------

--
-- Estructura para la vista `vw_cuentas_contables`
--
DROP TABLE IF EXISTS `vw_cuentas_contables`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `vw_cuentas_contables`  AS SELECT `c`.`id` AS `id`, `c`.`codigo` AS `codigo`, `c`.`nombre` AS `nombre`, `c`.`tipo` AS `tipo`, `c`.`naturaleza` AS `naturaleza`, `c`.`nivel` AS `nivel`, `c`.`permite_subcuentas` AS `permite_subcuentas`, `c`.`padre_id` AS `padre_id`, `p`.`codigo` AS `padre_codigo`, `p`.`nombre` AS `padre_nombre`, (select count(0) from `cuentas_contables` `h` where `h`.`padre_id` = `c`.`id`) AS `hijos` FROM (`cuentas_contables` `c` left join `cuentas_contables` `p` on(`p`.`id` = `c`.`padre_id`)) ;

-- --------------------------------------------------------

--
-- Estructura para la vista `v_alertas_activas`
--
DROP TABLE IF EXISTS `v_alertas_activas`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `v_alertas_activas`  AS SELECT `a`.`id` AS `id`, `a`.`empresa_id` AS `empresa_id`, `a`.`usuario_id` AS `usuario_id`, `a`.`rol_destino` AS `rol_destino`, `a`.`tipo` AS `tipo`, `a`.`referencia_tipo` AS `referencia_tipo`, `a`.`referencia_id` AS `referencia_id`, `a`.`titulo` AS `titulo`, `a`.`mensaje` AS `mensaje`, `a`.`leida` AS `leida`, `a`.`activa` AS `activa`, `a`.`fecha_creacion` AS `fecha_creacion`, `a`.`fecha_lectura` AS `fecha_lectura`, `a`.`fecha_cierre` AS `fecha_cierre`, `a`.`whatsapp_enviado` AS `whatsapp_enviado`, `a`.`whatsapp_fecha` AS `whatsapp_fecha`, `e`.`nombre` AS `empresa_nombre` FROM (`alertas_b2b` `a` join `empresas` `e` on(`e`.`id` = `a`.`empresa_id`)) WHERE `a`.`activa` = 1 AND `a`.`leida` = 0 ;

-- --------------------------------------------------------

--
-- Estructura para la vista `v_areas_responsables`
--
DROP TABLE IF EXISTS `v_areas_responsables`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `v_areas_responsables`  AS SELECT `a`.`id` AS `area_id`, `a`.`empresa_id` AS `empresa_id`, `a`.`codigo` AS `codigo`, `a`.`nombre` AS `area_nombre`, `a`.`descripcion` AS `descripcion`, `a`.`modulo_relacionado` AS `modulo_relacionado`, `a`.`icono` AS `icono`, `a`.`color` AS `color`, `a`.`activo` AS `activa`, `ua`.`id` AS `asignacion_id`, `ua`.`usuario_id` AS `usuario_id`, `u`.`nombre` AS `usuario_nombre`, `u`.`puesto` AS `usuario_puesto`, `ua`.`rol_area` AS `rol_area`, `ua`.`puede_autorizar` AS `puede_autorizar`, `ua`.`activo` AS `asignacion_activa` FROM ((`areas_sistema` `a` left join `usuario_areas` `ua` on(`ua`.`area_id` = `a`.`id` and `ua`.`activo` = 1)) left join `usuarios` `u` on(`u`.`id` = `ua`.`usuario_id`)) WHERE `a`.`activo` = 1 ;

-- --------------------------------------------------------

--
-- Estructura para la vista `v_existencias`
--
DROP TABLE IF EXISTS `v_existencias`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `v_existencias`  AS SELECT `inventario_movimientos`.`mercancia_id` AS `mercancia_id`, `inventario_movimientos`.`tipo_inventario_id` AS `tipo_inventario_id`, coalesce(sum(case when `inventario_movimientos`.`tipo_movimiento` = 'entrada' then `inventario_movimientos`.`unidades` when `inventario_movimientos`.`tipo_movimiento` = 'salida' then -`inventario_movimientos`.`unidades` else 0 end),0) AS `unidades_disponibles` FROM `inventario_movimientos` GROUP BY `inventario_movimientos`.`mercancia_id`, `inventario_movimientos`.`tipo_inventario_id` ;

-- --------------------------------------------------------

--
-- Estructura para la vista `v_facturas_en_proceso`
--
DROP TABLE IF EXISTS `v_facturas_en_proceso`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `v_facturas_en_proceso`  AS SELECT `f`.`id` AS `id`, `f`.`empresa_emisora_id` AS `empresa_emisora_id`, `f`.`empresa_receptora_id` AS `empresa_receptora_id`, `f`.`turno_id` AS `turno_id`, `f`.`orden_compra_id` AS `orden_compra_id`, `f`.`folio` AS `folio`, `f`.`fecha_emision` AS `fecha_emision`, `f`.`fecha_vencimiento` AS `fecha_vencimiento`, `f`.`subtotal` AS `subtotal`, `f`.`iva` AS `iva`, `f`.`total` AS `total`, `f`.`forma_pago` AS `forma_pago`, `f`.`metodo_pago` AS `metodo_pago`, `f`.`condiciones_pago` AS `condiciones_pago`, `f`.`estado` AS `estado`, `f`.`estado_almacen` AS `estado_almacen`, `f`.`estado_reparto` AS `estado_reparto`, `f`.`estado_entrega` AS `estado_entrega`, `f`.`fecha_recepcion` AS `fecha_recepcion`, `f`.`recibida_por_usuario_id` AS `recibida_por_usuario_id`, `f`.`almacen_completado_por` AS `almacen_completado_por`, `f`.`almacen_completado_fecha` AS `almacen_completado_fecha`, `f`.`reparto_asignado_a` AS `reparto_asignado_a`, `f`.`reparto_recogido_fecha` AS `reparto_recogido_fecha`, `f`.`reparto_entregado_fecha` AS `reparto_entregado_fecha`, `f`.`cliente_almacen_usuario_id` AS `cliente_almacen_usuario_id`, `f`.`cliente_almacen_fecha` AS `cliente_almacen_fecha`, `f`.`notas_recepcion` AS `notas_recepcion`, `f`.`emitida_por_usuario_id` AS `emitida_por_usuario_id`, `f`.`fecha_creacion` AS `fecha_creacion`, `f`.`fecha_actualizacion` AS `fecha_actualizacion`, `ee`.`nombre` AS `emisor_nombre`, `er`.`nombre` AS `receptor_nombre` FROM ((`facturas_b2b` `f` join `empresas` `ee` on(`ee`.`id` = `f`.`empresa_emisora_id`)) join `empresas` `er` on(`er`.`id` = `f`.`empresa_receptora_id`)) WHERE `f`.`estado` not in ('cancelada','recibida') ;

-- --------------------------------------------------------

--
-- Estructura para la vista `v_inventario_consolidado`
--
DROP TABLE IF EXISTS `v_inventario_consolidado`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `v_inventario_consolidado`  AS SELECT `i`.`id` AS `id`, coalesce(`m`.`nombre`,`p`.`nombre`,`i`.`producto`) AS `producto`, `i`.`inventario_inicial` AS `inventario_inicial`, `i`.`entradas` AS `entradas`, `i`.`salidas` AS `salidas`, `i`.`inventario_inicial`+ `i`.`entradas` - `i`.`salidas` AS `disponible`, (`i`.`inventario_inicial` + `i`.`entradas` - `i`.`salidas`) * coalesce(`dc`.`precio_unitario`,0) AS `valor_inventario` FROM (((`inventario` `i` left join `mercancia` `m` on(`m`.`id` = `i`.`mercancia_id`)) left join `productos_terminados` `p` on(`p`.`id` = `i`.`producto_id`)) left join `detalle_compra` `dc` on(`dc`.`mercancia_id` = `i`.`mercancia_id`)) ORDER BY coalesce(`m`.`nombre`,`p`.`nombre`,`i`.`producto`) ASC ;

-- --------------------------------------------------------

--
-- Estructura para la vista `v_movimientos_inventario`
--
DROP TABLE IF EXISTS `v_movimientos_inventario`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `v_movimientos_inventario`  AS SELECT `mi`.`id` AS `movimiento_id`, coalesce(`m`.`nombre`,`p`.`nombre`) AS `producto`, `mi`.`tipo` AS `tipo`, `mi`.`cantidad` AS `cantidad`, `mi`.`costo_unitario` AS `costo_unitario`, `mi`.`cantidad`* `mi`.`costo_unitario` AS `total`, `mi`.`referencia` AS `referencia`, `mi`.`fecha` AS `fecha`, `mi`.`mercancia_id` AS `mercancia_id`, `mi`.`producto_id` AS `producto_id` FROM ((`movimientos_inventario` `mi` left join `mercancia` `m` on(`m`.`id` = `mi`.`mercancia_id`)) left join `productos_terminados` `p` on(`p`.`id` = `mi`.`producto_id`)) ORDER BY `mi`.`fecha` DESC ;

-- --------------------------------------------------------

--
-- Estructura para la vista `v_ordenes_pendientes`
--
DROP TABLE IF EXISTS `v_ordenes_pendientes`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `v_ordenes_pendientes`  AS SELECT `o`.`id` AS `id`, `o`.`empresa_cliente_id` AS `empresa_cliente_id`, `o`.`empresa_proveedor_id` AS `empresa_proveedor_id`, `o`.`turno_id` AS `turno_id`, `o`.`folio` AS `folio`, `o`.`fecha_solicitud` AS `fecha_solicitud`, `o`.`subtotal` AS `subtotal`, `o`.`iva` AS `iva`, `o`.`total` AS `total`, `o`.`estado` AS `estado`, `o`.`solicitado_por_usuario_id` AS `solicitado_por_usuario_id`, `o`.`aprobado_por_usuario_id` AS `aprobado_por_usuario_id`, `o`.`fecha_aprobacion` AS `fecha_aprobacion`, `o`.`notas` AS `notas`, `o`.`notas_rechazo` AS `notas_rechazo`, `o`.`fecha_creacion` AS `fecha_creacion`, `o`.`fecha_actualizacion` AS `fecha_actualizacion`, `ec`.`nombre` AS `cliente_nombre`, `ep`.`nombre` AS `proveedor_nombre` FROM ((`ordenes_compra_b2b` `o` join `empresas` `ec` on(`ec`.`id` = `o`.`empresa_cliente_id`)) join `empresas` `ep` on(`ep`.`id` = `o`.`empresa_proveedor_id`)) WHERE `o`.`estado` in ('borrador','enviada','recibida') ;

-- --------------------------------------------------------

--
-- Estructura para la vista `v_stock`
--
DROP TABLE IF EXISTS `v_stock`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `v_stock`  AS SELECT `e`.`mercancia_id` AS `mercancia_id`, `m`.`nombre` AS `producto`, `t`.`clave` AS `fase`, `e`.`unidades_disponibles` AS `unidades` FROM ((`v_existencias` `e` join `mercancia` `m` on(`m`.`id` = `e`.`mercancia_id`)) join `tipos_inventario` `t` on(`t`.`id` = `e`.`tipo_inventario_id`)) ORDER BY `m`.`nombre` ASC, `t`.`id` ASC ;

-- --------------------------------------------------------

--
-- Estructura para la vista `v_usuarios_registro`
--
DROP TABLE IF EXISTS `v_usuarios_registro`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `v_usuarios_registro`  AS SELECT `u`.`id` AS `id`, `u`.`nombre` AS `nombre`, `u`.`correo` AS `correo`, `u`.`puesto` AS `puesto`, `u`.`estado_registro` AS `estado_registro`, `u`.`empresa_id` AS `empresa_id`, `e`.`nombre` AS `empresa_nombre`, `u`.`fecha_registro` AS `fecha_registro`, `u`.`fecha_invitacion` AS `fecha_invitacion`, `inv`.`nombre` AS `invitado_por_nombre`, count(distinct `ua`.`area_id`) AS `num_areas_asignadas` FROM (((`usuarios` `u` left join `empresas` `e` on(`e`.`id` = `u`.`empresa_id`)) left join `usuarios` `inv` on(`inv`.`id` = `u`.`invitado_por`)) left join `usuario_areas` `ua` on(`ua`.`usuario_id` = `u`.`id` and `ua`.`activo` = 1)) GROUP BY `u`.`id` ;

-- --------------------------------------------------------

--
-- Estructura para la vista `v_usuario_permisos_areas`
--
DROP TABLE IF EXISTS `v_usuario_permisos_areas`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `v_usuario_permisos_areas`  AS SELECT `ua`.`usuario_id` AS `usuario_id`, `ua`.`empresa_id` AS `empresa_id`, `u`.`nombre` AS `usuario_nombre`, `a`.`codigo` AS `area_codigo`, `a`.`nombre` AS `area_nombre`, `a`.`modulo_relacionado` AS `modulo_relacionado`, `ua`.`rol_area` AS `rol_area`, `ua`.`puede_autorizar` AS `puede_autorizar`, `ua`.`puede_editar` AS `puede_editar`, `ua`.`puede_eliminar` AS `puede_eliminar`, `ua`.`notificar_alertas` AS `notificar_alertas` FROM ((`usuario_areas` `ua` join `usuarios` `u` on(`u`.`id` = `ua`.`usuario_id`)) join `areas_sistema` `a` on(`a`.`id` = `ua`.`area_id`)) WHERE `ua`.`activo` = 1 AND `a`.`activo` = 1 ;

--
-- 脥ndices para tablas volcadas
--

--
-- Indices de la tabla `alertas_b2b`
--
ALTER TABLE `alertas_b2b`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_empresa` (`empresa_id`),
  ADD KEY `idx_usuario` (`usuario_id`),
  ADD KEY `idx_rol` (`rol_destino`),
  ADD KEY `idx_activa` (`activa`),
  ADD KEY `idx_referencia` (`referencia_tipo`,`referencia_id`);

--
-- Indices de la tabla `areas_produccion`
--
ALTER TABLE `areas_produccion`
  ADD PRIMARY KEY (`id`),
  ADD KEY `empresa_id` (`empresa_id`);

--
-- Indices de la tabla `areas_sistema`
--
ALTER TABLE `areas_sistema`
  ADD PRIMARY KEY (`id`);

--
-- Indices de la tabla `asientos_contables`
--
ALTER TABLE `asientos_contables`
  ADD PRIMARY KEY (`id`),
  ADD KEY `producto_id` (`producto_id`),
  ADD KEY `mercancia_id` (`mercancia_id`),
  ADD KEY `cuenta_debe` (`cuenta_debe`),
  ADD KEY `cuenta_haber` (`cuenta_haber`);

--
-- Indices de la tabla `asientos_detalle`
--
ALTER TABLE `asientos_detalle`
  ADD PRIMARY KEY (`id`),
  ADD KEY `asiento_id` (`asiento_id`),
  ADD KEY `cuenta_id` (`cuenta_id`);

--
-- Indices de la tabla `cajas`
--
ALTER TABLE `cajas`
  ADD PRIMARY KEY (`id`);

--
-- Indices de la tabla `caja_botones`
--
ALTER TABLE `caja_botones`
  ADD PRIMARY KEY (`id`);

--
-- Indices de la tabla `caja_ventas`
--
ALTER TABLE `caja_ventas`
  ADD PRIMARY KEY (`id`),
  ADD KEY `turno_id` (`turno_id`),
  ADD KEY `usuario_id` (`usuario_id`);

--
-- Indices de la tabla `caja_ventas_detalle`
--
ALTER TABLE `caja_ventas_detalle`
  ADD PRIMARY KEY (`id`),
  ADD KEY `venta_id` (`venta_id`);

--
-- Indices de la tabla `catalogo_inventario`
--
ALTER TABLE `catalogo_inventario`
  ADD PRIMARY KEY (`id`),
  ADD KEY `empresa_id` (`empresa_id`);

--
-- Indices de la tabla `catalogo_modulos`
--
ALTER TABLE `catalogo_modulos`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `codigo` (`codigo`),
  ADD KEY `idx_codigo` (`codigo`),
  ADD KEY `idx_activo` (`activo`);

--
-- Indices de la tabla `catalogo_mp`
--
ALTER TABLE `catalogo_mp`
  ADD PRIMARY KEY (`id`),
  ADD KEY `empresa_id` (`empresa_id`);

--
-- Indices de la tabla `cfdi_importados`
--
ALTER TABLE `cfdi_importados`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uuid` (`uuid`),
  ADD KEY `compra_id` (`compra_id`),
  ADD KEY `venta_id` (`venta_id`),
  ADD KEY `idx_uuid` (`uuid`),
  ADD KEY `idx_empresa` (`empresa_id`),
  ADD KEY `idx_rfc_emisor` (`rfc_emisor`),
  ADD KEY `idx_fecha` (`fecha_emision`);

--
-- Indices de la tabla `cfdi_importados_detalle`
--
ALTER TABLE `cfdi_importados_detalle`
  ADD PRIMARY KEY (`id`),
  ADD KEY `cfdi_id` (`cfdi_id`);

--
-- Indices de la tabla `cfdi_log`
--
ALTER TABLE `cfdi_log`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_venta` (`venta_id`),
  ADD KEY `idx_empresa` (`empresa_id`),
  ADD KEY `idx_fecha` (`fecha`),
  ADD KEY `fk_cfdi_usuario` (`usuario_id`);

--
-- Indices de la tabla `compras`
--
ALTER TABLE `compras`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_compra_contratante` (`contratante_id`);

--
-- Indices de la tabla `consumos_internos`
--
ALTER TABLE `consumos_internos`
  ADD PRIMARY KEY (`id`),
  ADD KEY `registro_id` (`registro_id`),
  ADD KEY `producto_id` (`producto_id`),
  ADD KEY `usuario_id` (`usuario_id`),
  ADD KEY `idx_fecha` (`fecha`),
  ADD KEY `idx_empresa_fecha` (`empresa_id`,`fecha`);

--
-- Indices de la tabla `consumos_propios`
--
ALTER TABLE `consumos_propios`
  ADD PRIMARY KEY (`id`),
  ADD KEY `producto_id` (`producto_id`),
  ADD KEY `usuario_id` (`usuario_id`),
  ADD KEY `idx_consumos_turno` (`turno_id`),
  ADD KEY `idx_consumos_fecha` (`fecha`);

--
-- Indices de la tabla `contratantes`
--
ALTER TABLE `contratantes`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email_contacto` (`email_contacto`),
  ADD KEY `idx_rfc` (`rfc`),
  ADD KEY `idx_email` (`email_contacto`),
  ADD KEY `idx_activo` (`activo`);

--
-- Indices de la tabla `cuentas_contables`
--
ALTER TABLE `cuentas_contables`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `codigo` (`codigo`),
  ADD KEY `cuenta_padre_id` (`padre_id`);

--
-- Indices de la tabla `cuentas_por_cobrar`
--
ALTER TABLE `cuentas_por_cobrar`
  ADD PRIMARY KEY (`id`),
  ADD KEY `empresa_id` (`empresa_id`),
  ADD KEY `factura_b2b_id` (`factura_b2b_id`),
  ADD KEY `cfdi_id` (`cfdi_id`),
  ADD KEY `venta_id` (`venta_id`),
  ADD KEY `cliente_empresa_id` (`cliente_empresa_id`),
  ADD KEY `autorizado_por_usuario_id` (`autorizado_por_usuario_id`);

--
-- Indices de la tabla `cuentas_por_pagar`
--
ALTER TABLE `cuentas_por_pagar`
  ADD PRIMARY KEY (`id`),
  ADD KEY `empresa_id` (`empresa_id`),
  ADD KEY `factura_b2b_id` (`factura_b2b_id`),
  ADD KEY `cfdi_id` (`cfdi_id`),
  ADD KEY `compra_id` (`compra_id`),
  ADD KEY `proveedor_empresa_id` (`proveedor_empresa_id`),
  ADD KEY `autorizado_por_usuario_id` (`autorizado_por_usuario_id`);

--
-- Indices de la tabla `detalle_compra`
--
ALTER TABLE `detalle_compra`
  ADD PRIMARY KEY (`id`),
  ADD KEY `compra_id` (`compra_id`),
  ADD KEY `idx_dc_mercancia` (`mercancia_id`);

--
-- Indices de la tabla `detalle_venta`
--
ALTER TABLE `detalle_venta`
  ADD PRIMARY KEY (`id`);

--
-- Indices de la tabla `empresas`
--
ALTER TABLE `empresas`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_rfc` (`rfc`),
  ADD KEY `idx_contratante` (`contratante_id`);

--
-- Indices de la tabla `empresa_configuracion`
--
ALTER TABLE `empresa_configuracion`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_empresa` (`empresa_id`),
  ADD KEY `idx_empresa` (`empresa_id`);

--
-- Indices de la tabla `empresa_modulos`
--
ALTER TABLE `empresa_modulos`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_empresa_modulo` (`empresa_id`,`modulo_id`),
  ADD KEY `idx_empresa` (`empresa_id`),
  ADD KEY `idx_modulo` (`modulo_id`),
  ADD KEY `idx_activo` (`activo`);

--
-- Indices de la tabla `facturas_b2b`
--
ALTER TABLE `facturas_b2b`
  ADD PRIMARY KEY (`id`),
  ADD KEY `recibida_por_usuario_id` (`recibida_por_usuario_id`),
  ADD KEY `emitida_por_usuario_id` (`emitida_por_usuario_id`),
  ADD KEY `idx_emisora` (`empresa_emisora_id`),
  ADD KEY `idx_receptora` (`empresa_receptora_id`),
  ADD KEY `idx_estado` (`estado`);

--
-- Indices de la tabla `facturas_b2b_detalle`
--
ALTER TABLE `facturas_b2b_detalle`
  ADD PRIMARY KEY (`id`),
  ADD KEY `factura_id` (`factura_id`),
  ADD KEY `mercancia_id` (`mercancia_id`),
  ADD KEY `verificado_por_usuario_id` (`verificado_por_usuario_id`);

--
-- Indices de la tabla `facturas_notificaciones`
--
ALTER TABLE `facturas_notificaciones`
  ADD PRIMARY KEY (`id`),
  ADD KEY `empresa_destino_id` (`empresa_destino_id`);

--
-- Indices de la tabla `factura_b2b_checklist`
--
ALTER TABLE `factura_b2b_checklist`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_detalle_rol` (`detalle_id`,`rol`,`empresa_id`),
  ADD KEY `idx_factura` (`factura_id`),
  ADD KEY `idx_detalle` (`detalle_id`),
  ADD KEY `idx_rol` (`rol`);

--
-- Indices de la tabla `factura_b2b_tracking`
--
ALTER TABLE `factura_b2b_tracking`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_factura` (`factura_id`),
  ADD KEY `idx_fecha` (`fecha`);

--
-- Indices de la tabla `historial_asignaciones_area`
--
ALTER TABLE `historial_asignaciones_area`
  ADD PRIMARY KEY (`id`),
  ADD KEY `empresa_id` (`empresa_id`),
  ADD KEY `usuario_id` (`usuario_id`),
  ADD KEY `area_id` (`area_id`),
  ADD KEY `realizado_por` (`realizado_por`);

--
-- Indices de la tabla `historial_pagos`
--
ALTER TABLE `historial_pagos`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_suscripcion` (`suscripcion_id`),
  ADD KEY `idx_contratante` (`contratante_id`),
  ADD KEY `idx_fecha` (`fecha_pago`);

--
-- Indices de la tabla `incidencias`
--
ALTER TABLE `incidencias`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `codigo` (`codigo`),
  ADD KEY `area_id` (`area_id`),
  ADD KEY `responsable_id` (`responsable_id`),
  ADD KEY `created_by` (`created_by`),
  ADD KEY `idx_incidencias_empresa` (`empresa_id`);

--
-- Indices de la tabla `incidencias_bitacora`
--
ALTER TABLE `incidencias_bitacora`
  ADD PRIMARY KEY (`id`),
  ADD KEY `incidencia_id` (`incidencia_id`),
  ADD KEY `usuario_id` (`usuario_id`);

--
-- Indices de la tabla `inventario`
--
ALTER TABLE `inventario`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uq_inv_mercancia` (`mercancia_id`),
  ADD UNIQUE KEY `uq_inv_producto` (`producto_id`);

--
-- Indices de la tabla `inventario_movimientos`
--
ALTER TABLE `inventario_movimientos`
  ADD PRIMARY KEY (`id`),
  ADD KEY `mercancia_id` (`mercancia_id`),
  ADD KEY `idx_mv_fase_prod_fecha` (`tipo_inventario_id`,`mercancia_id`,`fecha`),
  ADD KEY `idx_mv_tipo` (`tipo_movimiento`);

--
-- Indices de la tabla `inventario_mp`
--
ALTER TABLE `inventario_mp`
  ADD PRIMARY KEY (`id`);

--
-- Indices de la tabla `inventario_pt`
--
ALTER TABLE `inventario_pt`
  ADD PRIMARY KEY (`id`);

--
-- Indices de la tabla `invitaciones`
--
ALTER TABLE `invitaciones`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `token` (`token`),
  ADD KEY `empresa_id` (`empresa_id`),
  ADD KEY `creada_por` (`creada_por`),
  ADD KEY `usuario_creado_id` (`usuario_creado_id`),
  ADD KEY `idx_invitacion_token` (`token`),
  ADD KEY `idx_invitacion_correo` (`correo`);

--
-- Indices de la tabla `listado_compras`
--
ALTER TABLE `listado_compras`
  ADD PRIMARY KEY (`id`);

--
-- Indices de la tabla `mercancia`
--
ALTER TABLE `mercancia`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_unidad` (`unidad_id`),
  ADD KEY `fk_cuenta` (`cuenta_id`),
  ADD KEY `fk_mercancia_subcuenta_cc` (`subcuenta_id`);

--
-- Indices de la tabla `mermas`
--
ALTER TABLE `mermas`
  ADD PRIMARY KEY (`id`),
  ADD KEY `registro_id` (`registro_id`),
  ADD KEY `producto_id` (`producto_id`),
  ADD KEY `usuario_id` (`usuario_id`),
  ADD KEY `idx_fecha` (`fecha`),
  ADD KEY `idx_empresa_fecha` (`empresa_id`,`fecha`);

--
-- Indices de la tabla `movimientos_inventario`
--
ALTER TABLE `movimientos_inventario`
  ADD PRIMARY KEY (`id`),
  ADD KEY `mercancia_id` (`mercancia_id`),
  ADD KEY `fk_mov_prod` (`producto_id`);

--
-- Indices de la tabla `notificaciones`
--
ALTER TABLE `notificaciones`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_usuario_leida` (`usuario_id`,`leida`),
  ADD KEY `idx_fecha` (`fecha_creacion`);

--
-- Indices de la tabla `notificaciones_usuario`
--
ALTER TABLE `notificaciones_usuario`
  ADD PRIMARY KEY (`id`),
  ADD KEY `empresa_id` (`empresa_id`),
  ADD KEY `usuario_origen_id` (`usuario_origen_id`),
  ADD KEY `idx_notif_usuario` (`usuario_destino_id`,`leida`);

--
-- Indices de la tabla `ordenes_compra_automaticas`
--
ALTER TABLE `ordenes_compra_automaticas`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `folio` (`folio`),
  ADD KEY `idx_empresa` (`empresa_id`),
  ADD KEY `idx_folio` (`folio`),
  ADD KEY `idx_estado` (`estado`),
  ADD KEY `idx_fecha` (`fecha_generacion`);

--
-- Indices de la tabla `ordenes_compra_automaticas_detalle`
--
ALTER TABLE `ordenes_compra_automaticas_detalle`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_orden` (`orden_id`),
  ADD KEY `idx_mercancia` (`mercancia_id`),
  ADD KEY `idx_estado` (`estado`);

--
-- Indices de la tabla `ordenes_compra_b2b`
--
ALTER TABLE `ordenes_compra_b2b`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_cliente` (`empresa_cliente_id`),
  ADD KEY `idx_proveedor` (`empresa_proveedor_id`),
  ADD KEY `idx_turno` (`turno_id`),
  ADD KEY `idx_estado` (`estado`),
  ADD KEY `idx_fecha` (`fecha_solicitud`);

--
-- Indices de la tabla `ordenes_compra_b2b_detalle`
--
ALTER TABLE `ordenes_compra_b2b_detalle`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_orden` (`orden_id`),
  ADD KEY `idx_mercancia` (`mercancia_id`);

--
-- Indices de la tabla `ordenes_compra_tracking`
--
ALTER TABLE `ordenes_compra_tracking`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_detalle` (`detalle_id`);

--
-- Indices de la tabla `ordenes_produccion`
--
ALTER TABLE `ordenes_produccion`
  ADD PRIMARY KEY (`id`),
  ADD KEY `empresa_id` (`empresa_id`),
  ADD KEY `proceso_id` (`proceso_id`),
  ADD KEY `creado_por` (`creado_por`);

--
-- Indices de la tabla `orden_mp`
--
ALTER TABLE `orden_mp`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_omp_orden` (`orden_id`),
  ADD KEY `idx_omp_mp` (`mp_mercancia_id`);

--
-- Indices de la tabla `orden_produccion`
--
ALTER TABLE `orden_produccion`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_op_pt` (`pt_mercancia_id`),
  ADD KEY `idx_op_estado` (`estado`,`fecha`);

--
-- Indices de la tabla `pagos_b2b`
--
ALTER TABLE `pagos_b2b`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_empresa` (`empresa_id`),
  ADD KEY `idx_cxp` (`cuenta_por_pagar_id`),
  ADD KEY `idx_cxc` (`cuenta_por_cobrar_id`),
  ADD KEY `idx_fecha` (`fecha_pago`);

--
-- Indices de la tabla `paso_insumos`
--
ALTER TABLE `paso_insumos`
  ADD PRIMARY KEY (`id`),
  ADD KEY `paso_id` (`paso_id`),
  ADD KEY `mercancia_id` (`mercancia_id`),
  ADD KEY `unidad_id` (`unidad_id`);

--
-- Indices de la tabla `paso_responsables`
--
ALTER TABLE `paso_responsables`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `paso_id` (`paso_id`,`usuario_id`),
  ADD KEY `usuario_id` (`usuario_id`);

--
-- Indices de la tabla `presentaciones`
--
ALTER TABLE `presentaciones`
  ADD PRIMARY KEY (`id`);

--
-- Indices de la tabla `procesos`
--
ALTER TABLE `procesos`
  ADD PRIMARY KEY (`id`),
  ADD KEY `empresa_id` (`empresa_id`),
  ADD KEY `producto_terminado_id` (`producto_terminado_id`),
  ADD KEY `producto_wip_id` (`producto_wip_id`),
  ADD KEY `unidad_produccion_id` (`unidad_produccion_id`);

--
-- Indices de la tabla `proceso_pasos`
--
ALTER TABLE `proceso_pasos`
  ADD PRIMARY KEY (`id`),
  ADD KEY `proceso_id` (`proceso_id`),
  ADD KEY `area_id` (`area_id`);

--
-- Indices de la tabla `produccion`
--
ALTER TABLE `produccion`
  ADD PRIMARY KEY (`id`);

--
-- Indices de la tabla `produccion_detalle_mp`
--
ALTER TABLE `produccion_detalle_mp`
  ADD PRIMARY KEY (`id`);

--
-- Indices de la tabla `productos_terminados`
--
ALTER TABLE `productos_terminados`
  ADD PRIMARY KEY (`id`),
  ADD KEY `fk_pt_unidad` (`unidad_id`),
  ADD KEY `fk_pt_cuenta` (`cuenta_id`),
  ADD KEY `fk_pt_subcuenta` (`subcuenta_id`);

--
-- Indices de la tabla `producto_base`
--
ALTER TABLE `producto_base`
  ADD PRIMARY KEY (`id`);

--
-- Indices de la tabla `proveedores`
--
ALTER TABLE `proveedores`
  ADD PRIMARY KEY (`id`);

--
-- Indices de la tabla `pt_precios`
--
ALTER TABLE `pt_precios`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_empresa_mercancia` (`empresa_id`,`mercancia_id`),
  ADD KEY `producto_id` (`producto_id`);

--
-- Indices de la tabla `pt_reglas_markup`
--
ALTER TABLE `pt_reglas_markup`
  ADD PRIMARY KEY (`id`);

--
-- Indices de la tabla `rangos_organizacionales`
--
ALTER TABLE `rangos_organizacionales`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `nombre` (`nombre`),
  ADD UNIQUE KEY `nivel` (`nivel`);

--
-- Indices de la tabla `registros_diarios`
--
ALTER TABLE `registros_diarios`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_empresa_fecha` (`empresa_id`,`fecha`),
  ADD KEY `usuario_id` (`usuario_id`);

--
-- Indices de la tabla `relaciones_b2b`
--
ALTER TABLE `relaciones_b2b`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_relacion` (`empresa_proveedor_id`,`empresa_cliente_id`),
  ADD KEY `idx_proveedor` (`empresa_proveedor_id`),
  ADD KEY `idx_cliente` (`empresa_cliente_id`);

--
-- Indices de la tabla `retiros_efectivo`
--
ALTER TABLE `retiros_efectivo`
  ADD PRIMARY KEY (`id`),
  ADD KEY `turno_id` (`turno_id`),
  ADD KEY `usuario_id` (`usuario_id`);

--
-- Indices de la tabla `roles_b2b_empresa`
--
ALTER TABLE `roles_b2b_empresa`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_empresa_usuario` (`empresa_id`,`usuario_id`),
  ADD KEY `idx_empresa` (`empresa_id`);

--
-- Indices de la tabla `subcuentas_contables`
--
ALTER TABLE `subcuentas_contables`
  ADD PRIMARY KEY (`id`),
  ADD KEY `cuenta_id` (`cuenta_id`);

--
-- Indices de la tabla `suscripciones`
--
ALTER TABLE `suscripciones`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_contratante` (`contratante_id`),
  ADD KEY `idx_estado` (`estado`),
  ADD KEY `idx_vencimiento` (`fecha_vencimiento`);

--
-- Indices de la tabla `tipos_inventario`
--
ALTER TABLE `tipos_inventario`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `clave` (`clave`);

--
-- Indices de la tabla `tipo_inventario`
--
ALTER TABLE `tipo_inventario`
  ADD PRIMARY KEY (`id`);

--
-- Indices de la tabla `transferencias_detalle`
--
ALTER TABLE `transferencias_detalle`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_transferencia` (`transferencia_id`),
  ADD KEY `idx_producto` (`producto_id`);

--
-- Indices de la tabla `transferencias_intercompany`
--
ALTER TABLE `transferencias_intercompany`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `folio` (`folio`),
  ADD KEY `idx_contratante` (`contratante_id`),
  ADD KEY `idx_origen` (`empresa_origen_id`),
  ADD KEY `idx_destino` (`empresa_destino_id`),
  ADD KEY `idx_folio` (`folio`),
  ADD KEY `idx_fecha` (`fecha_transferencia`),
  ADD KEY `idx_estado` (`estado`),
  ADD KEY `fk_trans_usuario` (`usuario_id`),
  ADD KEY `fk_trans_usuario_recibe` (`usuario_recibe_id`);

--
-- Indices de la tabla `turnos`
--
ALTER TABLE `turnos`
  ADD PRIMARY KEY (`id`),
  ADD KEY `empresa_id` (`empresa_id`),
  ADD KEY `idx_turnos_estado` (`estado`),
  ADD KEY `idx_turnos_usuario` (`usuario_id`);

--
-- Indices de la tabla `turno_arqueo`
--
ALTER TABLE `turno_arqueo`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `turno_id` (`turno_id`);

--
-- Indices de la tabla `turno_gastos`
--
ALTER TABLE `turno_gastos`
  ADD PRIMARY KEY (`id`),
  ADD KEY `usuario_id` (`usuario_id`),
  ADD KEY `idx_gastos_turno` (`turno_id`);

--
-- Indices de la tabla `turno_inventario`
--
ALTER TABLE `turno_inventario`
  ADD PRIMARY KEY (`id`),
  ADD KEY `producto_id` (`producto_id`),
  ADD KEY `idx_turno_inventario_turno` (`turno_id`);

--
-- Indices de la tabla `turno_inventario_final`
--
ALTER TABLE `turno_inventario_final`
  ADD PRIMARY KEY (`id`),
  ADD KEY `producto_id` (`producto_id`),
  ADD KEY `idx_inv_final_turno` (`turno_id`);

--
-- Indices de la tabla `turno_mermas`
--
ALTER TABLE `turno_mermas`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_turno` (`turno_id`),
  ADD KEY `idx_empresa` (`empresa_id`);

--
-- Indices de la tabla `ubicaciones_config`
--
ALTER TABLE `ubicaciones_config`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_empresa_nivel` (`empresa_id`,`nivel`),
  ADD KEY `idx_empresa` (`empresa_id`);

--
-- Indices de la tabla `ubicaciones_valores`
--
ALTER TABLE `ubicaciones_valores`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_empresa_nivel_codigo` (`empresa_id`,`nivel`,`codigo`),
  ADD KEY `idx_empresa_nivel` (`empresa_id`,`nivel`),
  ADD KEY `idx_padre` (`padre_id`);

--
-- Indices de la tabla `unidades_medida`
--
ALTER TABLE `unidades_medida`
  ADD PRIMARY KEY (`id`);

--
-- Indices de la tabla `usuarios`
--
ALTER TABLE `usuarios`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `correo` (`correo`),
  ADD KEY `idx_contratante` (`contratante_id`),
  ADD KEY `idx_rango` (`rango`);

--
-- Indices de la tabla `usuario_areas`
--
ALTER TABLE `usuario_areas`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_usuario_area` (`usuario_id`,`area_id`),
  ADD KEY `idx_usuario` (`usuario_id`),
  ADD KEY `idx_area` (`area_id`);

--
-- Indices de la tabla `ventas`
--
ALTER TABLE `ventas`
  ADD PRIMARY KEY (`id`),
  ADD KEY `empresa_id` (`empresa_id`),
  ADD KEY `turno_id` (`turno_id`),
  ADD KEY `usuario_id` (`usuario_id`),
  ADD KEY `idx_tipo_factura` (`tipo_factura`),
  ADD KEY `idx_cfdi_uuid` (`cfdi_uuid`),
  ADD KEY `idx_cfdi_estado` (`cfdi_estado`),
  ADD KEY `fk_venta_empresa_destino` (`empresa_destino_id`),
  ADD KEY `fk_venta_contratante` (`contratante_id`);

--
-- Indices de la tabla `ventas_historicas`
--
ALTER TABLE `ventas_historicas`
  ADD PRIMARY KEY (`id`),
  ADD KEY `registro_id` (`registro_id`),
  ADD KEY `producto_id` (`producto_id`),
  ADD KEY `usuario_id` (`usuario_id`),
  ADD KEY `idx_fecha` (`fecha`),
  ADD KEY `idx_empresa_fecha` (`empresa_id`,`fecha`);

--
-- AUTO_INCREMENT de las tablas volcadas
--

--
-- AUTO_INCREMENT de la tabla `alertas_b2b`
--
ALTER TABLE `alertas_b2b`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `areas_produccion`
--
ALTER TABLE `areas_produccion`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=16;

--
-- AUTO_INCREMENT de la tabla `areas_sistema`
--
ALTER TABLE `areas_sistema`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=24;

--
-- AUTO_INCREMENT de la tabla `asientos_contables`
--
ALTER TABLE `asientos_contables`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=19;

--
-- AUTO_INCREMENT de la tabla `asientos_detalle`
--
ALTER TABLE `asientos_detalle`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=33;

--
-- AUTO_INCREMENT de la tabla `cajas`
--
ALTER TABLE `cajas`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT de la tabla `caja_botones`
--
ALTER TABLE `caja_botones`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `caja_ventas`
--
ALTER TABLE `caja_ventas`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT de la tabla `caja_ventas_detalle`
--
ALTER TABLE `caja_ventas_detalle`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=12;

--
-- AUTO_INCREMENT de la tabla `catalogo_inventario`
--
ALTER TABLE `catalogo_inventario`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `catalogo_modulos`
--
ALTER TABLE `catalogo_modulos`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- AUTO_INCREMENT de la tabla `catalogo_mp`
--
ALTER TABLE `catalogo_mp`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `cfdi_importados`
--
ALTER TABLE `cfdi_importados`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `cfdi_importados_detalle`
--
ALTER TABLE `cfdi_importados_detalle`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `cfdi_log`
--
ALTER TABLE `cfdi_log`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `compras`
--
ALTER TABLE `compras`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `consumos_internos`
--
ALTER TABLE `consumos_internos`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `consumos_propios`
--
ALTER TABLE `consumos_propios`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT de la tabla `contratantes`
--
ALTER TABLE `contratantes`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT de la tabla `cuentas_contables`
--
ALTER TABLE `cuentas_contables`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=123;

--
-- AUTO_INCREMENT de la tabla `cuentas_por_cobrar`
--
ALTER TABLE `cuentas_por_cobrar`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `cuentas_por_pagar`
--
ALTER TABLE `cuentas_por_pagar`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `detalle_compra`
--
ALTER TABLE `detalle_compra`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=15;

--
-- AUTO_INCREMENT de la tabla `detalle_venta`
--
ALTER TABLE `detalle_venta`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `empresas`
--
ALTER TABLE `empresas`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT de la tabla `empresa_configuracion`
--
ALTER TABLE `empresa_configuracion`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT de la tabla `empresa_modulos`
--
ALTER TABLE `empresa_modulos`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT de la tabla `facturas_b2b`
--
ALTER TABLE `facturas_b2b`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `facturas_b2b_detalle`
--
ALTER TABLE `facturas_b2b_detalle`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `facturas_notificaciones`
--
ALTER TABLE `facturas_notificaciones`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `factura_b2b_checklist`
--
ALTER TABLE `factura_b2b_checklist`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `factura_b2b_tracking`
--
ALTER TABLE `factura_b2b_tracking`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `historial_asignaciones_area`
--
ALTER TABLE `historial_asignaciones_area`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `historial_pagos`
--
ALTER TABLE `historial_pagos`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `incidencias`
--
ALTER TABLE `incidencias`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `incidencias_bitacora`
--
ALTER TABLE `incidencias_bitacora`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `inventario`
--
ALTER TABLE `inventario`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=22;

--
-- AUTO_INCREMENT de la tabla `inventario_movimientos`
--
ALTER TABLE `inventario_movimientos`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT de la tabla `inventario_mp`
--
ALTER TABLE `inventario_mp`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `inventario_pt`
--
ALTER TABLE `inventario_pt`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `invitaciones`
--
ALTER TABLE `invitaciones`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `listado_compras`
--
ALTER TABLE `listado_compras`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=53;

--
-- AUTO_INCREMENT de la tabla `mercancia`
--
ALTER TABLE `mercancia`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=67;

--
-- AUTO_INCREMENT de la tabla `mermas`
--
ALTER TABLE `mermas`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `movimientos_inventario`
--
ALTER TABLE `movimientos_inventario`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=21;

--
-- AUTO_INCREMENT de la tabla `notificaciones`
--
ALTER TABLE `notificaciones`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `notificaciones_usuario`
--
ALTER TABLE `notificaciones_usuario`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `ordenes_compra_automaticas`
--
ALTER TABLE `ordenes_compra_automaticas`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `ordenes_compra_automaticas_detalle`
--
ALTER TABLE `ordenes_compra_automaticas_detalle`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `ordenes_compra_b2b`
--
ALTER TABLE `ordenes_compra_b2b`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `ordenes_compra_b2b_detalle`
--
ALTER TABLE `ordenes_compra_b2b_detalle`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `ordenes_compra_tracking`
--
ALTER TABLE `ordenes_compra_tracking`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `ordenes_produccion`
--
ALTER TABLE `ordenes_produccion`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `orden_mp`
--
ALTER TABLE `orden_mp`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `orden_produccion`
--
ALTER TABLE `orden_produccion`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `pagos_b2b`
--
ALTER TABLE `pagos_b2b`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `paso_insumos`
--
ALTER TABLE `paso_insumos`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `paso_responsables`
--
ALTER TABLE `paso_responsables`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `presentaciones`
--
ALTER TABLE `presentaciones`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `procesos`
--
ALTER TABLE `procesos`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `proceso_pasos`
--
ALTER TABLE `proceso_pasos`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `produccion`
--
ALTER TABLE `produccion`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `produccion_detalle_mp`
--
ALTER TABLE `produccion_detalle_mp`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `productos_terminados`
--
ALTER TABLE `productos_terminados`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT de la tabla `producto_base`
--
ALTER TABLE `producto_base`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `proveedores`
--
ALTER TABLE `proveedores`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT de la tabla `pt_precios`
--
ALTER TABLE `pt_precios`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=49;

--
-- AUTO_INCREMENT de la tabla `pt_reglas_markup`
--
ALTER TABLE `pt_reglas_markup`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `rangos_organizacionales`
--
ALTER TABLE `rangos_organizacionales`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `registros_diarios`
--
ALTER TABLE `registros_diarios`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT de la tabla `relaciones_b2b`
--
ALTER TABLE `relaciones_b2b`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `retiros_efectivo`
--
ALTER TABLE `retiros_efectivo`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `roles_b2b_empresa`
--
ALTER TABLE `roles_b2b_empresa`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `subcuentas_contables`
--
ALTER TABLE `subcuentas_contables`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `suscripciones`
--
ALTER TABLE `suscripciones`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT de la tabla `tipo_inventario`
--
ALTER TABLE `tipo_inventario`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT de la tabla `transferencias_detalle`
--
ALTER TABLE `transferencias_detalle`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `transferencias_intercompany`
--
ALTER TABLE `transferencias_intercompany`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `turnos`
--
ALTER TABLE `turnos`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT de la tabla `turno_arqueo`
--
ALTER TABLE `turno_arqueo`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `turno_gastos`
--
ALTER TABLE `turno_gastos`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT de la tabla `turno_inventario`
--
ALTER TABLE `turno_inventario`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=13;

--
-- AUTO_INCREMENT de la tabla `turno_inventario_final`
--
ALTER TABLE `turno_inventario_final`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `turno_mermas`
--
ALTER TABLE `turno_mermas`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT de la tabla `ubicaciones_config`
--
ALTER TABLE `ubicaciones_config`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `ubicaciones_valores`
--
ALTER TABLE `ubicaciones_valores`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `unidades_medida`
--
ALTER TABLE `unidades_medida`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT de la tabla `usuarios`
--
ALTER TABLE `usuarios`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=29;

--
-- AUTO_INCREMENT de la tabla `usuario_areas`
--
ALTER TABLE `usuario_areas`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT de la tabla `ventas`
--
ALTER TABLE `ventas`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `ventas_historicas`
--
ALTER TABLE `ventas_historicas`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- Restricciones para tablas volcadas
--

--
-- Filtros para la tabla `areas_produccion`
--
ALTER TABLE `areas_produccion`
  ADD CONSTRAINT `areas_produccion_ibfk_1` FOREIGN KEY (`empresa_id`) REFERENCES `empresas` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `asientos_contables`
--
ALTER TABLE `asientos_contables`
  ADD CONSTRAINT `asientos_contables_ibfk_1` FOREIGN KEY (`producto_id`) REFERENCES `productos_terminados` (`id`),
  ADD CONSTRAINT `asientos_contables_ibfk_2` FOREIGN KEY (`mercancia_id`) REFERENCES `mercancia` (`id`),
  ADD CONSTRAINT `asientos_contables_ibfk_3` FOREIGN KEY (`cuenta_debe`) REFERENCES `cuentas_contables` (`id`),
  ADD CONSTRAINT `asientos_contables_ibfk_4` FOREIGN KEY (`cuenta_haber`) REFERENCES `cuentas_contables` (`id`);

--
-- Filtros para la tabla `asientos_detalle`
--
ALTER TABLE `asientos_detalle`
  ADD CONSTRAINT `asientos_detalle_ibfk_1` FOREIGN KEY (`asiento_id`) REFERENCES `asientos_contables` (`id`),
  ADD CONSTRAINT `asientos_detalle_ibfk_2` FOREIGN KEY (`cuenta_id`) REFERENCES `cuentas_contables` (`id`);

--
-- Filtros para la tabla `caja_ventas`
--
ALTER TABLE `caja_ventas`
  ADD CONSTRAINT `caja_ventas_ibfk_1` FOREIGN KEY (`turno_id`) REFERENCES `turnos` (`id`),
  ADD CONSTRAINT `caja_ventas_ibfk_2` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`);

--
-- Filtros para la tabla `caja_ventas_detalle`
--
ALTER TABLE `caja_ventas_detalle`
  ADD CONSTRAINT `caja_ventas_detalle_ibfk_1` FOREIGN KEY (`venta_id`) REFERENCES `caja_ventas` (`id`);

--
-- Filtros para la tabla `catalogo_inventario`
--
ALTER TABLE `catalogo_inventario`
  ADD CONSTRAINT `catalogo_inventario_ibfk_1` FOREIGN KEY (`empresa_id`) REFERENCES `empresas` (`id`);

--
-- Filtros para la tabla `catalogo_mp`
--
ALTER TABLE `catalogo_mp`
  ADD CONSTRAINT `catalogo_mp_ibfk_1` FOREIGN KEY (`empresa_id`) REFERENCES `empresas` (`id`);

--
-- Filtros para la tabla `cfdi_importados`
--
ALTER TABLE `cfdi_importados`
  ADD CONSTRAINT `cfdi_importados_ibfk_1` FOREIGN KEY (`empresa_id`) REFERENCES `empresas` (`id`),
  ADD CONSTRAINT `cfdi_importados_ibfk_2` FOREIGN KEY (`compra_id`) REFERENCES `compras` (`id`),
  ADD CONSTRAINT `cfdi_importados_ibfk_3` FOREIGN KEY (`venta_id`) REFERENCES `ventas` (`id`);

--
-- Filtros para la tabla `cfdi_importados_detalle`
--
ALTER TABLE `cfdi_importados_detalle`
  ADD CONSTRAINT `cfdi_importados_detalle_ibfk_1` FOREIGN KEY (`cfdi_id`) REFERENCES `cfdi_importados` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `cfdi_log`
--
ALTER TABLE `cfdi_log`
  ADD CONSTRAINT `fk_cfdi_empresa` FOREIGN KEY (`empresa_id`) REFERENCES `empresas` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_cfdi_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`),
  ADD CONSTRAINT `fk_cfdi_venta` FOREIGN KEY (`venta_id`) REFERENCES `ventas` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `compras`
--
ALTER TABLE `compras`
  ADD CONSTRAINT `fk_compra_contratante` FOREIGN KEY (`contratante_id`) REFERENCES `contratantes` (`id`);

--
-- Filtros para la tabla `consumos_internos`
--
ALTER TABLE `consumos_internos`
  ADD CONSTRAINT `consumos_internos_ibfk_1` FOREIGN KEY (`empresa_id`) REFERENCES `empresas` (`id`),
  ADD CONSTRAINT `consumos_internos_ibfk_2` FOREIGN KEY (`registro_id`) REFERENCES `registros_diarios` (`id`),
  ADD CONSTRAINT `consumos_internos_ibfk_3` FOREIGN KEY (`producto_id`) REFERENCES `mercancia` (`id`),
  ADD CONSTRAINT `consumos_internos_ibfk_4` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`);

--
-- Filtros para la tabla `consumos_propios`
--
ALTER TABLE `consumos_propios`
  ADD CONSTRAINT `consumos_propios_ibfk_1` FOREIGN KEY (`turno_id`) REFERENCES `turnos` (`id`),
  ADD CONSTRAINT `consumos_propios_ibfk_2` FOREIGN KEY (`producto_id`) REFERENCES `mercancia` (`id`),
  ADD CONSTRAINT `consumos_propios_ibfk_3` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`);

--
-- Filtros para la tabla `cuentas_contables`
--
ALTER TABLE `cuentas_contables`
  ADD CONSTRAINT `cuentas_contables_ibfk_1` FOREIGN KEY (`padre_id`) REFERENCES `cuentas_contables` (`id`);

--
-- Filtros para la tabla `cuentas_por_cobrar`
--
ALTER TABLE `cuentas_por_cobrar`
  ADD CONSTRAINT `cuentas_por_cobrar_ibfk_1` FOREIGN KEY (`empresa_id`) REFERENCES `empresas` (`id`),
  ADD CONSTRAINT `cuentas_por_cobrar_ibfk_2` FOREIGN KEY (`factura_b2b_id`) REFERENCES `facturas_b2b` (`id`),
  ADD CONSTRAINT `cuentas_por_cobrar_ibfk_3` FOREIGN KEY (`cfdi_id`) REFERENCES `cfdi_importados` (`id`),
  ADD CONSTRAINT `cuentas_por_cobrar_ibfk_4` FOREIGN KEY (`venta_id`) REFERENCES `ventas` (`id`),
  ADD CONSTRAINT `cuentas_por_cobrar_ibfk_5` FOREIGN KEY (`cliente_empresa_id`) REFERENCES `empresas` (`id`),
  ADD CONSTRAINT `cuentas_por_cobrar_ibfk_6` FOREIGN KEY (`autorizado_por_usuario_id`) REFERENCES `usuarios` (`id`);

--
-- Filtros para la tabla `cuentas_por_pagar`
--
ALTER TABLE `cuentas_por_pagar`
  ADD CONSTRAINT `cuentas_por_pagar_ibfk_1` FOREIGN KEY (`empresa_id`) REFERENCES `empresas` (`id`),
  ADD CONSTRAINT `cuentas_por_pagar_ibfk_2` FOREIGN KEY (`factura_b2b_id`) REFERENCES `facturas_b2b` (`id`),
  ADD CONSTRAINT `cuentas_por_pagar_ibfk_3` FOREIGN KEY (`cfdi_id`) REFERENCES `cfdi_importados` (`id`),
  ADD CONSTRAINT `cuentas_por_pagar_ibfk_4` FOREIGN KEY (`compra_id`) REFERENCES `compras` (`id`),
  ADD CONSTRAINT `cuentas_por_pagar_ibfk_5` FOREIGN KEY (`proveedor_empresa_id`) REFERENCES `empresas` (`id`),
  ADD CONSTRAINT `cuentas_por_pagar_ibfk_6` FOREIGN KEY (`autorizado_por_usuario_id`) REFERENCES `usuarios` (`id`);

--
-- Filtros para la tabla `detalle_compra`
--
ALTER TABLE `detalle_compra`
  ADD CONSTRAINT `detalle_compra_ibfk_1` FOREIGN KEY (`compra_id`) REFERENCES `listado_compras` (`id`),
  ADD CONSTRAINT `fk_dc_mercancia` FOREIGN KEY (`mercancia_id`) REFERENCES `mercancia` (`id`) ON DELETE SET NULL ON UPDATE CASCADE;

--
-- Filtros para la tabla `empresa_configuracion`
--
ALTER TABLE `empresa_configuracion`
  ADD CONSTRAINT `empresa_configuracion_ibfk_1` FOREIGN KEY (`empresa_id`) REFERENCES `empresas` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `empresa_modulos`
--
ALTER TABLE `empresa_modulos`
  ADD CONSTRAINT `fk_em_empresa` FOREIGN KEY (`empresa_id`) REFERENCES `empresas` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_em_modulo` FOREIGN KEY (`modulo_id`) REFERENCES `catalogo_modulos` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `facturas_b2b`
--
ALTER TABLE `facturas_b2b`
  ADD CONSTRAINT `facturas_b2b_ibfk_1` FOREIGN KEY (`empresa_emisora_id`) REFERENCES `empresas` (`id`),
  ADD CONSTRAINT `facturas_b2b_ibfk_2` FOREIGN KEY (`empresa_receptora_id`) REFERENCES `empresas` (`id`),
  ADD CONSTRAINT `facturas_b2b_ibfk_3` FOREIGN KEY (`recibida_por_usuario_id`) REFERENCES `usuarios` (`id`),
  ADD CONSTRAINT `facturas_b2b_ibfk_4` FOREIGN KEY (`emitida_por_usuario_id`) REFERENCES `usuarios` (`id`);

--
-- Filtros para la tabla `facturas_b2b_detalle`
--
ALTER TABLE `facturas_b2b_detalle`
  ADD CONSTRAINT `facturas_b2b_detalle_ibfk_1` FOREIGN KEY (`factura_id`) REFERENCES `facturas_b2b` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `facturas_b2b_detalle_ibfk_2` FOREIGN KEY (`mercancia_id`) REFERENCES `mercancia` (`id`),
  ADD CONSTRAINT `facturas_b2b_detalle_ibfk_3` FOREIGN KEY (`verificado_por_usuario_id`) REFERENCES `usuarios` (`id`);

--
-- Filtros para la tabla `facturas_notificaciones`
--
ALTER TABLE `facturas_notificaciones`
  ADD CONSTRAINT `facturas_notificaciones_ibfk_1` FOREIGN KEY (`empresa_destino_id`) REFERENCES `empresas` (`id`);

--
-- Filtros para la tabla `factura_b2b_checklist`
--
ALTER TABLE `factura_b2b_checklist`
  ADD CONSTRAINT `factura_b2b_checklist_ibfk_1` FOREIGN KEY (`factura_id`) REFERENCES `facturas_b2b` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `factura_b2b_tracking`
--
ALTER TABLE `factura_b2b_tracking`
  ADD CONSTRAINT `factura_b2b_tracking_ibfk_1` FOREIGN KEY (`factura_id`) REFERENCES `facturas_b2b` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `historial_asignaciones_area`
--
ALTER TABLE `historial_asignaciones_area`
  ADD CONSTRAINT `historial_asignaciones_area_ibfk_1` FOREIGN KEY (`empresa_id`) REFERENCES `empresas` (`id`),
  ADD CONSTRAINT `historial_asignaciones_area_ibfk_2` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`),
  ADD CONSTRAINT `historial_asignaciones_area_ibfk_3` FOREIGN KEY (`area_id`) REFERENCES `areas_sistema` (`id`),
  ADD CONSTRAINT `historial_asignaciones_area_ibfk_4` FOREIGN KEY (`realizado_por`) REFERENCES `usuarios` (`id`);

--
-- Filtros para la tabla `historial_pagos`
--
ALTER TABLE `historial_pagos`
  ADD CONSTRAINT `fk_pago_contratante` FOREIGN KEY (`contratante_id`) REFERENCES `contratantes` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_pago_suscripcion` FOREIGN KEY (`suscripcion_id`) REFERENCES `suscripciones` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `incidencias`
--
ALTER TABLE `incidencias`
  ADD CONSTRAINT `incidencias_ibfk_1` FOREIGN KEY (`empresa_id`) REFERENCES `empresas` (`id`),
  ADD CONSTRAINT `incidencias_ibfk_2` FOREIGN KEY (`area_id`) REFERENCES `areas_produccion` (`id`),
  ADD CONSTRAINT `incidencias_ibfk_3` FOREIGN KEY (`responsable_id`) REFERENCES `usuarios` (`id`),
  ADD CONSTRAINT `incidencias_ibfk_4` FOREIGN KEY (`created_by`) REFERENCES `usuarios` (`id`);

--
-- Filtros para la tabla `incidencias_bitacora`
--
ALTER TABLE `incidencias_bitacora`
  ADD CONSTRAINT `incidencias_bitacora_ibfk_1` FOREIGN KEY (`incidencia_id`) REFERENCES `incidencias` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `incidencias_bitacora_ibfk_2` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`);

--
-- Filtros para la tabla `inventario`
--
ALTER TABLE `inventario`
  ADD CONSTRAINT `fk_inv_mercancia` FOREIGN KEY (`mercancia_id`) REFERENCES `mercancia` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_inv_producto` FOREIGN KEY (`producto_id`) REFERENCES `productos_terminados` (`id`);

--
-- Filtros para la tabla `inventario_movimientos`
--
ALTER TABLE `inventario_movimientos`
  ADD CONSTRAINT `inventario_movimientos_ibfk_1` FOREIGN KEY (`tipo_inventario_id`) REFERENCES `tipo_inventario` (`id`),
  ADD CONSTRAINT `inventario_movimientos_ibfk_2` FOREIGN KEY (`mercancia_id`) REFERENCES `mercancia` (`id`);

--
-- Filtros para la tabla `invitaciones`
--
ALTER TABLE `invitaciones`
  ADD CONSTRAINT `invitaciones_ibfk_1` FOREIGN KEY (`empresa_id`) REFERENCES `empresas` (`id`),
  ADD CONSTRAINT `invitaciones_ibfk_2` FOREIGN KEY (`creada_por`) REFERENCES `usuarios` (`id`),
  ADD CONSTRAINT `invitaciones_ibfk_3` FOREIGN KEY (`usuario_creado_id`) REFERENCES `usuarios` (`id`);

--
-- Filtros para la tabla `mercancia`
--
ALTER TABLE `mercancia`
  ADD CONSTRAINT `fk_cuenta` FOREIGN KEY (`cuenta_id`) REFERENCES `cuentas_contables` (`id`),
  ADD CONSTRAINT `fk_mercancia_subcuenta_cc` FOREIGN KEY (`subcuenta_id`) REFERENCES `cuentas_contables` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_unidad` FOREIGN KEY (`unidad_id`) REFERENCES `unidades_medida` (`id`),
  ADD CONSTRAINT `mercancia_ibfk_1` FOREIGN KEY (`unidad_id`) REFERENCES `unidades_medida` (`id`),
  ADD CONSTRAINT `mercancia_ibfk_2` FOREIGN KEY (`cuenta_id`) REFERENCES `cuentas_contables` (`id`),
  ADD CONSTRAINT `mercancia_ibfk_3` FOREIGN KEY (`subcuenta_id`) REFERENCES `cuentas_contables` (`id`);

--
-- Filtros para la tabla `mermas`
--
ALTER TABLE `mermas`
  ADD CONSTRAINT `mermas_ibfk_1` FOREIGN KEY (`empresa_id`) REFERENCES `empresas` (`id`),
  ADD CONSTRAINT `mermas_ibfk_2` FOREIGN KEY (`registro_id`) REFERENCES `registros_diarios` (`id`),
  ADD CONSTRAINT `mermas_ibfk_3` FOREIGN KEY (`producto_id`) REFERENCES `mercancia` (`id`),
  ADD CONSTRAINT `mermas_ibfk_4` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`);

--
-- Filtros para la tabla `movimientos_inventario`
--
ALTER TABLE `movimientos_inventario`
  ADD CONSTRAINT `fk_mov_prod` FOREIGN KEY (`producto_id`) REFERENCES `productos_terminados` (`id`),
  ADD CONSTRAINT `movimientos_inventario_ibfk_1` FOREIGN KEY (`mercancia_id`) REFERENCES `mercancia` (`id`);

--
-- Filtros para la tabla `notificaciones`
--
ALTER TABLE `notificaciones`
  ADD CONSTRAINT `notificaciones_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `notificaciones_usuario`
--
ALTER TABLE `notificaciones_usuario`
  ADD CONSTRAINT `notificaciones_usuario_ibfk_1` FOREIGN KEY (`empresa_id`) REFERENCES `empresas` (`id`),
  ADD CONSTRAINT `notificaciones_usuario_ibfk_2` FOREIGN KEY (`usuario_destino_id`) REFERENCES `usuarios` (`id`),
  ADD CONSTRAINT `notificaciones_usuario_ibfk_3` FOREIGN KEY (`usuario_origen_id`) REFERENCES `usuarios` (`id`);

--
-- Filtros para la tabla `ordenes_compra_automaticas_detalle`
--
ALTER TABLE `ordenes_compra_automaticas_detalle`
  ADD CONSTRAINT `ordenes_compra_automaticas_detalle_ibfk_1` FOREIGN KEY (`orden_id`) REFERENCES `ordenes_compra_automaticas` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `ordenes_compra_b2b_detalle`
--
ALTER TABLE `ordenes_compra_b2b_detalle`
  ADD CONSTRAINT `ordenes_compra_b2b_detalle_ibfk_1` FOREIGN KEY (`orden_id`) REFERENCES `ordenes_compra_b2b` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `ordenes_compra_tracking`
--
ALTER TABLE `ordenes_compra_tracking`
  ADD CONSTRAINT `ordenes_compra_tracking_ibfk_1` FOREIGN KEY (`detalle_id`) REFERENCES `ordenes_compra_automaticas_detalle` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `ordenes_produccion`
--
ALTER TABLE `ordenes_produccion`
  ADD CONSTRAINT `ordenes_produccion_ibfk_1` FOREIGN KEY (`empresa_id`) REFERENCES `empresas` (`id`),
  ADD CONSTRAINT `ordenes_produccion_ibfk_2` FOREIGN KEY (`proceso_id`) REFERENCES `procesos` (`id`),
  ADD CONSTRAINT `ordenes_produccion_ibfk_3` FOREIGN KEY (`creado_por`) REFERENCES `usuarios` (`id`);

--
-- Filtros para la tabla `orden_mp`
--
ALTER TABLE `orden_mp`
  ADD CONSTRAINT `fk_omp_mp` FOREIGN KEY (`mp_mercancia_id`) REFERENCES `mercancia` (`id`) ON UPDATE CASCADE,
  ADD CONSTRAINT `fk_omp_orden` FOREIGN KEY (`orden_id`) REFERENCES `orden_produccion` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `orden_produccion`
--
ALTER TABLE `orden_produccion`
  ADD CONSTRAINT `fk_op_pt` FOREIGN KEY (`pt_mercancia_id`) REFERENCES `mercancia` (`id`) ON UPDATE CASCADE;

--
-- Filtros para la tabla `paso_insumos`
--
ALTER TABLE `paso_insumos`
  ADD CONSTRAINT `paso_insumos_ibfk_1` FOREIGN KEY (`paso_id`) REFERENCES `proceso_pasos` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `paso_insumos_ibfk_2` FOREIGN KEY (`mercancia_id`) REFERENCES `mercancia` (`id`),
  ADD CONSTRAINT `paso_insumos_ibfk_3` FOREIGN KEY (`unidad_id`) REFERENCES `unidades_medida` (`id`);

--
-- Filtros para la tabla `paso_responsables`
--
ALTER TABLE `paso_responsables`
  ADD CONSTRAINT `paso_responsables_ibfk_1` FOREIGN KEY (`paso_id`) REFERENCES `proceso_pasos` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `paso_responsables_ibfk_2` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `procesos`
--
ALTER TABLE `procesos`
  ADD CONSTRAINT `procesos_ibfk_1` FOREIGN KEY (`empresa_id`) REFERENCES `empresas` (`id`),
  ADD CONSTRAINT `procesos_ibfk_2` FOREIGN KEY (`producto_terminado_id`) REFERENCES `mercancia` (`id`),
  ADD CONSTRAINT `procesos_ibfk_3` FOREIGN KEY (`producto_wip_id`) REFERENCES `mercancia` (`id`),
  ADD CONSTRAINT `procesos_ibfk_4` FOREIGN KEY (`unidad_produccion_id`) REFERENCES `unidades_medida` (`id`);

--
-- Filtros para la tabla `proceso_pasos`
--
ALTER TABLE `proceso_pasos`
  ADD CONSTRAINT `proceso_pasos_ibfk_1` FOREIGN KEY (`proceso_id`) REFERENCES `procesos` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `proceso_pasos_ibfk_2` FOREIGN KEY (`area_id`) REFERENCES `areas_produccion` (`id`);

--
-- Filtros para la tabla `productos_terminados`
--
ALTER TABLE `productos_terminados`
  ADD CONSTRAINT `fk_pt_cuenta` FOREIGN KEY (`cuenta_id`) REFERENCES `cuentas_contables` (`id`),
  ADD CONSTRAINT `fk_pt_subcuenta` FOREIGN KEY (`subcuenta_id`) REFERENCES `cuentas_contables` (`id`),
  ADD CONSTRAINT `fk_pt_unidad` FOREIGN KEY (`unidad_id`) REFERENCES `unidades_medida` (`id`),
  ADD CONSTRAINT `productos_terminados_ibfk_1` FOREIGN KEY (`unidad_id`) REFERENCES `unidades_medida` (`id`),
  ADD CONSTRAINT `productos_terminados_ibfk_2` FOREIGN KEY (`cuenta_id`) REFERENCES `cuentas_contables` (`id`),
  ADD CONSTRAINT `productos_terminados_ibfk_3` FOREIGN KEY (`subcuenta_id`) REFERENCES `cuentas_contables` (`id`);

--
-- Filtros para la tabla `pt_precios`
--
ALTER TABLE `pt_precios`
  ADD CONSTRAINT `pt_precios_ibfk_1` FOREIGN KEY (`producto_id`) REFERENCES `mercancia` (`id`);

--
-- Filtros para la tabla `registros_diarios`
--
ALTER TABLE `registros_diarios`
  ADD CONSTRAINT `registros_diarios_ibfk_1` FOREIGN KEY (`empresa_id`) REFERENCES `empresas` (`id`),
  ADD CONSTRAINT `registros_diarios_ibfk_2` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`);

--
-- Filtros para la tabla `retiros_efectivo`
--
ALTER TABLE `retiros_efectivo`
  ADD CONSTRAINT `retiros_efectivo_ibfk_1` FOREIGN KEY (`turno_id`) REFERENCES `turnos` (`id`),
  ADD CONSTRAINT `retiros_efectivo_ibfk_2` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`);

--
-- Filtros para la tabla `subcuentas_contables`
--
ALTER TABLE `subcuentas_contables`
  ADD CONSTRAINT `subcuentas_contables_ibfk_1` FOREIGN KEY (`cuenta_id`) REFERENCES `cuentas_contables` (`id`);

--
-- Filtros para la tabla `suscripciones`
--
ALTER TABLE `suscripciones`
  ADD CONSTRAINT `fk_suscripcion_contratante` FOREIGN KEY (`contratante_id`) REFERENCES `contratantes` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `transferencias_detalle`
--
ALTER TABLE `transferencias_detalle`
  ADD CONSTRAINT `fk_transdet_transferencia` FOREIGN KEY (`transferencia_id`) REFERENCES `transferencias_intercompany` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `transferencias_intercompany`
--
ALTER TABLE `transferencias_intercompany`
  ADD CONSTRAINT `fk_trans_contratante` FOREIGN KEY (`contratante_id`) REFERENCES `contratantes` (`id`),
  ADD CONSTRAINT `fk_trans_destino` FOREIGN KEY (`empresa_destino_id`) REFERENCES `empresas` (`id`),
  ADD CONSTRAINT `fk_trans_origen` FOREIGN KEY (`empresa_origen_id`) REFERENCES `empresas` (`id`),
  ADD CONSTRAINT `fk_trans_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`),
  ADD CONSTRAINT `fk_trans_usuario_recibe` FOREIGN KEY (`usuario_recibe_id`) REFERENCES `usuarios` (`id`);

--
-- Filtros para la tabla `turnos`
--
ALTER TABLE `turnos`
  ADD CONSTRAINT `turnos_ibfk_1` FOREIGN KEY (`empresa_id`) REFERENCES `empresas` (`id`),
  ADD CONSTRAINT `turnos_ibfk_2` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`);

--
-- Filtros para la tabla `turno_arqueo`
--
ALTER TABLE `turno_arqueo`
  ADD CONSTRAINT `turno_arqueo_ibfk_1` FOREIGN KEY (`turno_id`) REFERENCES `turnos` (`id`);

--
-- Filtros para la tabla `turno_gastos`
--
ALTER TABLE `turno_gastos`
  ADD CONSTRAINT `turno_gastos_ibfk_1` FOREIGN KEY (`turno_id`) REFERENCES `turnos` (`id`),
  ADD CONSTRAINT `turno_gastos_ibfk_2` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`);

--
-- Filtros para la tabla `turno_inventario`
--
ALTER TABLE `turno_inventario`
  ADD CONSTRAINT `turno_inventario_ibfk_1` FOREIGN KEY (`turno_id`) REFERENCES `turnos` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `turno_inventario_ibfk_2` FOREIGN KEY (`producto_id`) REFERENCES `mercancia` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `turno_inventario_final`
--
ALTER TABLE `turno_inventario_final`
  ADD CONSTRAINT `turno_inventario_final_ibfk_1` FOREIGN KEY (`turno_id`) REFERENCES `turnos` (`id`),
  ADD CONSTRAINT `turno_inventario_final_ibfk_2` FOREIGN KEY (`producto_id`) REFERENCES `mercancia` (`id`);

--
-- Filtros para la tabla `ubicaciones_config`
--
ALTER TABLE `ubicaciones_config`
  ADD CONSTRAINT `fk_ubicacion_config_empresa` FOREIGN KEY (`empresa_id`) REFERENCES `empresas` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `ubicaciones_valores`
--
ALTER TABLE `ubicaciones_valores`
  ADD CONSTRAINT `fk_ubicacion_empresa` FOREIGN KEY (`empresa_id`) REFERENCES `empresas` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_ubicacion_padre` FOREIGN KEY (`padre_id`) REFERENCES `ubicaciones_valores` (`id`) ON DELETE SET NULL;

--
-- Filtros para la tabla `usuarios`
--
ALTER TABLE `usuarios`
  ADD CONSTRAINT `fk_usuario_rango` FOREIGN KEY (`rango`) REFERENCES `rangos_organizacionales` (`nivel`);

--
-- Filtros para la tabla `usuario_areas`
--
ALTER TABLE `usuario_areas`
  ADD CONSTRAINT `usuario_areas_fk_area_sistema` FOREIGN KEY (`area_id`) REFERENCES `areas_sistema` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `usuario_areas_ibfk_1` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `ventas`
--
ALTER TABLE `ventas`
  ADD CONSTRAINT `fk_venta_contratante` FOREIGN KEY (`contratante_id`) REFERENCES `contratantes` (`id`),
  ADD CONSTRAINT `fk_venta_empresa_destino` FOREIGN KEY (`empresa_destino_id`) REFERENCES `empresas` (`id`),
  ADD CONSTRAINT `ventas_ibfk_1` FOREIGN KEY (`empresa_id`) REFERENCES `empresas` (`id`),
  ADD CONSTRAINT `ventas_ibfk_2` FOREIGN KEY (`turno_id`) REFERENCES `turnos` (`id`),
  ADD CONSTRAINT `ventas_ibfk_3` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`);

--
-- Filtros para la tabla `ventas_historicas`
--
ALTER TABLE `ventas_historicas`
  ADD CONSTRAINT `ventas_historicas_ibfk_1` FOREIGN KEY (`empresa_id`) REFERENCES `empresas` (`id`),
  ADD CONSTRAINT `ventas_historicas_ibfk_2` FOREIGN KEY (`registro_id`) REFERENCES `registros_diarios` (`id`),
  ADD CONSTRAINT `ventas_historicas_ibfk_3` FOREIGN KEY (`producto_id`) REFERENCES `mercancia` (`id`),
  ADD CONSTRAINT `ventas_historicas_ibfk_4` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
