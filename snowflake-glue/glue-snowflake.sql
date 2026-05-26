create or replace database glue_data

use glue_data

create or replace schema orders

CREATE OR REPLACE TABLE orders (
    order_id            INTEGER,
    order_date          TIMESTAMP,
    order_customer_id   INTEGER,
    order_status        STRING
);

INSERT INTO orders VALUES
(1, '2013-07-25 00:00:00.0', 11599, 'CLOSED'),
(2, '2013-07-25 00:00:00.0', 256, 'PENDING_PAYMENT'),
(3, '2013-07-25 00:00:00.0', 12111, 'COMPLETE');

select * from orders

delete from GLUE_DATA.ORDERS.ORDERS