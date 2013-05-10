-- 
-- If you do not use the mastertickets plugin, you need to use this create, 
--   s.t., the corresponding table is created.
-- This table is need at the projectplan plugin version 1.0.0 or higher.
--
-- Table structure for table `mastertickets`
--
-- Note: Do NOT forget to convert the ticket dependencies at
--   admin -> ProjectPlan -> General Settings -> enable_mastertickets_compatiblity_mode
--

CREATE TABLE `mastertickets` (
  `source` int(11) NOT NULL DEFAULT '0',
  `dest` int(11) NOT NULL DEFAULT '0',
  PRIMARY KEY (`source`,`dest`)
);
