-- (MariaDB 11.4.8) ten1389edu@gmail.com
-- ==============================================================================================
-- 
--  ups_tuser__sel_pk
-- 
-- ==============================================================================================

DROP PROCEDURE IF EXISTS ups_tuser__sel_pk;

DELIMITER $$
CREATE PROCEDURE ups_tuser__sel_pk (
  IN  p_json JSON,
  OUT q_json JSON,
  OUT r_json JSON
)
BEGIN
  DECLARE v_p_userid_comp VARCHAR(2);
  DECLARE v_p_userid  VARCHAR(32);
  DECLARE v_p_limit   VARCHAR(10);
  DECLARE v_p_limit_MIN INT DEFAULT -9999;
  DECLARE v_p_limit_MAX INT DEFAULT +9999;
  
  DECLARE v_ret_val1 INT DEFAULT 0;
  DECLARE v_ret_val2 INT DEFAULT 0;  
  DECLARE v_ret_mssg TEXT DEFAULT '';

  DECLARE v_sql        TEXT;
  DECLARE v_sql_limit  INT;
  DECLARE v_sql_direct VARCHAR(4);   -- ASC / DESC
  DECLARE v_sql_userid_comp VARCHAR(2);   -- <, <=, =, >, >=

  DECLARE v_hdl_stat CHAR(5);
  DECLARE v_hdl_text TEXT;

  DECLARE v_stmt_prepared INT DEFAULT 0;

  main: BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
      GET DIAGNOSTICS CONDITION 1 
        v_ret_val2   = MYSQL_ERRNO,
        v_hdl_stat  = RETURNED_SQLSTATE,
        v_hdl_text   = MESSAGE_TEXT;

      IF v_stmt_prepared = 1 THEN
        DEALLOCATE PREPARE stmt;
        SET v_stmt_prepared = 0;
      END IF;

      SET v_ret_val1 = -501;
      SET v_ret_mssg = CONCAT('SQL-ERROR: ', v_ret_val2, ' (', IFNULL(v_hdl_stat, 'NULL'), ')-> ', IFNULL(v_hdl_text, 'NULL'));
    END;

    SET q_json = JSON_ARRAY();
    SET r_json = JSON_OBJECT();

    IF IFNULL(JSON_VALID(p_json), 0) = 0 OR JSON_TYPE(p_json) <> 'OBJECT' THEN
      SET v_ret_val1 = -200;
      SET v_ret_mssg = 'ERROR: JSON is not valid';
      LEAVE main;
    END IF;

    IF IFNULL(JSON_CONTAINS_PATH(p_json, 'one', '$.limit'), 0) = 0 THEN
      SET v_ret_val1 = -201;
      SET v_ret_val2 = 1;
      SET v_ret_mssg = 'ERROR: required keys missing (need limit)';
      LEAVE main;
    ELSE
      SET v_p_limit = IFNULL(TRIM(JSON_VALUE(p_json, '$.limit')), '');
      IF v_p_limit NOT REGEXP '^[+-]?[1-9][0-9]*$' THEN
        SET v_ret_val1 = -201;
        SET v_ret_val2 = 2;
        SET v_ret_mssg = 'ERROR: limit must be signed non-zero integer';
        LEAVE main;
      ELSE
        SET v_sql_limit = LEAST(v_p_limit_MAX, GREATEST(v_p_limit_MIN, CAST(v_p_limit AS SIGNED)));
        SET v_sql_direct = IF(v_sql_limit < 0, 'DESC', 'ASC');
        SET v_sql_limit = ABS(v_sql_limit);
      END IF;
    END IF;

    IF IFNULL(JSON_CONTAINS_PATH(p_json, 'all', '$.userid_comp', '$.userid'), 0) = 0 THEN
      SET v_ret_val1 = -202;
      SET v_ret_val2 = 1;
      SET v_ret_mssg = 'ERROR: required keys missing (need userid_comp, userid)';
      LEAVE main;
    ELSE
      SET v_p_userid_comp = IFNULL(UPPER(TRIM(JSON_VALUE(p_json, '$.userid_comp'))), 'XX');
      IF v_p_userid_comp NOT IN ('GT','GE','EQ','LT','LE') THEN
          SET v_ret_val1 = -202;
          SET v_ret_val2 = 2;
        SET v_ret_mssg = 'ERROR: userid_comp must be one of GT, GE, EQ, LT, LE';
        LEAVE main;
      ELSE
        SET v_sql_userid_comp = CASE v_p_userid_comp
          WHEN 'GT' THEN '>'
          WHEN 'GE' THEN '>='
          WHEN 'EQ' THEN '='
          WHEN 'LT' THEN '<'
          WHEN 'LE' THEN '<='
        END;
      END IF;

      SET v_p_userid = IFNULL(TRIM(JSON_VALUE(p_json, '$.userid')), '');
    END IF;

    SET @sel_data  = JSON_ARRAY();
    SET @sel_count = 0;

    SET v_sql = CONCAT(
      ' SELECT IFNULL(',
        ' JSON_ARRAYAGG(',
          ' JSON_OBJECT(''userid'', s.userid, ''name'', s.name)',
          ' ORDER BY s.userid ', v_sql_direct,
        ' ), JSON_ARRAY()',
      ' )',
      ' INTO @sel_data ',
      ' FROM (',
        ' SELECT userid, name ',
        ' FROM tuser ',
          ' WHERE userid ', v_sql_userid_comp, ' ? ',
          ' ORDER BY userid ', v_sql_direct,
          ' LIMIT ', v_sql_limit,
      ' ) AS s'
    );

    PREPARE stmt FROM v_sql;
    SET v_stmt_prepared = 1;
    EXECUTE stmt USING v_p_userid;
    DEALLOCATE PREPARE stmt;
    SET v_stmt_prepared = 0;
    
    SET v_sql = CONCAT(
      ' SELECT COUNT(*)',
      ' INTO @sel_count',
      ' FROM tuser',
        ' WHERE userid ', v_sql_userid_comp, ' ?'
    );
    PREPARE stmt FROM v_sql;
    SET v_stmt_prepared = 1;
    EXECUTE stmt USING v_p_userid;
    DEALLOCATE PREPARE stmt;
    SET v_stmt_prepared = 0;
  
    SET q_json = IFNULL(@sel_data, JSON_ARRAY());
    SET v_ret_val2 = IFNULL(@sel_count, 0);
    SET v_ret_val1 = IFNULL(JSON_LENGTH(q_json), 0);

    IF v_ret_val1 = 0 THEN
      SET v_ret_mssg = 'FAIL: empty result';
    ELSE
      SET v_ret_mssg = 'SUCC: found';
    END IF; 
  END main;

  SET r_json = JSON_OBJECT('value1', v_ret_val1, 'value2', v_ret_val2, 'buflen', 0, 'buffer', v_ret_mssg);

END $$
DELIMITER ;
