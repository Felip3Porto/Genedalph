-- MySQL dump 10.17  Distrib 10.3.13-MariaDB, for Linux (x86_64)
--
-- Host: localhost    Database: Genedalfv2
-- ------------------------------------------------------
-- Server version	10.3.13-MariaDB
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO,MYSQL40' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `DEG_lncRNA_roster`
--

DROP TABLE IF EXISTS `DEG_lncRNA_roster`;
CREATE TABLE `DEG_lncRNA_roster` (
  `roster_id` int(11) NOT NULL,
  `cell_line` varchar(45) DEFAULT NULL,
  `lncRNA_name` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`roster_id`)
) ENGINE=InnoDB;


DROP TABLE IF EXISTS `Expression`;
CREATE TABLE `Expression` (
  `expression_id` int(11) NOT NULL,
  `ENSG_id` varchar(200) DEFAULT NULL,
  `gene_symbol` varchar(69) DEFAULT NULL,
  `baseMean` decimal(45,25) DEFAULT NULL,
  `log2FoldChange` decimal(45,25) DEFAULT NULL,
  `lfcSE` decimal(45,25) DEFAULT NULL,
  `pvalue` decimal(45,38) DEFAULT NULL,
  `stat` decimal(45,25) DEFAULT NULL,
  `padj` decimal(45,38) DEFAULT NULL,
  `DEG_lncRNA_roster_roster_id` int(11) NOT NULL,
  PRIMARY KEY (`expression_id`),
  KEY `fk_Expression_DEG_lncRNA_roster_idx` (`DEG_lncRNA_roster_roster_id`),
  CONSTRAINT `fk_Expression_DEG_lncRNA_roster` FOREIGN KEY (`DEG_lncRNA_roster_roster_id`) REFERENCES `DEG_lncRNA_roster` (`roster_id`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

