-- (MariaDB 11.4.8) ten1389edu@gmail.com
-- ==============================================================================================
-- 
-- CHECK 
-- 
-- ==============================================================================================


-- check COLLATE
SELECT 'AAAAAAAAAA' = 'aaaaaAAAAA';

-- check LENGTH
SELECT LENGTH('가');
SELECT LENGTH('가A');
SELECT LENGTH('가A1');
SELECT CHAR_LENGTH('가');
SELECT CHAR_LENGTH('가A');
SELECT CHAR_LENGTH('가1');


SELECT * FROM tlogin_passwd;

-- ==============================================================================================
-- 
-- prepare data 
-- 
-- ==============================================================================================



SET @p_json = '', @r_json = '';
SET @p_json = JSON_OBJECT('userid','PREP_USER5','name','BBBBBBBBBB');
-- SUCC: insert
CALL ups_tuser__ins(@p_json, @r_json);
SELECT JSON_PRETTY(@p_json) AS p_json; SELECT JSON_PRETTY(@r_json) AS r_json;


SET @p_json = '', @r_json = '';
SET @p_json = JSON_OBJECT('userid','PREP_USER3','name','cccccccccc');
-- SUCC: insert
CALL ups_tuser__ins(@p_json, @r_json);
SELECT JSON_PRETTY(@p_json) AS p_json; SELECT JSON_PRETTY(@r_json) AS r_json;



SET @p_json = '', @r_json = '';
SET @p_json = JSON_OBJECT('userid','PREP_USER2','name','BBBBBBBBBB');
-- SUCC: insert
CALL ups_tuser__ins(@p_json, @r_json);
SELECT JSON_PRETTY(@p_json) AS p_json; SELECT JSON_PRETTY(@r_json) AS r_json;



SET @p_json = '', @r_json = '';
SET @p_json = JSON_OBJECT('userid','PREP_USER1','name','AAAAAAAAAA');
-- SUCC: insert
CALL ups_tuser__ins(@p_json, @r_json);
SELECT JSON_PRETTY(@p_json) AS p_json; SELECT JSON_PRETTY(@r_json) AS r_json;



SET @p_json = '', @r_json = '';
SET @p_json = JSON_OBJECT('userid','PREP_USER4','name','AAAAAAAAAA');
-- SUCC: insert
CALL ups_tuser__ins(@p_json, @r_json);
SELECT JSON_PRETTY(@p_json) AS p_json; SELECT JSON_PRETTY(@r_json) AS r_json;



SELECT * from tuser;


-- ==============================================================================================
-- 
-- prepare 
-- 
-- ==============================================================================================


SET @glb_userid = 'user1000';




-- ==============================================================================================
-- 
-- ins 
-- 
-- ==============================================================================================


SET @name__ins = 'New____';



SET @p_json = '', @r_json = '';
SET @p_json = JSON_OBJECT('userid', @glb_userid, 'name', @name__ins);
-- SUCC: insert
CALL ups_tuser__ins(@p_json, @r_json);
SELECT JSON_PRETTY(@p_json) AS p_json; SELECT JSON_PRETTY(@r_json) AS r_json;
SELECT * FROM tuser;


SET @p_json = '', @r_json = '';
SET @p_json = JSON_OBJECT('userid', @glb_userid, 'name', @name__ins);
-- =SQL-ERROR: dup
CALL ups_tuser__ins(@p_json, @r_json);
SELECT JSON_PRETTY(@p_json) AS p_json; SELECT JSON_PRETTY(@r_json) AS r_json;



SET @p_json = '', @r_json = '';
SET @p_json = '';
-- ERROR: JSON
CALL ups_tuser__ins(@p_json, @r_json);
SELECT JSON_PRETTY(@p_json) AS p_json; SELECT JSON_PRETTY(@r_json) AS r_json;



SET @p_json = '', @r_json = '';
SET @p_json = JSON_OBJECT('name', @name__ins);
-- ERROR: userid key
CALL ups_tuser__ins(@p_json, @r_json);
SELECT JSON_PRETTY(@p_json) AS p_json; SELECT JSON_PRETTY(@r_json) AS r_json;

SET @p_json = '', @r_json = '';
SET @p_json = JSON_OBJECT('userid', NULL, 'name', @name__ins);
-- ERROR: userid value
CALL ups_tuser__ins(@p_json, @r_json);
SELECT JSON_PRETTY(@p_json) AS p_json; SELECT JSON_PRETTY(@r_json) AS r_json;



SET @p_json = '', @r_json = '';
SET @p_json = JSON_OBJECT('userid', @glb_userid);
-- ERROR: name key
CALL ups_tuser__ins(@p_json, @r_json);
SELECT JSON_PRETTY(@p_json) AS p_json; SELECT JSON_PRETTY(@r_json) AS r_json;

SET @p_json = '', @r_json = '';
SET @p_json = JSON_OBJECT('userid', @glb_userid, 'name', NULL);
-- ERROR: name value
CALL ups_tuser__ins(@p_json, @r_json);
SELECT JSON_PRETTY(@p_json) AS p_json; SELECT JSON_PRETTY(@r_json) AS r_json;



-- ==============================================================================================
-- 
-- upd
-- 
-- ==============================================================================================

SET @name__upd = 'Upd____';



SET @p_json = '', @r_json = '';
SET @p_json = JSON_OBJECT('userid', 'unmatched', 'name', @name__upd);
-- FAIL: unmatched
CALL ups_tuser__upd(@p_json, @r_json);
SELECT JSON_PRETTY(@p_json) AS p_json; SELECT JSON_PRETTY(@r_json) AS r_json;



SET @p_json = '', @r_json = '';
SET @p_json = JSON_OBJECT('userid', @glb_userid, 'name', @name__upd);
-- SUCC: Update
CALL ups_tuser__upd(@p_json, @r_json);
SELECT JSON_PRETTY(@p_json) AS p_json; SELECT JSON_PRETTY(@r_json) AS r_json;
SELECT * FROM tuser;



SET @p_json = '', @r_json = '';
SET @p_json = JSON_OBJECT('userid', @glb_userid, 'name', @name__upd);
-- SUCC: Update Again
CALL ups_tuser__upd(@p_json, @r_json);
SELECT JSON_PRETTY(@p_json) AS p_json; SELECT JSON_PRETTY(@r_json) AS r_json;
SELECT * FROM tuser;



SET @p_json = '', @r_json = '';
SET @p_json = '';
-- ERROR: JSON
CALL ups_tuser__upd(@p_json, @r_json);
SELECT JSON_PRETTY(@p_json) AS p_json; SELECT JSON_PRETTY(@r_json) AS r_json;



SET @p_json = '', @r_json = '';
SET @p_json = JSON_OBJECT('name', @name__upd);
-- ERROR: userid key
CALL ups_tuser__upd(@p_json, @r_json);
SELECT JSON_PRETTY(@p_json) AS p_json; SELECT JSON_PRETTY(@r_json) AS r_json;

SET @p_json = '', @r_json = '';
SET @p_json = JSON_OBJECT('userid', NULL, 'name', @name__upd);
-- ERROR: userid value
CALL ups_tuser__upd(@p_json, @r_json);
SELECT JSON_PRETTY(@p_json) AS p_json; SELECT JSON_PRETTY(@r_json) AS r_json;



SET @p_json = '', @r_json = '';
SET @p_json = JSON_OBJECT('userid', @glb_userid);
-- ERROR: name key
CALL ups_tuser__upd(@p_json, @r_json);
SELECT JSON_PRETTY(@p_json) AS p_json; SELECT JSON_PRETTY(@r_json) AS r_json;

SET @p_json = '', @r_json = '';
SET @p_json = JSON_OBJECT('userid', @glb_userid, 'name', NULL);
-- ERROR: name value
CALL ups_tuser__upd(@p_json, @r_json);
SELECT JSON_PRETTY(@p_json) AS p_json; SELECT JSON_PRETTY(@r_json) AS r_json;



-- ==============================================================================================
-- 
-- sel
-- 
-- ==============================================================================================

SET @userid__sel_middle = 'PREP_USER3';

SELECT * FROM tuser;



SET @p_json = '', @q_json = '', @r_json = '';
SET @p_json = JSON_OBJECT('limit', 9999, 'userid_comp', 'EQ', 'userid', 'unmatched');
-- FAIL: unmatched
CALL ups_tuser__sel_pk(@p_json, @q_json, @r_json);
SELECT JSON_PRETTY(@p_json) AS p_json; SELECT JSON_PRETTY(@q_json) AS q_json; SELECT JSON_PRETTY(@r_json) AS r_json;



SET @p_json = '', @q_json = '', @r_json = '';
SET @p_json = JSON_OBJECT('limit', 9999, 'userid_comp', 'GE', 'userid', NULL);
-- SUCC: ALL ASC
CALL ups_tuser__sel_pk(@p_json, @q_json, @r_json);
SELECT JSON_PRETTY(@p_json) AS p_json; SELECT JSON_PRETTY(@q_json) AS q_json; SELECT JSON_PRETTY(@r_json) AS r_json;

SET @p_json = '', @q_json = '', @r_json = '';
SET @p_json = JSON_OBJECT('limit', 2, 'userid_comp', 'GE', 'userid', NULL);
-- SUCC: ALL ASC with limit
CALL ups_tuser__sel_pk(@p_json, @q_json, @r_json);
SELECT JSON_PRETTY(@p_json) AS p_json; SELECT JSON_PRETTY(@q_json) AS q_json; SELECT JSON_PRETTY(@r_json) AS r_json;



SET @p_json = '', @q_json = '', @r_json = '';
SET @p_json = JSON_OBJECT('limit', -9999, 'userid_comp', 'GE', 'userid', NULL);
-- SUCC: ALL DESC
CALL ups_tuser__sel_pk(@p_json, @q_json, @r_json);
SELECT JSON_PRETTY(@p_json) AS p_json; SELECT JSON_PRETTY(@q_json) AS q_json; SELECT JSON_PRETTY(@r_json) AS r_json;

SET @p_json = '', @q_json = '', @r_json = '';
SET @p_json = JSON_OBJECT('limit', -2, 'userid_comp', 'GE', 'userid', NULL);
-- SUCC: ALL DESC with limit
CALL ups_tuser__sel_pk(@p_json, @q_json, @r_json);
SELECT JSON_PRETTY(@p_json) AS p_json; SELECT JSON_PRETTY(@q_json) AS q_json; SELECT JSON_PRETTY(@r_json) AS r_json;



SET @p_json = '', @q_json = '', @r_json = '';
SET @p_json = JSON_OBJECT('limit', 9999, 'userid_comp', 'LT', 'userid', @userid__sel_middle);
-- SUCC: LT @userid__sel_middle ASC 
CALL ups_tuser__sel_pk(@p_json, @q_json, @r_json);
SELECT JSON_PRETTY(@p_json) AS p_json; SELECT JSON_PRETTY(@q_json) AS q_json; SELECT JSON_PRETTY(@r_json) AS r_json;



SET @p_json = '', @q_json = '', @r_json = '';
SET @p_json = JSON_OBJECT('limit', 9999, 'userid_comp', 'LE', 'userid', @userid__sel_middle);
-- SUCC: LE @userid__sel_middle ASC 
CALL ups_tuser__sel_pk(@p_json, @q_json, @r_json);
SELECT JSON_PRETTY(@p_json) AS p_json; SELECT JSON_PRETTY(@q_json) AS q_json; SELECT JSON_PRETTY(@r_json) AS r_json;



SET @p_json = '', @q_json = '', @r_json = '';
SET @p_json = JSON_OBJECT('limit', 9999, 'userid_comp', 'EQ', 'userid', @userid__sel_middle);
-- SUCC: EQ @userid__sel_middle ASC 
CALL ups_tuser__sel_pk(@p_json, @q_json, @r_json);
SELECT JSON_PRETTY(@p_json) AS p_json; SELECT JSON_PRETTY(@q_json) AS q_json; SELECT JSON_PRETTY(@r_json) AS r_json;



SET @p_json = '', @q_json = '', @r_json = '';
SET @p_json = JSON_OBJECT('limit', 9999, 'userid_comp', 'GE', 'userid', @userid__sel_middle);
-- SUCC: GE @userid__sel_middle ASC 
CALL ups_tuser__sel_pk(@p_json, @q_json, @r_json);
SELECT JSON_PRETTY(@p_json) AS p_json; SELECT JSON_PRETTY(@q_json) AS q_json; SELECT JSON_PRETTY(@r_json) AS r_json;



SET @p_json = '', @q_json = '', @r_json = '';
SET @p_json = JSON_OBJECT('limit', 9999, 'userid_comp', 'GT', 'userid', @userid__sel_middle);
-- SUCC: GT @userid__sel_middle ASC 
CALL ups_tuser__sel_pk(@p_json, @q_json, @r_json);
SELECT JSON_PRETTY(@p_json) AS p_json; SELECT JSON_PRETTY(@q_json) AS q_json; SELECT JSON_PRETTY(@r_json) AS r_json;



SET @p_json = '', @q_json = '', @r_json = '';
-- ERROR: JSON
CALL ups_tuser__sel_pk(@p_json, @q_json, @r_json);
SELECT JSON_PRETTY(@p_json) AS p_json; SELECT JSON_PRETTY(@q_json) AS q_json; SELECT JSON_PRETTY(@r_json) AS r_json;



SET @p_json = '', @q_json = '', @r_json = '';
SET @p_json = JSON_OBJECT('limit', 9999, 'userid', @glb_userid);
-- ERROR: userid_comp key
CALL ups_tuser__sel_pk(@p_json, @q_json, @r_json);
SELECT JSON_PRETTY(@p_json) AS p_json; SELECT JSON_PRETTY(@q_json) AS q_json; SELECT JSON_PRETTY(@r_json) AS r_json;

SET @p_json = '', @q_json = '', @r_json = '';
SET @p_json = JSON_OBJECT('limit', 9999, 'userid_comp', NULL, 'userid', @userid__sel_middle);
-- ERROR: userid_comp value
CALL ups_tuser__sel_pk(@p_json, @q_json, @r_json);
SELECT JSON_PRETTY(@p_json) AS p_json; SELECT JSON_PRETTY(@q_json) AS q_json; SELECT JSON_PRETTY(@r_json) AS r_json;

SET @p_json = '', @q_json = '', @r_json = '';
SET @p_json = JSON_OBJECT('limit', 9999, 'userid_comp', 'gg', 'userid', @userid__sel_middle);
-- ERROR: userid_comp value BAD
CALL ups_tuser__sel_pk(@p_json, @q_json, @r_json);
SELECT JSON_PRETTY(@p_json) AS p_json; SELECT JSON_PRETTY(@q_json) AS q_json; SELECT JSON_PRETTY(@r_json) AS r_json;



SET @p_json = '', @q_json = '', @r_json = '';
SET @p_json = JSON_OBJECT('limit', 9999, 'userid_comp', 'EQ');
-- ERROR: userid key
CALL ups_tuser__sel_pk(@p_json, @q_json, @r_json);
SELECT JSON_PRETTY(@p_json) AS p_json; SELECT JSON_PRETTY(@q_json) AS q_json; SELECT JSON_PRETTY(@r_json) AS r_json;

SET @p_json = '', @q_json = '', @r_json = '';
SET @p_json = JSON_OBJECT('limit', 9999, 'userid_comp', 'EQ', 'userid', '');
-- FAIL: unmatched or SUCC
CALL ups_tuser__sel_pk(@p_json, @q_json, @r_json);
SELECT JSON_PRETTY(@p_json) AS p_json; SELECT JSON_PRETTY(@q_json) AS q_json; SELECT JSON_PRETTY(@r_json) AS r_json;



SET @p_json = '', @q_json = '', @r_json = '';
SET @p_json = JSON_OBJECT('userid_comp', 'EQ', 'userid', @userid__sel_middle);
-- ERROR: limit key
CALL ups_tuser__sel_pk(@p_json, @q_json, @r_json);
SELECT JSON_PRETTY(@p_json) AS p_json; SELECT JSON_PRETTY(@q_json) AS q_json; SELECT JSON_PRETTY(@r_json) AS r_json;

SET @p_json = '', @q_json = '', @r_json = '';
SET @p_json = JSON_OBJECT('limit', '', 'userid_comp', 'EQ', 'userid', @userid__sel_middle);
-- ERROR: limit value
CALL ups_tuser__sel_pk(@p_json, @q_json, @r_json);
SELECT JSON_PRETTY(@p_json) AS p_json; SELECT JSON_PRETTY(@q_json) AS q_json; SELECT JSON_PRETTY(@r_json) AS r_json;



-- ==============================================================================================
-- 
-- del
-- 
-- ==============================================================================================



SET @p_json = '', @r_json = '';
SET @p_json = JSON_OBJECT('userid', 'unmatched');
-- FAIL: unmatched
CALL ups_tuser__del(@p_json, @r_json);
SELECT JSON_PRETTY(@p_json) AS p_json; SELECT JSON_PRETTY(@r_json) AS r_json;



SET @p_json = '', @r_json = '';
SET @p_json = JSON_OBJECT('userid', @glb_userid);
-- SUCC: delete
CALL ups_tuser__del(@p_json, @r_json);
SELECT JSON_PRETTY(@p_json) AS p_json; SELECT JSON_PRETTY(@r_json) AS r_json;
SELECT * FROM tuser;



SET @p_json = '', @r_json = '';
-- ERROR: JSON
CALL ups_tuser__del(@p_json, @r_json);
SELECT JSON_PRETTY(@p_json) AS p_json; SELECT JSON_PRETTY(@r_json) AS r_json;



SET @p_json = '', @r_json = '';
SET @p_json = JSON_OBJECT();
-- ERROR: userid key
CALL ups_tuser__del(@p_json, @r_json);
SELECT JSON_PRETTY(@p_json) AS p_json; SELECT JSON_PRETTY(@r_json) AS r_json;

SET @p_json = '', @r_json = '';
SET @p_json = JSON_OBJECT('userid', NULL);
-- ERROR: userid value
CALL ups_tuser__del(@p_json, @r_json);
SELECT JSON_PRETTY(@p_json) AS p_json; SELECT JSON_PRETTY(@r_json) AS r_json;


