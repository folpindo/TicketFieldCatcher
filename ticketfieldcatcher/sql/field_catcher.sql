CREATE TABLE daco_field_catcher (
  ticket int(10) unsigned NOT NULL AUTO_INCREMENT,
  sku text,
  brand text,
  deleted tinyint(1) DEFAULT NULL,
  PRIMARY KEY (ticket)
)

