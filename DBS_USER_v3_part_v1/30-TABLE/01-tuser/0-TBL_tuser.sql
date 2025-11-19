-- (MariaDB 11.4.8) ten1389edu@gmail.com
-- ==============================================================================================
-- 
--  Check
-- 
-- ==============================================================================================

select @@sql_mode; 
-- NO_ZERO_DATE for DT7
-- STRICT_TRANS_TABLES 또는 STRICT_ALL_TABLES for 데이터 길이 상한방어



-- ==============================================================================================
-- 
--  tuser
-- 
-- ==============================================================================================

DROP TABLE IF EXISTS tuser;


CREATE TABLE tuser (  

  userid VARCHAR(32) NOT NULL,

  name VARCHAR(64) NOT NULL,

  dt7 DATETIME(6) NOT NULL DEFAULT '0000-00-00 00:00:00',

  dt8 DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

  PRIMARY KEY (userid)

);



SHOW CREATE TABLE tuser\G
DESC tuser; 



SHOW INDEX FROM tuser;



SELECT TABLE_NAME, TABLE_COLLATION
  FROM INFORMATION_SCHEMA.TABLES
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'tuser';

SELECT TABLE_NAME, COLUMN_NAME, CHARACTER_SET_NAME, COLLATION_NAME
  FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'tuser';


