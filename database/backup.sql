-- MySQL dump 10.13  Distrib 8.0.46, for Linux (x86_64)
--
-- Host: localhost    Database: product_db
-- ------------------------------------------------------
-- Server version	8.0.46

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Current Database: `product_db`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `product_db` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;

USE `product_db`;

--
-- Table structure for table `outbox_messages`
--

DROP TABLE IF EXISTS `outbox_messages`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `outbox_messages` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `message_key` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `payload` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `topic` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `outbox_messages`
--

LOCK TABLES `outbox_messages` WRITE;
/*!40000 ALTER TABLE `outbox_messages` DISABLE KEYS */;
/*!40000 ALTER TABLE `outbox_messages` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `processed_orders`
--

DROP TABLE IF EXISTS `processed_orders`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `processed_orders` (
  `order_id` bigint NOT NULL,
  `accepted` bit(1) NOT NULL,
  `reason` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`order_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `processed_orders`
--

LOCK TABLES `processed_orders` WRITE;
/*!40000 ALTER TABLE `processed_orders` DISABLE KEYS */;
INSERT INTO `processed_orders` VALUES (1,_binary '','Stock deducted'),(2,_binary '','Stock deducted'),(3,_binary '','Stock deducted'),(4,_binary '','Stock deducted'),(5,_binary '','Stock deducted'),(6,_binary '','Stock deducted'),(7,_binary '\0','Product missing or insufficient stock at fulfillment'),(8,_binary '\0','Product missing or insufficient stock at fulfillment'),(9,_binary '\0','Product missing or insufficient stock at fulfillment'),(10,_binary '\0','Product missing or insufficient stock at fulfillment'),(11,_binary '\0','Product missing or insufficient stock at fulfillment'),(12,_binary '\0','Product missing or insufficient stock at fulfillment'),(13,_binary '\0','Product missing or insufficient stock at fulfillment'),(14,_binary '\0','Product missing or insufficient stock at fulfillment'),(15,_binary '','Stock deducted'),(16,_binary '','Stock deducted');
/*!40000 ALTER TABLE `processed_orders` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `products`
--

DROP TABLE IF EXISTS `products`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `products` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `price` decimal(12,2) NOT NULL,
  `stock` int NOT NULL,
  `version` bigint DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `products`
--

LOCK TABLES `products` WRITE;
/*!40000 ALTER TABLE `products` DISABLE KEYS */;
INSERT INTO `products` VALUES (1,'Laptop Java Developer',15000000.00,20,0),(2,'Ban phim co',850000.00,50,0),(3,'Chuot khong day',250000.00,100,0),(4,'E2E decimal product',19.95,7,1),(6,'E2E decimal product',19.95,6,2),(7,'E2E concurrent stock',10.00,0,3);
/*!40000 ALTER TABLE `products` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Current Database: `order_db`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `order_db` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;

USE `order_db`;

--
-- Table structure for table `orders`
--

DROP TABLE IF EXISTS `orders`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `orders` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `product_id` bigint NOT NULL,
  `product_name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `quantity` int NOT NULL,
  `reason` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `status` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `total_price` decimal(22,2) NOT NULL,
  `unit_price` decimal(12,2) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `orders`
--

LOCK TABLES `orders` WRITE;
/*!40000 ALTER TABLE `orders` DISABLE KEYS */;
INSERT INTO `orders` VALUES (1,'2026-11-15 00:40:45.645111',4,'E2E decimal product',3,'Stock deducted','CONFIRMED',59.85,19.95),(2,'2026-11-15 00:42:09.788302',5,'Postman test product updated',3,'Stock deducted','CONFIRMED',59.85,19.95),(3,'2026-11-15 00:42:13.327588',6,'E2E decimal product',3,'Stock deducted','CONFIRMED',59.85,19.95),(4,'2026-11-15 00:42:42.996116',7,'E2E concurrent stock',1,'Stock deducted','CONFIRMED',10.00,10.00),(5,'2026-11-15 00:42:43.049878',7,'E2E concurrent stock',1,'Stock deducted','CONFIRMED',10.00,10.00),(6,'2026-11-15 00:42:43.056279',7,'E2E concurrent stock',1,'Stock deducted','CONFIRMED',10.00,10.00),(7,'2026-11-15 00:42:43.072399',7,'E2E concurrent stock',1,'Product missing or insufficient stock at fulfillment','REJECTED',10.00,10.00),(8,'2026-11-15 00:42:43.095080',7,'E2E concurrent stock',1,'Product missing or insufficient stock at fulfillment','REJECTED',10.00,10.00),(9,'2026-11-15 00:42:43.099950',7,'E2E concurrent stock',1,'Product missing or insufficient stock at fulfillment','REJECTED',10.00,10.00),(10,'2026-11-15 00:42:43.136190',7,'E2E concurrent stock',1,'Product missing or insufficient stock at fulfillment','REJECTED',10.00,10.00),(11,'2026-11-15 00:42:43.143129',7,'E2E concurrent stock',1,'Product missing or insufficient stock at fulfillment','REJECTED',10.00,10.00),(12,'2026-11-15 00:42:43.144025',7,'E2E concurrent stock',1,'Product missing or insufficient stock at fulfillment','REJECTED',10.00,10.00),(13,'2026-11-15 00:42:43.179893',7,'E2E concurrent stock',1,'Product missing or insufficient stock at fulfillment','REJECTED',10.00,10.00),(14,'2026-11-15 00:42:43.151792',7,'E2E concurrent stock',1,'Product missing or insufficient stock at fulfillment','REJECTED',10.00,10.00),(15,'2026-11-15 00:43:12.687722',6,'E2E decimal product',1,'Stock deducted','CONFIRMED',19.95,19.95),(16,'2026-11-15 00:45:57.382671',8,'Postman test product updated',3,'Stock deducted','CONFIRMED',59.85,19.95);
/*!40000 ALTER TABLE `orders` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `outbox_messages`
--

DROP TABLE IF EXISTS `outbox_messages`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `outbox_messages` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `message_key` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `payload` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `topic` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `outbox_messages`
--

LOCK TABLES `outbox_messages` WRITE;
/*!40000 ALTER TABLE `outbox_messages` DISABLE KEYS */;
/*!40000 ALTER TABLE `outbox_messages` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-11-15  0:46:27
