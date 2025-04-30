BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "sessions" (
	"session_id"	TEXT NOT NULL UNIQUE,
	"user_id"	TEXT NOT NULL,
	"time_created"	INTEGER NOT NULL,
	FOREIGN KEY("user_id") REFERENCES "users"("user_id"),
	PRIMARY KEY("session_id","user_id")
);
CREATE TABLE IF NOT EXISTS "members" (
	"chat_id"	TEXT NOT NULL,
	"user_id"	TEXT NOT NULL,
	FOREIGN KEY("chat_id") REFERENCES "chats"("chat_id"),
	FOREIGN KEY("user_id") REFERENCES "users"("user_id"),
	PRIMARY KEY("chat_id","user_id")
);
CREATE TABLE IF NOT EXISTS "messages" (
	"message_id"	TEXT NOT NULL UNIQUE,
	"message"	TEXT NOT NULL,
	"time"	INTEGER NOT NULL,
	"author"	TEXT NOT NULL,
	"chat_id"	INTEGER NOT NULL,
	FOREIGN KEY("chat_id") REFERENCES "chats"("chat_id"),
	FOREIGN KEY("author") REFERENCES "users"("user_id"),
	PRIMARY KEY("message_id")
);
CREATE TABLE IF NOT EXISTS "chats" (
	"chat_id"	TEXT NOT NULL,
	"chat_name"	TEXT,
	"chat_photo"	TEXT,
	"group"	INTEGER NOT NULL,
	PRIMARY KEY("chat_id")
);
CREATE TABLE IF NOT EXISTS "users" (
	"user_id"	TEXT NOT NULL UNIQUE,
	"username"	TEXT NOT NULL UNIQUE,
	"pfp"	TEXT NOT NULL,
	"bio"	TEXT,
	PRIMARY KEY("user_id")
);
COMMIT;
