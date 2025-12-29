-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Servidor: 127.0.0.1
-- Tiempo de generación: 27-12-2025 a las 05:42:49
-- Versión del servidor: 10.4.32-MariaDB
-- Versión de PHP: 8.2.12

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
-- Estructura de tabla para la tabla `contratantes`
--

CREATE TABLE `contratantes` (
  `id` int(11) NOT NULL,
  `razon_social` varchar(255) NOT NULL,
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

INSERT INTO `contratantes` (`id`, `razon_social`, `rfc`, `email_contacto`, `telefono`, `direccion`, `ciudad`, `estado`, `cp`, `pais`, `activo`, `fecha_registro`, `fecha_suspension`, `notas`) VALUES
(1, 'Empresa Demo', 'XAXX010101000', 'demo@empresa.com', '0000000000', NULL, NULL, NULL, NULL, 'M?xico', 1, '2025-12-26 05:42:02', NULL, NULL);

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

--
-- Índices para tablas volcadas
--

--
-- Indices de la tabla `catalogo_modulos`
--
ALTER TABLE `catalogo_modulos`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `codigo` (`codigo`),
  ADD KEY `idx_codigo` (`codigo`),
  ADD KEY `idx_activo` (`activo`);

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
-- Indices de la tabla `contratantes`
--
ALTER TABLE `contratantes`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `rfc` (`rfc`),
  ADD UNIQUE KEY `email_contacto` (`email_contacto`),
  ADD KEY `idx_rfc` (`rfc`),
  ADD KEY `idx_email` (`email_contacto`),
  ADD KEY `idx_activo` (`activo`);

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
-- Indices de la tabla `historial_pagos`
--
ALTER TABLE `historial_pagos`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_suscripcion` (`suscripcion_id`),
  ADD KEY `idx_contratante` (`contratante_id`),
  ADD KEY `idx_fecha` (`fecha_pago`);

--
-- Indices de la tabla `rangos_organizacionales`
--
ALTER TABLE `rangos_organizacionales`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `nombre` (`nombre`),
  ADD UNIQUE KEY `nivel` (`nivel`);

--
-- Indices de la tabla `suscripciones`
--
ALTER TABLE `suscripciones`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_contratante` (`contratante_id`),
  ADD KEY `idx_estado` (`estado`),
  ADD KEY `idx_vencimiento` (`fecha_vencimiento`);

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
-- AUTO_INCREMENT de las tablas volcadas
--

--
-- AUTO_INCREMENT de la tabla `catalogo_modulos`
--
ALTER TABLE `catalogo_modulos`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- AUTO_INCREMENT de la tabla `cfdi_log`
--
ALTER TABLE `cfdi_log`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `contratantes`
--
ALTER TABLE `contratantes`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT de la tabla `empresa_modulos`
--
ALTER TABLE `empresa_modulos`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `historial_pagos`
--
ALTER TABLE `historial_pagos`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `rangos_organizacionales`
--
ALTER TABLE `rangos_organizacionales`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `suscripciones`
--
ALTER TABLE `suscripciones`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

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
-- Restricciones para tablas volcadas
--

--
-- Filtros para la tabla `cfdi_log`
--
ALTER TABLE `cfdi_log`
  ADD CONSTRAINT `fk_cfdi_empresa` FOREIGN KEY (`empresa_id`) REFERENCES `empresas` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_cfdi_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`),
  ADD CONSTRAINT `fk_cfdi_venta` FOREIGN KEY (`venta_id`) REFERENCES `ventas` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `empresa_modulos`
--
ALTER TABLE `empresa_modulos`
  ADD CONSTRAINT `fk_em_empresa` FOREIGN KEY (`empresa_id`) REFERENCES `empresas` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_em_modulo` FOREIGN KEY (`modulo_id`) REFERENCES `catalogo_modulos` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `historial_pagos`
--
ALTER TABLE `historial_pagos`
  ADD CONSTRAINT `fk_pago_contratante` FOREIGN KEY (`contratante_id`) REFERENCES `contratantes` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_pago_suscripcion` FOREIGN KEY (`suscripcion_id`) REFERENCES `suscripciones` (`id`) ON DELETE CASCADE;

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
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
