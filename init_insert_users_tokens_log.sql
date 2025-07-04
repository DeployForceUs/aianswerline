INSERT INTO users (id, phone_number, verification_code, is_verified, tokens_balance, created_at) VALUES
  (1,  '19998887777', '000000', true, 1, '2025-07-03 00:36:30.258766'),
  (3, '+19999999999', '000000', true, 1, '2025-07-03 02:35:03.10508'),
  (6, '+17866027656', '000000', true, 1, '2025-07-03 02:44:40.935826');

INSERT INTO tokens_log (id, user_id, change, source, description, created_at) VALUES
  (1, 1,  2, 'system', 'Initial 2 tokens for new user', '2025-07-03 00:36:30.259841'),
  (2, 1, -1, 'chat',   'Message: Hello, test message',  '2025-07-03 00:36:30.261876'),
  (3, 3,  2, 'system', 'Initial 2 tokens for new user', '2025-07-03 02:35:03.106874'),
  (4, 3, -1, 'chat',   'Message: hello from curl',      '2025-07-03 02:35:03.111141'),
  (5, 6,  2, 'system', 'Initial 2 tokens for new user', '2025-07-03 02:44:40.936619'),
  (6, 6, -1, 'chat',   'Message: Test',                 '2025-07-03 02:44:40.937924'),
  (7, 6, -1, 'chat',   'Message: Good. You?',           '2025-07-03 02:45:41.899172');
