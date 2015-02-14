SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

ALTER TABLE stat_statements_data
   ADD COLUMN ssd_user_id integer DEFAULT 0;
