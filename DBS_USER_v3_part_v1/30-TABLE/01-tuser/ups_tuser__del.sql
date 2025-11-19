-- (MariaDB 11.4.8) ten1389edu@gmail.com
-- ==============================================================================================
-- 
--  ups_tuser__del
-- 
-- ==============================================================================================

DROP PROCEDURE IF EXISTS ups_tuser__del;

DELIMITER $$
CREATE PROCEDURE ups_tuser__del (
  IN  p_json JSON,  
  OUT r_json JSON
)
BEGIN
  DECLARE v_p_userid VARCHAR(32);
  DECLARE v_p_userid_MINLEN TINYINT DEFAULT 4;

  DECLARE v_ret_val1 INT DEFAULT 0;
  DECLARE v_ret_val2 INT DEFAULT 0;  
  DECLARE v_ret_mssg TEXT DEFAULT '';

  DECLARE v_hdl_stat CHAR(5);
  DECLARE v_hdl_text TEXT;

  main: BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
      GET DIAGNOSTICS CONDITION 1 
        v_ret_val2 = MYSQL_ERRNO,
        v_hdl_stat = RETURNED_SQLSTATE,
        v_hdl_text = MESSAGE_TEXT;

      SET v_ret_val1 = -501;
      SET v_ret_mssg = CONCAT('SQL-ERROR: ', v_ret_val2, ' (', IFNULL(v_hdl_stat, 'NULL'), ')-> ', IFNULL(v_hdl_text, 'NULL'));
    END;
    
    SET r_json = JSON_OBJECT();

    IF IFNULL(JSON_VALID(p_json), 0) = 0 OR JSON_TYPE(p_json) <> 'OBJECT' THEN
      SET v_ret_val1 = -200;
      SET v_ret_mssg = 'ERROR: JSON is not valid';
      LEAVE main;
    END IF;

    IF IFNULL(JSON_CONTAINS_PATH(p_json, 'one', '$.userid'), 0) = 0 THEN
      SET v_ret_val1 = -201;
      SET v_ret_val2 = 1;
      SET v_ret_mssg = 'ERROR: required keys missing (need userid)';
      LEAVE main;
    ELSE
      SET v_p_userid = IFNULL(TRIM(JSON_VALUE(p_json, '$.userid')), '');  
      IF CHAR_LENGTH(v_p_userid) < v_p_userid_MINLEN THEN
        SET v_ret_val1 = -201;
        SET v_ret_val2 = 2;
        SET v_ret_mssg = CONCAT('ERROR: userid must be at least ', v_p_userid_MINLEN, ' characters long');
        LEAVE main;
      END IF;
    END IF;


    DELETE
    FROM tuser
      WHERE userid = v_p_userid
    ;

    SET v_ret_val1 = ROW_COUNT();
    
    IF v_ret_val1 = 0 THEN
      SET v_ret_mssg = 'FAIL: unknown userid';
    ELSE
      SET v_ret_mssg = CONCAT('SUCC: deleted [', v_p_userid, ']');
    END IF; 
  END main;

  SET r_json = JSON_OBJECT('value1', v_ret_val1, 'value2', v_ret_val2, 'buflen', 0, 'buffer', v_ret_mssg);

END $$
DELIMITER ;
