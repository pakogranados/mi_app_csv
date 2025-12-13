-- MariaDB dump 10.19  Distrib 10.4.32-MariaDB, for Win64 (AMD64)
--
-- Host: localhost    Database: miapp
-- ------------------------------------------------------
-- Server version	10.4.32-MariaDB

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `asientos_contables`
--

DROP TABLE IF EXISTS `asientos_contables`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `asientos_contables` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `fecha` timestamp NOT NULL DEFAULT current_timestamp(),
  `concepto` varchar(255) NOT NULL,
  `descripcion` varchar(255) DEFAULT NULL,
  `cuenta_debe` int(11) DEFAULT NULL,
  `cuenta_haber` int(11) DEFAULT NULL,
  `monto` decimal(12,2) NOT NULL,
  `producto_id` int(11) DEFAULT NULL,
  `mercancia_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `producto_id` (`producto_id`),
  KEY `mercancia_id` (`mercancia_id`),
  KEY `cuenta_debe` (`cuenta_debe`),
  KEY `cuenta_haber` (`cuenta_haber`),
  CONSTRAINT `asientos_contables_ibfk_1` FOREIGN KEY (`producto_id`) REFERENCES `productos_terminados` (`id`),
  CONSTRAINT `asientos_contables_ibfk_2` FOREIGN KEY (`mercancia_id`) REFERENCES `mercancia` (`id`),
  CONSTRAINT `asientos_contables_ibfk_3` FOREIGN KEY (`cuenta_debe`) REFERENCES `cuentas_contables` (`id`),
  CONSTRAINT `asientos_contables_ibfk_4` FOREIGN KEY (`cuenta_haber`) REFERENCES `cuentas_contables` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `asientos_contables`
--

LOCK TABLES `asientos_contables` WRITE;
/*!40000 ALTER TABLE `asientos_contables` DISABLE KEYS */;
INSERT INTO `asientos_contables` VALUES (1,'2025-08-19 16:29:33','','Entrada PT - Producto Terminado Test',NULL,NULL,1000.00,3,NULL),(3,'2025-08-28 01:29:35','Compra 75930',NULL,NULL,NULL,0.00,NULL,NULL),(4,'2025-08-28 01:30:59','Compra 45573',NULL,NULL,NULL,0.00,NULL,NULL),(5,'2025-08-28 01:38:33','Compra 1708825',NULL,NULL,NULL,0.00,NULL,NULL),(6,'2025-08-28 14:59:24','Compra 635',NULL,NULL,NULL,0.00,NULL,NULL),(7,'2025-08-28 15:13:13','Compra 51',NULL,NULL,NULL,0.00,NULL,NULL),(8,'2025-08-28 15:14:37','Compra 9 14',NULL,NULL,NULL,0.00,NULL,NULL),(9,'2025-08-28 16:04:58','Compra 5510',NULL,NULL,NULL,0.00,NULL,NULL),(10,'2025-08-28 16:11:44','Compra 15',NULL,NULL,NULL,0.00,NULL,NULL),(11,'2025-08-30 14:48:33','Compra 515',NULL,NULL,NULL,0.00,NULL,NULL),(12,'2025-09-01 05:17:35','Compra 100103',NULL,NULL,NULL,0.00,NULL,NULL),(13,'2025-09-01 05:18:24','Compra 100103',NULL,NULL,NULL,0.00,NULL,NULL),(14,'2025-09-01 05:19:50','Compra 100103',NULL,NULL,NULL,0.00,NULL,NULL),(15,'2025-09-01 06:14:50','Compra 100103',NULL,NULL,NULL,0.00,NULL,NULL),(16,'2025-09-01 06:25:05','Compra 100103',NULL,NULL,NULL,0.00,NULL,NULL),(17,'2025-09-04 02:03:48','Compra 5165',NULL,NULL,NULL,0.00,NULL,NULL),(18,'2025-09-04 02:27:04','Compra 51',NULL,NULL,NULL,0.00,NULL,NULL);
/*!40000 ALTER TABLE `asientos_contables` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `asientos_detalle`
--

DROP TABLE IF EXISTS `asientos_detalle`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `asientos_detalle` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `asiento_id` int(11) NOT NULL,
  `cuenta_id` int(11) NOT NULL,
  `debe` decimal(12,2) DEFAULT 0.00,
  `haber` decimal(12,2) DEFAULT 0.00,
  PRIMARY KEY (`id`),
  KEY `asiento_id` (`asiento_id`),
  KEY `cuenta_id` (`cuenta_id`),
  CONSTRAINT `asientos_detalle_ibfk_1` FOREIGN KEY (`asiento_id`) REFERENCES `asientos_contables` (`id`),
  CONSTRAINT `asientos_detalle_ibfk_2` FOREIGN KEY (`cuenta_id`) REFERENCES `cuentas_contables` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=33 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `asientos_detalle`
--

LOCK TABLES `asientos_detalle` WRITE;
/*!40000 ALTER TABLE `asientos_detalle` DISABLE KEYS */;
INSERT INTO `asientos_detalle` VALUES (1,3,10,34.00,0.00),(2,3,30,0.00,34.00),(3,4,10,1990.00,0.00),(4,4,30,0.00,1990.00),(5,5,10,379.80,0.00),(6,5,30,0.00,379.80),(7,6,10,212.00,0.00),(8,6,30,0.00,212.00),(9,7,10,212.00,0.00),(10,7,30,0.00,212.00),(11,8,10,212.00,0.00),(12,8,30,0.00,212.00),(13,9,10,51.00,0.00),(14,9,30,0.00,51.00),(15,10,10,212.00,0.00),(16,10,30,0.00,212.00),(17,11,10,0.00,0.00),(18,11,30,0.00,0.00),(19,12,10,384.26,0.00),(20,12,30,0.00,384.26),(21,13,10,584.26,0.00),(22,13,30,0.00,584.26),(23,14,10,615.00,0.00),(24,14,30,0.00,615.00),(25,15,10,615.00,0.00),(26,15,30,0.00,615.00),(27,16,10,615.00,0.00),(28,16,30,0.00,615.00),(29,17,10,212.00,0.00),(30,17,30,0.00,212.00),(31,18,10,615.00,0.00),(32,18,30,0.00,615.00);
/*!40000 ALTER TABLE `asientos_detalle` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `compras`
--

DROP TABLE IF EXISTS `compras`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `compras` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `fecha` date DEFAULT NULL,
  `proveedor` varchar(255) DEFAULT NULL,
  `numero_factura` varchar(50) DEFAULT NULL,
  `total` decimal(10,2) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `compras`
--

LOCK TABLES `compras` WRITE;
/*!40000 ALTER TABLE `compras` DISABLE KEYS */;
/*!40000 ALTER TABLE `compras` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `cuentas_contables`
--

DROP TABLE IF EXISTS `cuentas_contables`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `cuentas_contables` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `codigo` varchar(20) NOT NULL,
  `nombre` varchar(255) NOT NULL,
  `tipo` enum('Activo','Pasivo','Patrimonio','Ingresos','Gastos') NOT NULL,
  `naturaleza` enum('Deudora','Acreedora') NOT NULL,
  `nivel` tinyint(4) NOT NULL,
  `padre_id` int(11) DEFAULT NULL,
  `permite_subcuentas` tinyint(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  UNIQUE KEY `codigo` (`codigo`),
  KEY `cuenta_padre_id` (`padre_id`),
  CONSTRAINT `cuentas_contables_ibfk_1` FOREIGN KEY (`padre_id`) REFERENCES `cuentas_contables` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=123 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cuentas_contables`
--

LOCK TABLES `cuentas_contables` WRITE;
/*!40000 ALTER TABLE `cuentas_contables` DISABLE KEYS */;
INSERT INTO `cuentas_contables` VALUES (1,'100-000-000','ACTIVO','Activo','Deudora',1,NULL,0),(2,'200-000-000','PASIVO','Pasivo','Acreedora',1,NULL,0),(3,'300-000-000','PATRIMONIO','Patrimonio','Acreedora',1,NULL,0),(4,'110-000-000','ACTIVO CIRCULANTE','Activo','Deudora',1,1,0),(5,'112-000-000','INVENTARIOS','Activo','Deudora',1,4,0),(6,'112-001-000','MERCANCÍAS','Activo','Deudora',2,5,1),(7,'112-001-001','AZUCAR 2KG','Activo','Deudora',3,6,0),(8,'111-000-000','EFECTIVO Y EQUIVALENTES','Activo','Deudora',1,4,0),(9,'111-001-000','CAJA','Activo','Deudora',2,8,0),(10,'111-002-000','BANCOS','Activo','Deudora',2,8,0),(11,'111-003-000','CUENTAS DE TERCEROS','Activo','Deudora',2,8,1),(12,'111-004-000','OTROS EFECTIVOS','Activo','Deudora',2,8,0),(13,'112-002-000','MATERIAS PRIMAS','Activo','Deudora',2,5,1),(14,'112-003-000','PRODUCTOS EN PROCESO','Activo','Deudora',2,5,1),(15,'113-000-000','CUENTAS POR COBRAR','Activo','Deudora',1,4,0),(16,'113-001-000','CLIENTES','Activo','Deudora',2,15,1),(17,'113-002-000','DEUDORES DIVERSOS','Activo','Deudora',2,15,1),(18,'114-000-000','OTROS ACTIVOS CIRCULANTES','Activo','Deudora',1,4,0),(19,'114-001-000','ANTICIPOS','Activo','Deudora',2,18,1),(20,'114-002-000','IMPUESTOS A FAVOR','Activo','Deudora',2,18,1),(21,'130-000-000','INVENTARIOS (ALTERNOS)','Activo','Deudora',1,1,0),(22,'130-001-000','MERCANCÍAS A','Activo','Deudora',2,21,1),(23,'130-002-000','MERCANCÍAS B','Activo','Deudora',2,21,1),(24,'130-003-000','MERCANCÍAS C','Activo','Deudora',2,21,1),(25,'130-004-000','MERCANCÍAS D','Activo','Deudora',2,21,1),(26,'130-005-000','MERCANCÍAS E','Activo','Deudora',2,21,1),(27,'130-006-000','MERCANCÍAS F','Activo','Deudora',2,21,1),(28,'130-007-000','MERCANCÍAS G','Activo','Deudora',2,21,1),(29,'130-008-000','MERCANCÍAS H','Activo','Deudora',2,21,1),(30,'150-000-000','ACTIVO NO CIRCULANTE','Activo','Deudora',1,1,0),(31,'151-000-000','ACTIVOS FIJOS','Activo','Deudora',1,30,0),(32,'151-001-000','MOBILIARIO Y EQUIPO','Activo','Deudora',2,31,1),(33,'151-002-000','EQUIPO DE CÓMPUTO','Activo','Deudora',2,31,1),(34,'151-003-000','EQUIPO DE TRANSPORTE','Activo','Deudora',2,31,1),(35,'151-004-000','OTROS ACTIVOS FIJOS','Activo','Deudora',2,31,1),(36,'210-000-000','PASIVO CIRCULANTE','Pasivo','Acreedora',1,2,0),(37,'211-000-000','PROVEEDORES Y ACREEDORES','Pasivo','Acreedora',1,36,0),(38,'211-001-000','PROVEEDORES','Pasivo','Acreedora',2,37,1),(39,'211-002-000','ACREEDORES','Pasivo','Acreedora',2,37,1),(40,'212-000-000','PASIVOS ACUMULADOS','Pasivo','Acreedora',1,36,0),(41,'212-001-000','IMPUESTOS POR PAGAR','Pasivo','Acreedora',2,40,1),(42,'212-002-000','OTROS PASIVOS','Pasivo','Acreedora',2,40,0),(43,'220-000-000','PASIVO A LARGO PLAZO','Pasivo','Acreedora',1,2,0),(44,'221-000-000','CRÉDITOS DE LARGO PLAZO','Pasivo','Acreedora',1,43,0),(45,'221-001-000','CRÉDITOS BANCARIOS','Pasivo','Acreedora',2,44,1),(46,'301-000-000','CAPITAL SOCIAL Y RESULTADOS','Patrimonio','Acreedora',1,3,0),(47,'301-001-000','CAPITAL SOCIAL','Patrimonio','Acreedora',2,46,0),(48,'301-002-000','RESERVAS','Patrimonio','Acreedora',2,46,0),(49,'301-003-000','RESULTADOS ACUMULADOS','Patrimonio','Acreedora',2,46,0),(50,'301-004-000','RESULTADO DEL EJERCICIO','Patrimonio','Acreedora',2,46,0),(51,'400-000-000','INGRESOS','Ingresos','Acreedora',1,NULL,0),(52,'401-000-000','INGRESOS ORDINARIOS','Ingresos','Acreedora',1,51,0),(53,'401-001-000','VENTAS','Ingresos','Acreedora',2,52,1),(54,'402-000-000','OTROS INGRESOS','Ingresos','Acreedora',1,51,0),(55,'402-001-000','OTROS PRODUCTOS','Ingresos','Acreedora',2,54,1),(56,'500-000-000','COSTOS Y CUENTAS RELACIONADAS','Gastos','Deudora',1,NULL,0),(57,'501-000-000','COSTO DE VENTAS','Gastos','Deudora',1,56,0),(58,'501-001-000','COSTO MERCANCÍAS','Gastos','Deudora',2,57,1),(59,'501-002-000','OTROS COSTOS','Gastos','Deudora',2,57,1),(60,'502-000-000','CLIENTES / CUENTAS RELACIONADAS','Gastos','Deudora',1,56,1),(61,'600-000-000','GASTOS','Gastos','Deudora',1,NULL,1),(62,'600-001-001','Sueldos y Salarios','Gastos','Deudora',3,108,0),(63,'600-001-002','Horas Extras','Gastos','Deudora',3,108,0),(64,'600-001-003','Comisiones de venta','Gastos','Deudora',3,108,0),(65,'600-001-004','Renta','Gastos','Deudora',3,108,0),(66,'600-001-005','Mejoras en Imagen','Gastos','Deudora',3,108,0),(67,'600-001-006','Luz','Gastos','Deudora',3,108,0),(68,'600-001-007','Agua','Gastos','Deudora',3,108,0),(69,'600-001-008','Gas','Gastos','Deudora',3,108,0),(70,'600-001-009','Aseguranza','Gastos','Deudora',3,108,0),(71,'600-001-010','Articulos de limpieza','Gastos','Deudora',3,108,0),(72,'600-001-011','Mantenimiento de equipo','Gastos','Deudora',3,108,0),(73,'600-001-012','Suministro de oficina','Gastos','Deudora',3,108,0),(74,'600-001-013','Gasolina','Gastos','Deudora',3,108,0),(75,'600-001-014','Publicidad','Gastos','Deudora',3,108,0),(76,'600-001-015','Reclutamiento','Gastos','Deudora',3,108,0),(77,'600-001-016','Capacitaci?n','Gastos','Deudora',3,108,0),(78,'600-001-017','Gastos de Transporte','Gastos','Deudora',3,108,0),(79,'600-001-018','Comida empleados','Gastos','Deudora',3,108,0),(80,'600-001-019','Cortesias empleados','Gastos','Deudora',3,108,0),(81,'600-001-020','Gastos Varios','Gastos','Deudora',3,108,0),(82,'600-001-021','Gastos Corporativos','Gastos','Deudora',3,108,0),(83,'600-001-022','Intereses financieros','Gastos','Deudora',3,108,0),(84,'600-001-023','Comisiones bancarias','Gastos','Deudora',3,108,0),(85,'600-001-024','ISR','Gastos','Deudora',3,108,0),(86,'600-001-025','IEPS','Gastos','Deudora',3,108,0),(87,'212-002-001','OTRO PASIVO 001','Pasivo','Acreedora',3,42,0),(88,'212-002-002','OTRO PASIVO 002','Pasivo','Acreedora',3,42,0),(89,'212-002-003','OTRO PASIVO 003','Pasivo','Acreedora',3,42,0),(90,'212-002-004','OTRO PASIVO 004','Pasivo','Acreedora',3,42,0),(91,'212-002-005','OTRO PASIVO 005','Pasivo','Acreedora',3,42,0),(92,'212-002-006','OTRO PASIVO 006','Pasivo','Acreedora',3,42,0),(93,'212-002-007','OTRO PASIVO 007','Pasivo','Acreedora',3,42,0),(94,'212-002-008','OTRO PASIVO 008','Pasivo','Acreedora',3,42,0),(95,'212-002-009','OTRO PASIVO 009','Pasivo','Acreedora',3,42,0),(96,'212-002-010','OTRO PASIVO 010','Pasivo','Acreedora',3,42,0),(97,'301-003-001','RESULTADOS ACUMULADOS DETALLE','Patrimonio','Acreedora',3,49,0),(98,'301-004-001','RESULTADO 001','Patrimonio','Acreedora',3,50,0),(99,'301-004-002','RESULTADO 002','Patrimonio','Acreedora',3,50,0),(100,'301-004-003','RESULTADO 003','Patrimonio','Acreedora',3,50,0),(101,'301-004-004','RESULTADO 004','Patrimonio','Acreedora',3,50,0),(102,'301-004-005','RESULTADO 005','Patrimonio','Acreedora',3,50,0),(103,'301-004-006','RESULTADO 006','Patrimonio','Acreedora',3,50,0),(104,'301-004-007','RESULTADO 007','Patrimonio','Acreedora',3,50,0),(105,'301-004-008','RESULTADO 008','Patrimonio','Acreedora',3,50,0),(106,'301-004-009','RESULTADO 009','Patrimonio','Acreedora',3,50,0),(107,'112-001-002','AZUCAR 5KG','Activo','Deudora',3,6,0),(108,'600-001-000','GASTOS OPERATIVOS','Gastos','Deudora',2,61,1),(109,'600-001-026','IVA','Gastos','Deudora',3,108,0),(110,'112-001-003','HIELO','Activo','Deudora',3,6,0),(111,'112-001-004','GASOLINA','Activo','Deudora',3,6,0),(112,'112-001-005','AZUCAR 1 KG','Activo','Deudora',3,6,0),(113,'112-001-006','CACAHUATE','Activo','Deudora',3,6,0),(114,'112-001-007','CAJETA 1KG','Activo','Deudora',3,6,0),(115,'112-001-008','CAJETA 5KG','Activo','Deudora',3,6,0),(116,'112-001-009','CONO WAFFLE','Activo','Deudora',3,6,0),(117,'112-001-010','CONO CHOCOLATE','Activo','Deudora',3,6,0),(118,'112-001-011','IEPS','Activo','Deudora',3,6,0),(119,'112-001-012','IVA','Activo','Deudora',3,6,0),(120,'112-001-013','HARINA PARA BROWNIES 3.4KG','Activo','Deudora',3,6,0),(121,'112-001-014','HARINA PARA BROWNIES 2.26KG','Activo','Deudora',3,6,0),(122,'112-001-015','FRESA 1KG','Activo','Deudora',3,6,0);
/*!40000 ALTER TABLE `cuentas_contables` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `detalle_compra`
--

DROP TABLE IF EXISTS `detalle_compra`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `detalle_compra` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `compra_id` int(11) NOT NULL,
  `mercancia_id` int(11) DEFAULT NULL,
  `producto` varchar(255) DEFAULT NULL,
  `unidades` decimal(10,2) DEFAULT NULL,
  `precio_unitario` decimal(10,2) DEFAULT NULL,
  `precio_total` decimal(10,2) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `compra_id` (`compra_id`),
  KEY `idx_dc_mercancia` (`mercancia_id`),
  CONSTRAINT `detalle_compra_ibfk_1` FOREIGN KEY (`compra_id`) REFERENCES `listado_compras` (`id`),
  CONSTRAINT `fk_dc_mercancia` FOREIGN KEY (`mercancia_id`) REFERENCES `mercancia` (`id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `detalle_compra`
--

LOCK TABLES `detalle_compra` WRITE;
/*!40000 ALTER TABLE `detalle_compra` DISABLE KEYS */;
INSERT INTO `detalle_compra` VALUES (6,37,38,'Hielo',1.00,34.00,34.00),(7,38,NULL,'Nieve Chocolate',1.00,595.00,595.00),(8,38,NULL,'Nieve Vainilla',1.00,585.00,585.00),(9,38,NULL,'Cono Chocolate',1.00,810.00,810.00),(10,39,39,'Gasolina',1.00,379.80,379.80);
/*!40000 ALTER TABLE `detalle_compra` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `detalle_venta`
--

DROP TABLE IF EXISTS `detalle_venta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `detalle_venta` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `producto_terminado_id` int(11) DEFAULT NULL,
  `venta_id` int(11) NOT NULL,
  `mercancia_id` int(11) NOT NULL,
  `unidades` decimal(10,2) NOT NULL,
  `precio_unitario` decimal(10,2) NOT NULL,
  `fecha` date NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `detalle_venta`
--

LOCK TABLES `detalle_venta` WRITE;
/*!40000 ALTER TABLE `detalle_venta` DISABLE KEYS */;
/*!40000 ALTER TABLE `detalle_venta` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `inventario`
--

DROP TABLE IF EXISTS `inventario`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `inventario` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `mercancia_id` int(11) DEFAULT NULL,
  `producto_id` int(11) DEFAULT NULL,
  `producto` varchar(100) NOT NULL,
  `inventario_inicial` int(11) DEFAULT 0,
  `entradas` int(11) DEFAULT 0,
  `salidas` int(11) DEFAULT 0,
  `aprobado` tinyint(1) DEFAULT 0,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_inv_mercancia` (`mercancia_id`),
  UNIQUE KEY `uq_inv_producto` (`producto_id`),
  CONSTRAINT `fk_inv_mercancia` FOREIGN KEY (`mercancia_id`) REFERENCES `mercancia` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_inv_producto` FOREIGN KEY (`producto_id`) REFERENCES `productos_terminados` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `inventario`
--

LOCK TABLES `inventario` WRITE;
/*!40000 ALTER TABLE `inventario` DISABLE KEYS */;
INSERT INTO `inventario` VALUES (1,NULL,NULL,'Hielo',0,1,0,0),(2,NULL,NULL,'Nieve Chocolate',0,1,0,0),(3,NULL,NULL,'Nieve Vainilla',0,1,0,0),(4,NULL,NULL,'Cono Chocolate',0,1,0,0),(5,NULL,NULL,'Gasolina',0,1,0,0),(9,54,NULL,'Fresa 1kg',0,1,0,0);
/*!40000 ALTER TABLE `inventario` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `inventario_movimientos`
--

DROP TABLE IF EXISTS `inventario_movimientos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `inventario_movimientos` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `tipo_inventario_id` int(11) NOT NULL,
  `mercancia_id` int(11) NOT NULL,
  `fecha` date NOT NULL,
  `tipo_movimiento` enum('entrada','salida') NOT NULL,
  `unidades` decimal(10,2) NOT NULL,
  `precio_unitario` decimal(10,2) NOT NULL,
  `referencia` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `mercancia_id` (`mercancia_id`),
  KEY `idx_mv_fase_prod_fecha` (`tipo_inventario_id`,`mercancia_id`,`fecha`),
  KEY `idx_mv_tipo` (`tipo_movimiento`),
  CONSTRAINT `inventario_movimientos_ibfk_1` FOREIGN KEY (`tipo_inventario_id`) REFERENCES `tipo_inventario` (`id`),
  CONSTRAINT `inventario_movimientos_ibfk_2` FOREIGN KEY (`mercancia_id`) REFERENCES `mercancia` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `inventario_movimientos`
--

LOCK TABLES `inventario_movimientos` WRITE;
/*!40000 ALTER TABLE `inventario_movimientos` DISABLE KEYS */;
INSERT INTO `inventario_movimientos` VALUES (2,1,54,'2025-09-03','',1.00,615.00,'51');
/*!40000 ALTER TABLE `inventario_movimientos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `inventario_mp`
--

DROP TABLE IF EXISTS `inventario_mp`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `inventario_mp` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `mercancia_id` int(11) NOT NULL,
  `producto` varchar(255) NOT NULL,
  `inventario_inicial` decimal(10,2) DEFAULT 0.00,
  `entradas` decimal(10,2) DEFAULT 0.00,
  `salidas` decimal(10,2) DEFAULT 0.00,
  `aprobado` tinyint(4) DEFAULT 0,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `inventario_mp`
--

LOCK TABLES `inventario_mp` WRITE;
/*!40000 ALTER TABLE `inventario_mp` DISABLE KEYS */;
/*!40000 ALTER TABLE `inventario_mp` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `inventario_pt`
--

DROP TABLE IF EXISTS `inventario_pt`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `inventario_pt` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `producto_id` int(11) NOT NULL,
  `inventario_inicial` decimal(10,2) DEFAULT 0.00,
  `entradas` decimal(10,2) DEFAULT 0.00,
  `precio_unitario` decimal(10,2) DEFAULT NULL,
  `salidas` decimal(10,2) DEFAULT 0.00,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `inventario_pt`
--

LOCK TABLES `inventario_pt` WRITE;
/*!40000 ALTER TABLE `inventario_pt` DISABLE KEYS */;
/*!40000 ALTER TABLE `inventario_pt` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `listado_compras`
--

DROP TABLE IF EXISTS `listado_compras`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `listado_compras` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `fecha` datetime DEFAULT NULL,
  `numero_factura` varchar(50) DEFAULT NULL,
  `proveedor` varchar(255) DEFAULT NULL,
  `total` decimal(10,2) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=53 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `listado_compras`
--

LOCK TABLES `listado_compras` WRITE;
/*!40000 ALTER TABLE `listado_compras` DISABLE KEYS */;
INSERT INTO `listado_compras` VALUES (37,'2025-08-01 00:00:00','75930','Del Rio',34.00),(38,'2025-08-01 00:00:00','45573','Vani',1990.00),(39,'2025-08-01 00:00:00','1708825','Gazpro',379.80);
/*!40000 ALTER TABLE `listado_compras` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `mercancia`
--

DROP TABLE IF EXISTS `mercancia`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `mercancia` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
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
  PRIMARY KEY (`id`),
  KEY `fk_unidad` (`unidad_id`),
  KEY `fk_cuenta` (`cuenta_id`),
  KEY `fk_mercancia_subcuenta_cc` (`subcuenta_id`),
  CONSTRAINT `fk_cuenta` FOREIGN KEY (`cuenta_id`) REFERENCES `cuentas_contables` (`id`),
  CONSTRAINT `fk_mercancia_subcuenta_cc` FOREIGN KEY (`subcuenta_id`) REFERENCES `cuentas_contables` (`id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `fk_unidad` FOREIGN KEY (`unidad_id`) REFERENCES `unidades_medida` (`id`),
  CONSTRAINT `mercancia_ibfk_1` FOREIGN KEY (`unidad_id`) REFERENCES `unidades_medida` (`id`),
  CONSTRAINT `mercancia_ibfk_2` FOREIGN KEY (`cuenta_id`) REFERENCES `cuentas_contables` (`id`),
  CONSTRAINT `mercancia_ibfk_3` FOREIGN KEY (`subcuenta_id`) REFERENCES `cuentas_contables` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=55 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `mercancia`
--

LOCK TABLES `mercancia` WRITE;
/*!40000 ALTER TABLE `mercancia` DISABLE KEYS */;
INSERT INTO `mercancia` VALUES (32,'Azucar 2kg',0.00,3,'2000',6,7,0,0,0,0),(33,'Azucar 5kg',0.00,3,'5000',6,107,0,0,0,0),(35,'Producto Prueba',0.00,1,'1.00',NULL,NULL,0,0,0,0),(36,'Materia Prima Test',0.00,1,'100',NULL,NULL,0,0,0,0),(38,'Hielo',0.00,3,'5000',6,110,0,0,0,0),(39,'Gasolina',0.00,2,'1',NULL,74,0,0,0,0),(40,'Azucar 1 kg',0.00,3,'1000',6,112,0,0,0,0),(41,'Cacahuate',0.00,3,'1000',6,113,0,0,0,0),(42,'Cajeta 1kg',0.00,3,'1000',6,114,0,0,0,0),(43,'Cajeta 5kg',0.00,3,'5000',6,115,0,0,0,0),(47,'Cono Waffle',0.00,1,'125',6,116,0,1,0,0),(48,'Cono Chocolate',0.00,1,'360',6,117,0,0,0,0),(49,'IEPS',0.00,1,'1',NULL,86,0,0,0,0),(50,'IVA',0.00,1,'1',NULL,109,0,0,0,0),(51,'Harina para Brownies 3.4kg',0.00,3,'3400',6,120,1,0,0,0),(52,'Harina para Brownies 2.26kg',0.00,3,'2260',6,121,1,0,0,0),(53,'Cacahuate',0.00,3,'1000',6,113,0,0,0,0),(54,'Fresa 1kg',0.00,3,'1000',6,122,0,0,0,0);
/*!40000 ALTER TABLE `mercancia` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `movimientos_inventario`
--

DROP TABLE IF EXISTS `movimientos_inventario`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `movimientos_inventario` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `mercancia_id` int(11) DEFAULT NULL,
  `producto_id` int(11) DEFAULT NULL,
  `tipo` enum('entrada','salida') NOT NULL,
  `cantidad` decimal(12,2) NOT NULL,
  `costo_unitario` decimal(12,2) NOT NULL,
  `referencia` varchar(255) DEFAULT NULL,
  `fecha` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `mercancia_id` (`mercancia_id`),
  KEY `fk_mov_prod` (`producto_id`),
  CONSTRAINT `fk_mov_prod` FOREIGN KEY (`producto_id`) REFERENCES `productos_terminados` (`id`),
  CONSTRAINT `movimientos_inventario_ibfk_1` FOREIGN KEY (`mercancia_id`) REFERENCES `mercancia` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=21 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `movimientos_inventario`
--

LOCK TABLES `movimientos_inventario` WRITE;
/*!40000 ALTER TABLE `movimientos_inventario` DISABLE KEYS */;
INSERT INTO `movimientos_inventario` VALUES (4,35,NULL,'entrada',10.00,0.00,NULL,'2025-08-16 01:26:31'),(9,36,NULL,'entrada',50.00,12.50,NULL,'2025-08-17 02:57:31'),(10,36,NULL,'salida',10.00,12.50,NULL,'2025-08-17 02:57:47'),(11,NULL,3,'entrada',20.00,0.00,NULL,'2025-08-17 02:58:01'),(12,NULL,3,'salida',5.00,0.00,NULL,'2025-08-17 02:58:14'),(13,NULL,3,'salida',5.00,0.00,NULL,'2025-08-17 03:01:23'),(14,36,NULL,'entrada',50.00,12.50,NULL,'2025-08-17 03:01:41'),(15,36,NULL,'salida',10.00,12.50,NULL,'2025-08-17 03:01:56'),(16,NULL,3,'entrada',50.00,20.00,'Producci?n Lote 001','2025-08-18 04:53:21'),(17,NULL,3,'salida',10.00,20.00,'Venta Cliente X','2025-08-18 04:53:46'),(18,NULL,1,'entrada',50.00,20.00,'Producci?n Lote 001','2025-08-18 05:03:19'),(19,NULL,3,'entrada',50.00,20.00,'Producci?n Lote Test','2025-08-19 16:29:33');
/*!40000 ALTER TABLE `movimientos_inventario` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER trg_mov_inventario_entrada
AFTER INSERT ON movimientos_inventario
FOR EACH ROW
BEGIN
    
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
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER trg_mov_inventario_salida
AFTER INSERT ON movimientos_inventario
FOR EACH ROW
BEGIN
    
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
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER trg_contable_pt
AFTER INSERT ON movimientos_inventario
FOR EACH ROW
BEGIN
    
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
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `orden_mp`
--

DROP TABLE IF EXISTS `orden_mp`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `orden_mp` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `orden_id` bigint(20) NOT NULL,
  `mp_mercancia_id` int(11) NOT NULL,
  `unidades` decimal(14,4) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_omp_orden` (`orden_id`),
  KEY `idx_omp_mp` (`mp_mercancia_id`),
  CONSTRAINT `fk_omp_mp` FOREIGN KEY (`mp_mercancia_id`) REFERENCES `mercancia` (`id`) ON UPDATE CASCADE,
  CONSTRAINT `fk_omp_orden` FOREIGN KEY (`orden_id`) REFERENCES `orden_produccion` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `orden_mp`
--

LOCK TABLES `orden_mp` WRITE;
/*!40000 ALTER TABLE `orden_mp` DISABLE KEYS */;
/*!40000 ALTER TABLE `orden_mp` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `orden_produccion`
--

DROP TABLE IF EXISTS `orden_produccion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `orden_produccion` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `fecha` datetime NOT NULL DEFAULT current_timestamp(),
  `pt_mercancia_id` int(11) NOT NULL,
  `cantidad` decimal(14,4) NOT NULL,
  `estado` enum('abierta','cerrada') NOT NULL DEFAULT 'abierta',
  `referencia` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_op_pt` (`pt_mercancia_id`),
  KEY `idx_op_estado` (`estado`,`fecha`),
  CONSTRAINT `fk_op_pt` FOREIGN KEY (`pt_mercancia_id`) REFERENCES `mercancia` (`id`) ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `orden_produccion`
--

LOCK TABLES `orden_produccion` WRITE;
/*!40000 ALTER TABLE `orden_produccion` DISABLE KEYS */;
/*!40000 ALTER TABLE `orden_produccion` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `produccion`
--

DROP TABLE IF EXISTS `produccion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `produccion` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `fecha` date NOT NULL,
  `producto_terminado_id` int(11) NOT NULL,
  `cantidad_producida` decimal(10,2) NOT NULL,
  `estado` enum('en_proceso','terminado') DEFAULT 'en_proceso',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `produccion`
--

LOCK TABLES `produccion` WRITE;
/*!40000 ALTER TABLE `produccion` DISABLE KEYS */;
/*!40000 ALTER TABLE `produccion` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `produccion_detalle_mp`
--

DROP TABLE IF EXISTS `produccion_detalle_mp`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `produccion_detalle_mp` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `produccion_id` int(11) NOT NULL,
  `mercancia_id` int(11) NOT NULL,
  `cantidad_usada` decimal(10,2) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `produccion_detalle_mp`
--

LOCK TABLES `produccion_detalle_mp` WRITE;
/*!40000 ALTER TABLE `produccion_detalle_mp` DISABLE KEYS */;
/*!40000 ALTER TABLE `produccion_detalle_mp` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `productos_terminados`
--

DROP TABLE IF EXISTS `productos_terminados`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `productos_terminados` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(255) NOT NULL,
  `descripcion` text DEFAULT NULL,
  `unidad_id` int(11) DEFAULT NULL,
  `cont_neto` decimal(10,2) DEFAULT NULL,
  `cuenta_id` int(11) DEFAULT NULL,
  `subcuenta_id` int(11) DEFAULT NULL,
  `unidad_medida` varchar(50) DEFAULT NULL,
  `precio_venta` decimal(10,2) DEFAULT 0.00,
  PRIMARY KEY (`id`),
  KEY `fk_pt_unidad` (`unidad_id`),
  KEY `fk_pt_cuenta` (`cuenta_id`),
  KEY `fk_pt_subcuenta` (`subcuenta_id`),
  CONSTRAINT `fk_pt_cuenta` FOREIGN KEY (`cuenta_id`) REFERENCES `cuentas_contables` (`id`),
  CONSTRAINT `fk_pt_subcuenta` FOREIGN KEY (`subcuenta_id`) REFERENCES `cuentas_contables` (`id`),
  CONSTRAINT `fk_pt_unidad` FOREIGN KEY (`unidad_id`) REFERENCES `unidades_medida` (`id`),
  CONSTRAINT `productos_terminados_ibfk_1` FOREIGN KEY (`unidad_id`) REFERENCES `unidades_medida` (`id`),
  CONSTRAINT `productos_terminados_ibfk_2` FOREIGN KEY (`cuenta_id`) REFERENCES `cuentas_contables` (`id`),
  CONSTRAINT `productos_terminados_ibfk_3` FOREIGN KEY (`subcuenta_id`) REFERENCES `cuentas_contables` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `productos_terminados`
--

LOCK TABLES `productos_terminados` WRITE;
/*!40000 ALTER TABLE `productos_terminados` DISABLE KEYS */;
INSERT INTO `productos_terminados` VALUES (1,'Producto Trigger Test','Verificar inventario',1,25.00,NULL,NULL,NULL,0.00),(2,'Producto Trigger Test','Creado para prueba de inventario',1,25.00,NULL,NULL,NULL,0.00),(3,'Producto Terminado Test','Para prueba',1,50.00,NULL,NULL,NULL,0.00);
/*!40000 ALTER TABLE `productos_terminados` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER trg_pt_to_inventario
AFTER INSERT ON productos_terminados
FOR EACH ROW
BEGIN
     INSERT IGNORE INTO inventario (producto_id, producto, inventario_inicial, entradas, salidas, aprobado)
     VALUES (NEW.id, NEW.nombre, 0, 0, 0, 0);
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `proveedores`
--

DROP TABLE IF EXISTS `proveedores`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `proveedores` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(255) NOT NULL,
  `direccion` varchar(255) DEFAULT NULL,
  `ciudad` varchar(100) DEFAULT NULL,
  `telefono` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `proveedores`
--

LOCK TABLES `proveedores` WRITE;
/*!40000 ALTER TABLE `proveedores` DISABLE KEYS */;
INSERT INTO `proveedores` VALUES (1,'El Loco Jr','Ave Mariscal','Ciudad Juarez Chih','6566121866'),(2,'Vani','Gral Jose Trinidad','Ciudad Juarez Chih','656 626 9313'),(3,'SAMS Juarez','Ave Ejercito Nacional','Ciudad Juarez Chih','800'),(4,'Trevly','Calle Apolo 1050','Ciudad Juarez Chih','656 311 2760');
/*!40000 ALTER TABLE `proveedores` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `subcuentas_contables`
--

DROP TABLE IF EXISTS `subcuentas_contables`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `subcuentas_contables` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `cuenta_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `cuenta_id` (`cuenta_id`),
  CONSTRAINT `subcuentas_contables_ibfk_1` FOREIGN KEY (`cuenta_id`) REFERENCES `cuentas_contables` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `subcuentas_contables`
--

LOCK TABLES `subcuentas_contables` WRITE;
/*!40000 ALTER TABLE `subcuentas_contables` DISABLE KEYS */;
/*!40000 ALTER TABLE `subcuentas_contables` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tipo_inventario`
--

DROP TABLE IF EXISTS `tipo_inventario`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tipo_inventario` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` enum('MP','WIP','PT') NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tipo_inventario`
--

LOCK TABLES `tipo_inventario` WRITE;
/*!40000 ALTER TABLE `tipo_inventario` DISABLE KEYS */;
INSERT INTO `tipo_inventario` VALUES (1,'MP'),(2,'WIP'),(3,'PT');
/*!40000 ALTER TABLE `tipo_inventario` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tipos_inventario`
--

DROP TABLE IF EXISTS `tipos_inventario`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tipos_inventario` (
  `id` tinyint(4) NOT NULL,
  `clave` enum('MP','WIP','PT') NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `clave` (`clave`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tipos_inventario`
--

LOCK TABLES `tipos_inventario` WRITE;
/*!40000 ALTER TABLE `tipos_inventario` DISABLE KEYS */;
INSERT INTO `tipos_inventario` VALUES (1,'MP'),(2,'WIP'),(3,'PT');
/*!40000 ALTER TABLE `tipos_inventario` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `unidades_medida`
--

DROP TABLE IF EXISTS `unidades_medida`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `unidades_medida` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `unidades_medida`
--

LOCK TABLES `unidades_medida` WRITE;
/*!40000 ALTER TABLE `unidades_medida` DISABLE KEYS */;
INSERT INTO `unidades_medida` VALUES (1,'uds'),(2,'mililitro'),(3,'gramos'),(4,'KG');
/*!40000 ALTER TABLE `unidades_medida` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `usuarios`
--

DROP TABLE IF EXISTS `usuarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `usuarios` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `correo` varchar(100) NOT NULL,
  `contrasena` varchar(100) NOT NULL,
  `rol` enum('admin','editor') NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `correo` (`correo`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usuarios`
--

LOCK TABLES `usuarios` WRITE;
/*!40000 ALTER TABLE `usuarios` DISABLE KEYS */;
INSERT INTO `usuarios` VALUES (6,'Admin Principal','admin@miapp.com','$2b$12$VeOkED27Wc7gX2M2IMcNuuia7PfwIe9PsIOu2R0DWGoZNnMORyOrm','admin'),(8,'Editor Uno','editor@miapp.com','$2b$12$pqrosBEHOdv8gB0VavMRi.VfciJJVI.qyKNvOSvSykG/Lh/R36s5W','editor'),(9,'Pako','fcogranados@yahoo.com','$2b$12$hiLNYk5JNDIMiMpz5ykqoujvBf/Hs7vM7aHjcgfaxNx/zaDcT2xti','admin'),(12,'Admin','admin@local','$2b$12$abcdefghijklmnopqrstuvCnxm0mVwQ1JxWw1m0Q3v0','admin');
/*!40000 ALTER TABLE `usuarios` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Temporary table structure for view `v_existencias`
--

DROP TABLE IF EXISTS `v_existencias`;
/*!50001 DROP VIEW IF EXISTS `v_existencias`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE VIEW `v_existencias` AS SELECT
 1 AS `mercancia_id`,
  1 AS `tipo_inventario_id`,
  1 AS `unidades_disponibles` */;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `v_inventario_consolidado`
--

DROP TABLE IF EXISTS `v_inventario_consolidado`;
/*!50001 DROP VIEW IF EXISTS `v_inventario_consolidado`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE VIEW `v_inventario_consolidado` AS SELECT
 1 AS `id`,
  1 AS `producto`,
  1 AS `inventario_inicial`,
  1 AS `entradas`,
  1 AS `salidas`,
  1 AS `disponible`,
  1 AS `valor_inventario` */;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `v_movimientos_inventario`
--

DROP TABLE IF EXISTS `v_movimientos_inventario`;
/*!50001 DROP VIEW IF EXISTS `v_movimientos_inventario`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE VIEW `v_movimientos_inventario` AS SELECT
 1 AS `movimiento_id`,
  1 AS `producto`,
  1 AS `tipo`,
  1 AS `cantidad`,
  1 AS `costo_unitario`,
  1 AS `total`,
  1 AS `referencia`,
  1 AS `fecha`,
  1 AS `mercancia_id`,
  1 AS `producto_id` */;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `v_stock`
--

DROP TABLE IF EXISTS `v_stock`;
/*!50001 DROP VIEW IF EXISTS `v_stock`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE VIEW `v_stock` AS SELECT
 1 AS `mercancia_id`,
  1 AS `producto`,
  1 AS `fase`,
  1 AS `unidades` */;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `vw_cuentas_contables`
--

DROP TABLE IF EXISTS `vw_cuentas_contables`;
/*!50001 DROP VIEW IF EXISTS `vw_cuentas_contables`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE VIEW `vw_cuentas_contables` AS SELECT
 1 AS `id`,
  1 AS `codigo`,
  1 AS `nombre`,
  1 AS `tipo`,
  1 AS `naturaleza`,
  1 AS `nivel`,
  1 AS `permite_subcuentas`,
  1 AS `padre_id`,
  1 AS `padre_codigo`,
  1 AS `padre_nombre`,
  1 AS `hijos` */;
SET character_set_client = @saved_cs_client;

--
-- Final view structure for view `v_existencias`
--

/*!50001 DROP VIEW IF EXISTS `v_existencias`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `v_existencias` AS select `inventario_movimientos`.`mercancia_id` AS `mercancia_id`,`inventario_movimientos`.`tipo_inventario_id` AS `tipo_inventario_id`,coalesce(sum(case when `inventario_movimientos`.`tipo_movimiento` = 'entrada' then `inventario_movimientos`.`unidades` when `inventario_movimientos`.`tipo_movimiento` = 'salida' then -`inventario_movimientos`.`unidades` else 0 end),0) AS `unidades_disponibles` from `inventario_movimientos` group by `inventario_movimientos`.`mercancia_id`,`inventario_movimientos`.`tipo_inventario_id` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_inventario_consolidado`
--

/*!50001 DROP VIEW IF EXISTS `v_inventario_consolidado`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `v_inventario_consolidado` AS select `i`.`id` AS `id`,coalesce(`m`.`nombre`,`p`.`nombre`,`i`.`producto`) AS `producto`,`i`.`inventario_inicial` AS `inventario_inicial`,`i`.`entradas` AS `entradas`,`i`.`salidas` AS `salidas`,`i`.`inventario_inicial` + `i`.`entradas` - `i`.`salidas` AS `disponible`,(`i`.`inventario_inicial` + `i`.`entradas` - `i`.`salidas`) * coalesce(`dc`.`precio_unitario`,0) AS `valor_inventario` from (((`inventario` `i` left join `mercancia` `m` on(`m`.`id` = `i`.`mercancia_id`)) left join `productos_terminados` `p` on(`p`.`id` = `i`.`producto_id`)) left join `detalle_compra` `dc` on(`dc`.`mercancia_id` = `i`.`mercancia_id`)) order by coalesce(`m`.`nombre`,`p`.`nombre`,`i`.`producto`) */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_movimientos_inventario`
--

/*!50001 DROP VIEW IF EXISTS `v_movimientos_inventario`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `v_movimientos_inventario` AS select `mi`.`id` AS `movimiento_id`,coalesce(`m`.`nombre`,`p`.`nombre`) AS `producto`,`mi`.`tipo` AS `tipo`,`mi`.`cantidad` AS `cantidad`,`mi`.`costo_unitario` AS `costo_unitario`,`mi`.`cantidad` * `mi`.`costo_unitario` AS `total`,`mi`.`referencia` AS `referencia`,`mi`.`fecha` AS `fecha`,`mi`.`mercancia_id` AS `mercancia_id`,`mi`.`producto_id` AS `producto_id` from ((`movimientos_inventario` `mi` left join `mercancia` `m` on(`m`.`id` = `mi`.`mercancia_id`)) left join `productos_terminados` `p` on(`p`.`id` = `mi`.`producto_id`)) order by `mi`.`fecha` desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_stock`
--

/*!50001 DROP VIEW IF EXISTS `v_stock`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `v_stock` AS select `e`.`mercancia_id` AS `mercancia_id`,`m`.`nombre` AS `producto`,`t`.`clave` AS `fase`,`e`.`unidades_disponibles` AS `unidades` from ((`v_existencias` `e` join `mercancia` `m` on(`m`.`id` = `e`.`mercancia_id`)) join `tipos_inventario` `t` on(`t`.`id` = `e`.`tipo_inventario_id`)) order by `m`.`nombre`,`t`.`id` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `vw_cuentas_contables`
--

/*!50001 DROP VIEW IF EXISTS `vw_cuentas_contables`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `vw_cuentas_contables` AS select `c`.`id` AS `id`,`c`.`codigo` AS `codigo`,`c`.`nombre` AS `nombre`,`c`.`tipo` AS `tipo`,`c`.`naturaleza` AS `naturaleza`,`c`.`nivel` AS `nivel`,`c`.`permite_subcuentas` AS `permite_subcuentas`,`c`.`padre_id` AS `padre_id`,`p`.`codigo` AS `padre_codigo`,`p`.`nombre` AS `padre_nombre`,(select count(0) from `cuentas_contables` `h` where `h`.`padre_id` = `c`.`id`) AS `hijos` from (`cuentas_contables` `c` left join `cuentas_contables` `p` on(`p`.`id` = `c`.`padre_id`)) */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-09-05  9:26:40
