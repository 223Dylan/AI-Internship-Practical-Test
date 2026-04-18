BEGIN TRANSACTION;
CREATE TABLE "auth_group" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "name" varchar(150) NOT NULL UNIQUE);
CREATE TABLE "auth_group_permissions" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "group_id" integer NOT NULL REFERENCES "auth_group" ("id") DEFERRABLE INITIALLY DEFERRED, "permission_id" integer NOT NULL REFERENCES "auth_permission" ("id") DEFERRABLE INITIALLY DEFERRED);
CREATE TABLE "auth_permission" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "content_type_id" integer NOT NULL REFERENCES "django_content_type" ("id") DEFERRABLE INITIALLY DEFERRED, "codename" varchar(100) NOT NULL, "name" varchar(255) NOT NULL);
INSERT INTO "auth_permission" VALUES(1,1,'add_logentry','Can add log entry');
INSERT INTO "auth_permission" VALUES(2,1,'change_logentry','Can change log entry');
INSERT INTO "auth_permission" VALUES(3,1,'delete_logentry','Can delete log entry');
INSERT INTO "auth_permission" VALUES(4,1,'view_logentry','Can view log entry');
INSERT INTO "auth_permission" VALUES(5,3,'add_permission','Can add permission');
INSERT INTO "auth_permission" VALUES(6,3,'change_permission','Can change permission');
INSERT INTO "auth_permission" VALUES(7,3,'delete_permission','Can delete permission');
INSERT INTO "auth_permission" VALUES(8,3,'view_permission','Can view permission');
INSERT INTO "auth_permission" VALUES(9,2,'add_group','Can add group');
INSERT INTO "auth_permission" VALUES(10,2,'change_group','Can change group');
INSERT INTO "auth_permission" VALUES(11,2,'delete_group','Can delete group');
INSERT INTO "auth_permission" VALUES(12,2,'view_group','Can view group');
INSERT INTO "auth_permission" VALUES(13,4,'add_user','Can add user');
INSERT INTO "auth_permission" VALUES(14,4,'change_user','Can change user');
INSERT INTO "auth_permission" VALUES(15,4,'delete_user','Can delete user');
INSERT INTO "auth_permission" VALUES(16,4,'view_user','Can view user');
INSERT INTO "auth_permission" VALUES(17,5,'add_contenttype','Can add content type');
INSERT INTO "auth_permission" VALUES(18,5,'change_contenttype','Can change content type');
INSERT INTO "auth_permission" VALUES(19,5,'delete_contenttype','Can delete content type');
INSERT INTO "auth_permission" VALUES(20,5,'view_contenttype','Can view content type');
INSERT INTO "auth_permission" VALUES(21,6,'add_session','Can add session');
INSERT INTO "auth_permission" VALUES(22,6,'change_session','Can change session');
INSERT INTO "auth_permission" VALUES(23,6,'delete_session','Can delete session');
INSERT INTO "auth_permission" VALUES(24,6,'view_session','Can view session');
INSERT INTO "auth_permission" VALUES(25,11,'add_taskstep','Can add task step');
INSERT INTO "auth_permission" VALUES(26,11,'change_taskstep','Can change task step');
INSERT INTO "auth_permission" VALUES(27,11,'delete_taskstep','Can delete task step');
INSERT INTO "auth_permission" VALUES(28,11,'view_taskstep','Can view task step');
INSERT INTO "auth_permission" VALUES(29,8,'add_taskentity','Can add task entity');
INSERT INTO "auth_permission" VALUES(30,8,'change_taskentity','Can change task entity');
INSERT INTO "auth_permission" VALUES(31,8,'delete_taskentity','Can delete task entity');
INSERT INTO "auth_permission" VALUES(32,8,'view_taskentity','Can view task entity');
INSERT INTO "auth_permission" VALUES(33,10,'add_taskstatushistory','Can add task status history');
INSERT INTO "auth_permission" VALUES(34,10,'change_taskstatushistory','Can change task status history');
INSERT INTO "auth_permission" VALUES(35,10,'delete_taskstatushistory','Can delete task status history');
INSERT INTO "auth_permission" VALUES(36,10,'view_taskstatushistory','Can view task status history');
INSERT INTO "auth_permission" VALUES(37,9,'add_taskmessage','Can add task message');
INSERT INTO "auth_permission" VALUES(38,9,'change_taskmessage','Can change task message');
INSERT INTO "auth_permission" VALUES(39,9,'delete_taskmessage','Can delete task message');
INSERT INTO "auth_permission" VALUES(40,9,'view_taskmessage','Can view task message');
INSERT INTO "auth_permission" VALUES(41,7,'add_task','Can add task');
INSERT INTO "auth_permission" VALUES(42,7,'change_task','Can change task');
INSERT INTO "auth_permission" VALUES(43,7,'delete_task','Can delete task');
INSERT INTO "auth_permission" VALUES(44,7,'view_task','Can view task');
CREATE TABLE "auth_user" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "password" varchar(128) NOT NULL, "last_login" datetime NULL, "is_superuser" bool NOT NULL, "username" varchar(150) NOT NULL UNIQUE, "last_name" varchar(150) NOT NULL, "email" varchar(254) NOT NULL, "is_staff" bool NOT NULL, "is_active" bool NOT NULL, "date_joined" datetime NOT NULL, "first_name" varchar(150) NOT NULL);
INSERT INTO "auth_user" VALUES(1,'pbkdf2_sha256$1200000$FMohaPTkSgCfL4QnN5Xcyp$rO0iV9cKUPml20ZB3/vu5YL7Zyys8rF1ZMIHYMF8xks=','2026-04-16 11:28:35.618201',1,'lenovo','','makau.dylan@gmail.com',1,1,'2026-04-16 11:28:23.697443','');
CREATE TABLE "auth_user_groups" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED, "group_id" integer NOT NULL REFERENCES "auth_group" ("id") DEFERRABLE INITIALLY DEFERRED);
CREATE TABLE "auth_user_user_permissions" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED, "permission_id" integer NOT NULL REFERENCES "auth_permission" ("id") DEFERRABLE INITIALLY DEFERRED);
CREATE TABLE "core_task" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "code" varchar(24) NOT NULL UNIQUE, "customer_request_text" text NOT NULL, "intent" varchar(32) NOT NULL, "entities" text NOT NULL CHECK ((JSON_VALID("entities") OR "entities" IS NULL)), "risk_score" smallint unsigned NOT NULL CHECK ("risk_score" >= 0), "risk_reasons" text NOT NULL CHECK ((JSON_VALID("risk_reasons") OR "risk_reasons" IS NULL)), "status" varchar(16) NOT NULL, "assigned_team" varchar(16) NOT NULL, "created_at" datetime NOT NULL, "updated_at" datetime NOT NULL, "assignment_reason" text NOT NULL);
INSERT INTO "core_task" VALUES(9,'VNH-20260418-DURG3F','I need to send KES 15,000 to my mother in Kisumu urgently.','send_money','{"urgency": "high", "amount": "15000", "currency": "KES"}',60,'["Base operational risk.", "Money transfer requests require stronger fraud checks.", "Moderate transfer amount (>=15,000 KES) increases risk.", "High urgency requests have higher error and fraud pressure."]','PENDING','FINANCE','2026-04-18 14:34:17.602399','2026-04-18 14:34:17.602399','Money transfer workflows are handled by Finance for fraud and settlement checks.');
INSERT INTO "core_task" VALUES(10,'VNH-20260418-92ZOFX','Please verify my land title deed for the plot in Karen.','verify_document','{"urgency": "normal"}',42,'["Base operational risk.", "Document verification carries elevated fraud/legal exposure."]','IN_PROGRESS','LEGAL','2026-04-18 14:34:17.615396','2026-04-18 14:34:17.690395','Document verification requests are routed to Legal for validation.');
INSERT INTO "core_task" VALUES(11,'VNH-20260418-F20UZO','Can someone clean my apartment in Westlands on Friday?','hire_service','{"urgency": "normal"}',28,'["Base operational risk.", "Service hire has moderate fulfillment and quality risk."]','COMPLETED','OPERATIONS','2026-04-18 14:34:17.629398','2026-04-18 14:34:17.707401','Service fulfillment and field logistics are coordinated by Operations.');
INSERT INTO "core_task" VALUES(12,'VNH-20260418-TT172U','I need an airport pickup in Nairobi on Tuesday morning.','get_airport_transfer','{"urgency": "normal"}',30,'["Base operational risk.", "Airport transfer has moderate coordination and trust risk."]','IN_PROGRESS','OPERATIONS','2026-04-18 14:34:17.663396','2026-04-18 14:34:17.716410','Service fulfillment and field logistics are coordinated by Operations.');
INSERT INTO "core_task" VALUES(13,'VNH-20260418-JRKJ1O','What is the status of my last request? Task follow up please.','check_status','{"urgency": "normal"}',22,'["Base operational risk.", "Status checks carry low execution risk."]','PENDING','SUPPORT','2026-04-18 14:34:17.677399','2026-04-18 14:34:17.677399','Status follow-ups are handled by Support for customer communication.');
CREATE TABLE "core_taskentity" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "key" varchar(64) NOT NULL, "value" text NOT NULL, "created_at" datetime NOT NULL, "task_id" bigint NOT NULL REFERENCES "core_task" ("id") DEFERRABLE INITIALLY DEFERRED, CONSTRAINT "uq_task_entity_kv" UNIQUE ("task_id", "key", "value"));
INSERT INTO "core_taskentity" VALUES(12,'urgency','high','2026-04-18 14:34:17.605400',9);
INSERT INTO "core_taskentity" VALUES(13,'amount','15000','2026-04-18 14:34:17.606395',9);
INSERT INTO "core_taskentity" VALUES(14,'currency','KES','2026-04-18 14:34:17.606395',9);
INSERT INTO "core_taskentity" VALUES(15,'urgency','normal','2026-04-18 14:34:17.617396',10);
INSERT INTO "core_taskentity" VALUES(16,'urgency','normal','2026-04-18 14:34:17.653401',11);
INSERT INTO "core_taskentity" VALUES(17,'urgency','normal','2026-04-18 14:34:17.666407',12);
INSERT INTO "core_taskentity" VALUES(18,'urgency','normal','2026-04-18 14:34:17.679395',13);
CREATE TABLE "core_taskmessage" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "channel" varchar(16) NOT NULL, "content" text NOT NULL, "created_at" datetime NOT NULL, "task_id" bigint NOT NULL REFERENCES "core_task" ("id") DEFERRABLE INITIALLY DEFERRED, CONSTRAINT "uq_task_message_channel" UNIQUE ("task_id", "channel"));
INSERT INTO "core_taskmessage" VALUES(20,'WHATSAPP','Hi! Your request is received and now in Pending.
Task code: VNH-20260418-DURG3F
Team: Finance
We''ll keep you updated at each milestone.','2026-04-18 14:34:17.608395',9);
INSERT INTO "core_taskmessage" VALUES(21,'EMAIL','Subject: Vunoh Task Confirmation

Dear Customer,

Your request has been logged successfully.
Task Code: VNH-20260418-DURG3F
Intent: send_money
Current Status: Pending
Assigned Team: Finance
Risk Score: 60

We will notify you as your task progresses.

Regards,
Vunoh Global','2026-04-18 14:34:17.609395',9);
INSERT INTO "core_taskmessage" VALUES(22,'SMS','Vunoh: Task VNH-20260418-DURG3F is Pending. Team Finance. Reply with code for updates.','2026-04-18 14:34:17.609395',9);
INSERT INTO "core_taskmessage" VALUES(23,'WHATSAPP','Hi! Your request is received and now in Pending.
Task code: VNH-20260418-92ZOFX
Team: Legal
We''ll keep you updated at each milestone.','2026-04-18 14:34:17.621401',10);
INSERT INTO "core_taskmessage" VALUES(24,'EMAIL','Subject: Vunoh Task Confirmation

Dear Customer,

Your request has been logged successfully.
Task Code: VNH-20260418-92ZOFX
Intent: verify_document
Current Status: Pending
Assigned Team: Legal
Risk Score: 42

We will notify you as your task progresses.

Regards,
Vunoh Global','2026-04-18 14:34:17.622400',10);
INSERT INTO "core_taskmessage" VALUES(25,'SMS','Vunoh: Task VNH-20260418-92ZOFX is Pending. Team Legal. Reply with code for updates.','2026-04-18 14:34:17.622400',10);
INSERT INTO "core_taskmessage" VALUES(26,'WHATSAPP','Hi! Your request is received and now in Pending.
Task code: VNH-20260418-F20UZO
Team: Operations
We''ll keep you updated at each milestone.','2026-04-18 14:34:17.656399',11);
INSERT INTO "core_taskmessage" VALUES(27,'EMAIL','Subject: Vunoh Task Confirmation

Dear Customer,

Your request has been logged successfully.
Task Code: VNH-20260418-F20UZO
Intent: hire_service
Current Status: Pending
Assigned Team: Operations
Risk Score: 28

We will notify you as your task progresses.

Regards,
Vunoh Global','2026-04-18 14:34:17.656399',11);
INSERT INTO "core_taskmessage" VALUES(28,'SMS','Vunoh: Task VNH-20260418-F20UZO is Pending. Team Operations. Reply with code for updates.','2026-04-18 14:34:17.657396',11);
INSERT INTO "core_taskmessage" VALUES(29,'WHATSAPP','Hi! Your request is received and now in Pending.
Task code: VNH-20260418-TT172U
Team: Operations
We''ll keep you updated at each milestone.','2026-04-18 14:34:17.669399',12);
INSERT INTO "core_taskmessage" VALUES(30,'EMAIL','Subject: Vunoh Task Confirmation

Dear Customer,

Your request has been logged successfully.
Task Code: VNH-20260418-TT172U
Intent: get_airport_transfer
Current Status: Pending
Assigned Team: Operations
Risk Score: 30

We will notify you as your task progresses.

Regards,
Vunoh Global','2026-04-18 14:34:17.669399',12);
INSERT INTO "core_taskmessage" VALUES(31,'SMS','Vunoh: Task VNH-20260418-TT172U is Pending. Team Operations. Reply with code for updates.','2026-04-18 14:34:17.670399',12);
INSERT INTO "core_taskmessage" VALUES(32,'WHATSAPP','Hi! Your request is received and now in Pending.
Task code: VNH-20260418-JRKJ1O
Team: Support
We''ll keep you updated at each milestone.','2026-04-18 14:34:17.681397',13);
INSERT INTO "core_taskmessage" VALUES(33,'EMAIL','Subject: Vunoh Task Confirmation

Dear Customer,

Your request has been logged successfully.
Task Code: VNH-20260418-JRKJ1O
Intent: check_status
Current Status: Pending
Assigned Team: Support
Risk Score: 22

We will notify you as your task progresses.

Regards,
Vunoh Global','2026-04-18 14:34:17.681397',13);
INSERT INTO "core_taskmessage" VALUES(34,'SMS','Vunoh: Task VNH-20260418-JRKJ1O is Pending. Team Support. Reply with code for updates.','2026-04-18 14:34:17.682397',13);
CREATE TABLE "core_taskstatushistory" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "from_status" varchar(16) NOT NULL, "to_status" varchar(16) NOT NULL, "changed_at" datetime NOT NULL, "task_id" bigint NOT NULL REFERENCES "core_task" ("id") DEFERRABLE INITIALLY DEFERRED);
INSERT INTO "core_taskstatushistory" VALUES(12,'PENDING','PENDING','2026-04-18 14:34:17.609395',9);
INSERT INTO "core_taskstatushistory" VALUES(13,'PENDING','PENDING','2026-04-18 14:34:17.622400',10);
INSERT INTO "core_taskstatushistory" VALUES(14,'PENDING','PENDING','2026-04-18 14:34:17.657396',11);
INSERT INTO "core_taskstatushistory" VALUES(15,'PENDING','PENDING','2026-04-18 14:34:17.670399',12);
INSERT INTO "core_taskstatushistory" VALUES(16,'PENDING','PENDING','2026-04-18 14:34:17.682397',13);
INSERT INTO "core_taskstatushistory" VALUES(17,'PENDING','IN_PROGRESS','2026-04-18 14:34:17.691394',10);
INSERT INTO "core_taskstatushistory" VALUES(18,'PENDING','IN_PROGRESS','2026-04-18 14:34:17.699395',11);
INSERT INTO "core_taskstatushistory" VALUES(19,'IN_PROGRESS','COMPLETED','2026-04-18 14:34:17.709397',11);
INSERT INTO "core_taskstatushistory" VALUES(20,'PENDING','IN_PROGRESS','2026-04-18 14:34:17.717395',12);
CREATE TABLE "core_taskstep" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "step_order" smallint unsigned NOT NULL CHECK ("step_order" >= 0), "description" text NOT NULL, "created_at" datetime NOT NULL, "task_id" bigint NOT NULL REFERENCES "core_task" ("id") DEFERRABLE INITIALLY DEFERRED, CONSTRAINT "uq_task_step_order" UNIQUE ("task_id", "step_order"));
INSERT INTO "core_taskstep" VALUES(32,1,'Confirm sender identity and transaction authorization.','2026-04-18 14:34:17.606395',9);
INSERT INTO "core_taskstep" VALUES(33,2,'Verify recipient details for recipient.','2026-04-18 14:34:17.607396',9);
INSERT INTO "core_taskstep" VALUES(34,3,'Run fraud checks and compliance screening.','2026-04-18 14:34:17.607396',9);
INSERT INTO "core_taskstep" VALUES(35,4,'Initiate transfer and capture confirmation reference.','2026-04-18 14:34:17.607396',9);
INSERT INTO "core_taskstep" VALUES(36,5,'Notify customer after transfer confirmation.','2026-04-18 14:34:17.608395',9);
INSERT INTO "core_taskstep" VALUES(37,1,'Collect and validate submitted document details.','2026-04-18 14:34:17.618400',10);
INSERT INTO "core_taskstep" VALUES(38,2,'Run records verification with relevant authorities.','2026-04-18 14:34:17.619402',10);
INSERT INTO "core_taskstep" VALUES(39,3,'Escalate suspicious mismatches to Legal review.','2026-04-18 14:34:17.620398',10);
INSERT INTO "core_taskstep" VALUES(40,4,'Prepare verification result and supporting notes.','2026-04-18 14:34:17.620398',10);
INSERT INTO "core_taskstep" VALUES(41,5,'Share verification outcome with customer.','2026-04-18 14:34:17.621401',10);
INSERT INTO "core_taskstep" VALUES(42,1,'Confirm service scope for requested service.','2026-04-18 14:34:17.654397',11);
INSERT INTO "core_taskstep" VALUES(43,2,'Match and shortlist providers near Nairobi.','2026-04-18 14:34:17.655398',11);
INSERT INTO "core_taskstep" VALUES(44,3,'Confirm schedule and service fee with customer.','2026-04-18 14:34:17.655398',11);
INSERT INTO "core_taskstep" VALUES(45,4,'Dispatch provider and monitor completion evidence.','2026-04-18 14:34:17.655398',11);
INSERT INTO "core_taskstep" VALUES(46,5,'Close task after customer sign-off.','2026-04-18 14:34:17.656399',11);
INSERT INTO "core_taskstep" VALUES(47,1,'Collect arrival details and passenger contacts.','2026-04-18 14:34:17.667396',12);
INSERT INTO "core_taskstep" VALUES(48,2,'Assign verified driver and vehicle for Nairobi.','2026-04-18 14:34:17.667396',12);
INSERT INTO "core_taskstep" VALUES(49,3,'Share pickup instructions with customer.','2026-04-18 14:34:17.668395',12);
INSERT INTO "core_taskstep" VALUES(50,4,'Track arrival and pickup completion status.','2026-04-18 14:34:17.668395',12);
INSERT INTO "core_taskstep" VALUES(51,5,'Confirm successful drop-off and close task.','2026-04-18 14:34:17.668395',12);
INSERT INTO "core_taskstep" VALUES(52,1,'Retrieve task details by code and current workflow status.','2026-04-18 14:34:17.679395',13);
INSERT INTO "core_taskstep" VALUES(53,2,'Confirm latest update from assigned operations team.','2026-04-18 14:34:17.680397',13);
INSERT INTO "core_taskstep" VALUES(54,3,'Prepare concise progress summary for customer.','2026-04-18 14:34:17.680397',13);
INSERT INTO "core_taskstep" VALUES(55,4,'Share next expected action and timeline.','2026-04-18 14:34:17.681397',13);
CREATE TABLE "django_admin_log" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "object_id" text NULL, "object_repr" varchar(200) NOT NULL, "action_flag" smallint unsigned NOT NULL CHECK ("action_flag" >= 0), "change_message" text NOT NULL, "content_type_id" integer NULL REFERENCES "django_content_type" ("id") DEFERRABLE INITIALLY DEFERRED, "user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED, "action_time" datetime NOT NULL);
INSERT INTO "django_admin_log" VALUES(1,'1','demo_task1 (send_money)',1,'[{"added": {}}, {"added": {"name": "task entity", "object": "demo_task1: amount=15000"}}, {"added": {"name": "task entity", "object": "demo_task1: location=Kisumu"}}, {"added": {"name": "task step", "object": "demo_task1 step 3"}}, {"added": {"name": "task step", "object": "demo_task1 step 4"}}, {"added": {"name": "task message", "object": "demo_task1 WHATSAPP"}}]',7,1,'2026-04-16 11:34:05.890759');
CREATE TABLE "django_content_type" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "app_label" varchar(100) NOT NULL, "model" varchar(100) NOT NULL);
INSERT INTO "django_content_type" VALUES(1,'admin','logentry');
INSERT INTO "django_content_type" VALUES(2,'auth','group');
INSERT INTO "django_content_type" VALUES(3,'auth','permission');
INSERT INTO "django_content_type" VALUES(4,'auth','user');
INSERT INTO "django_content_type" VALUES(5,'contenttypes','contenttype');
INSERT INTO "django_content_type" VALUES(6,'sessions','session');
INSERT INTO "django_content_type" VALUES(7,'core','task');
INSERT INTO "django_content_type" VALUES(8,'core','taskentity');
INSERT INTO "django_content_type" VALUES(9,'core','taskmessage');
INSERT INTO "django_content_type" VALUES(10,'core','taskstatushistory');
INSERT INTO "django_content_type" VALUES(11,'core','taskstep');
CREATE TABLE "django_migrations" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "app" varchar(255) NOT NULL, "name" varchar(255) NOT NULL, "applied" datetime NOT NULL);
INSERT INTO "django_migrations" VALUES(1,'contenttypes','0001_initial','2026-04-16 11:03:46.026247');
INSERT INTO "django_migrations" VALUES(2,'auth','0001_initial','2026-04-16 11:03:46.087256');
INSERT INTO "django_migrations" VALUES(3,'admin','0001_initial','2026-04-16 11:03:46.128763');
INSERT INTO "django_migrations" VALUES(4,'admin','0002_logentry_remove_auto_add','2026-04-16 11:03:46.194195');
INSERT INTO "django_migrations" VALUES(5,'admin','0003_logentry_add_action_flag_choices','2026-04-16 11:03:46.214774');
INSERT INTO "django_migrations" VALUES(6,'contenttypes','0002_remove_content_type_name','2026-04-16 11:03:46.255778');
INSERT INTO "django_migrations" VALUES(7,'auth','0002_alter_permission_name_max_length','2026-04-16 11:03:46.285782');
INSERT INTO "django_migrations" VALUES(8,'auth','0003_alter_user_email_max_length','2026-04-16 11:03:46.309776');
INSERT INTO "django_migrations" VALUES(9,'auth','0004_alter_user_username_opts','2026-04-16 11:03:46.330774');
INSERT INTO "django_migrations" VALUES(10,'auth','0005_alter_user_last_login_null','2026-04-16 11:03:46.363949');
INSERT INTO "django_migrations" VALUES(11,'auth','0006_require_contenttypes_0002','2026-04-16 11:03:46.372784');
INSERT INTO "django_migrations" VALUES(12,'auth','0007_alter_validators_add_error_messages','2026-04-16 11:03:46.391774');
INSERT INTO "django_migrations" VALUES(13,'auth','0008_alter_user_username_max_length','2026-04-16 11:03:46.419778');
INSERT INTO "django_migrations" VALUES(14,'auth','0009_alter_user_last_name_max_length','2026-04-16 11:03:46.444777');
INSERT INTO "django_migrations" VALUES(15,'auth','0010_alter_group_name_max_length','2026-04-16 11:03:46.474054');
INSERT INTO "django_migrations" VALUES(16,'auth','0011_update_proxy_permissions','2026-04-16 11:03:46.495791');
INSERT INTO "django_migrations" VALUES(17,'auth','0012_alter_user_first_name_max_length','2026-04-16 11:03:46.530777');
INSERT INTO "django_migrations" VALUES(18,'sessions','0001_initial','2026-04-16 11:03:46.558781');
INSERT INTO "django_migrations" VALUES(19,'core','0001_initial','2026-04-16 11:22:38.466325');
INSERT INTO "django_migrations" VALUES(20,'core','0002_task_assignment_reason','2026-04-18 14:33:36.182412');
CREATE TABLE "django_session" ("session_key" varchar(40) NOT NULL PRIMARY KEY, "session_data" text NOT NULL, "expire_date" datetime NOT NULL);
INSERT INTO "django_session" VALUES('hngen1ecmqsc19is697vntiqkixp8gbz','.eJxVjEEOwiAQRe_C2pDCCAwu3fcMBGamUjVtUtqV8e7apAvd_vfef6mUt7WmrcmSRlYXZdTpdyuZHjLtgO95us2a5mldxqJ3RR-06X5meV4P9--g5la_NUaOHi0LFKGBXWDpSMCji3KO1hMAGXB2cAihKyDkDXZFmAaTKaB6fwDx0zhJ:1wDKtf:etGkHbORgXsROqtuyQBHg_S5mYZdKeXGGI8aOktf9Y8','2026-04-30 11:28:35.624201');
CREATE UNIQUE INDEX "auth_group_permissions_group_id_permission_id_0cd325b0_uniq" ON "auth_group_permissions" ("group_id", "permission_id");
CREATE INDEX "auth_group_permissions_group_id_b120cbf9" ON "auth_group_permissions" ("group_id");
CREATE INDEX "auth_group_permissions_permission_id_84c5c92e" ON "auth_group_permissions" ("permission_id");
CREATE UNIQUE INDEX "auth_user_groups_user_id_group_id_94350c0c_uniq" ON "auth_user_groups" ("user_id", "group_id");
CREATE INDEX "auth_user_groups_user_id_6a12ed8b" ON "auth_user_groups" ("user_id");
CREATE INDEX "auth_user_groups_group_id_97559544" ON "auth_user_groups" ("group_id");
CREATE UNIQUE INDEX "auth_user_user_permissions_user_id_permission_id_14a6b632_uniq" ON "auth_user_user_permissions" ("user_id", "permission_id");
CREATE INDEX "auth_user_user_permissions_user_id_a95ead1b" ON "auth_user_user_permissions" ("user_id");
CREATE INDEX "auth_user_user_permissions_permission_id_1fbb5f2c" ON "auth_user_user_permissions" ("permission_id");
CREATE INDEX "django_admin_log_content_type_id_c4bce8eb" ON "django_admin_log" ("content_type_id");
CREATE INDEX "django_admin_log_user_id_c564eba6" ON "django_admin_log" ("user_id");
CREATE UNIQUE INDEX "django_content_type_app_label_model_76bd3d3b_uniq" ON "django_content_type" ("app_label", "model");
CREATE UNIQUE INDEX "auth_permission_content_type_id_codename_01ab375a_uniq" ON "auth_permission" ("content_type_id", "codename");
CREATE INDEX "auth_permission_content_type_id_2f476e4b" ON "auth_permission" ("content_type_id");
CREATE INDEX "django_session_expire_date_a5c62663" ON "django_session" ("expire_date");
CREATE INDEX "core_taskentity_key_8839f1c6" ON "core_taskentity" ("key");
CREATE INDEX "core_taskentity_task_id_f157d348" ON "core_taskentity" ("task_id");
CREATE INDEX "core_tasken_task_id_25408d_idx" ON "core_taskentity" ("task_id", "key");
CREATE INDEX "core_taskmessage_task_id_f931a095" ON "core_taskmessage" ("task_id");
CREATE INDEX "core_taskme_task_id_55a63e_idx" ON "core_taskmessage" ("task_id", "channel");
CREATE INDEX "core_taskstatushistory_changed_at_decb1e20" ON "core_taskstatushistory" ("changed_at");
CREATE INDEX "core_taskstatushistory_task_id_cab6c168" ON "core_taskstatushistory" ("task_id");
CREATE INDEX "core_taskst_task_id_a23a1f_idx" ON "core_taskstatushistory" ("task_id", "changed_at");
CREATE INDEX "core_taskstep_task_id_447cd122" ON "core_taskstep" ("task_id");
CREATE INDEX "core_taskst_task_id_6a99d9_idx" ON "core_taskstep" ("task_id", "step_order");
CREATE INDEX "core_task_intent_b586b1f6" ON "core_task" ("intent");
CREATE INDEX "core_task_status_fc6ba3bd" ON "core_task" ("status");
CREATE INDEX "core_task_assigned_team_fc89c207" ON "core_task" ("assigned_team");
CREATE INDEX "core_task_created_at_9bb6b8d1" ON "core_task" ("created_at");
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('django_migrations',20);
INSERT INTO "sqlite_sequence" VALUES('django_admin_log',1);
INSERT INTO "sqlite_sequence" VALUES('django_content_type',11);
INSERT INTO "sqlite_sequence" VALUES('auth_permission',44);
INSERT INTO "sqlite_sequence" VALUES('auth_group',0);
INSERT INTO "sqlite_sequence" VALUES('auth_user',1);
INSERT INTO "sqlite_sequence" VALUES('core_taskentity',18);
INSERT INTO "sqlite_sequence" VALUES('core_taskstep',55);
INSERT INTO "sqlite_sequence" VALUES('core_taskmessage',34);
INSERT INTO "sqlite_sequence" VALUES('core_taskstatushistory',20);
INSERT INTO "sqlite_sequence" VALUES('core_task',13);
COMMIT;
