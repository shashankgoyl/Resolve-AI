-- ============================================================================
-- Resolve AI — demo seed data
-- Safe to re-run: clears demo rows first, then re-inserts.
-- This seeds the SAME 5 tickets the backend's in-memory demo mode uses,
-- so the dashboard looks identical whether DEMO_MODE=true or you've
-- pointed the frontend at a real Supabase project with this seed applied.
-- ============================================================================

delete from audit_logs where ticket_id in (select id from support_tickets where is_demo = true);
delete from agent_actions where ticket_id in (select id from support_tickets where is_demo = true);
delete from responses where ticket_id in (select id from support_tickets where is_demo = true);
delete from engineering_issues where ticket_id in (select id from support_tickets where is_demo = true);
delete from knowledge_sources where ticket_id in (select id from support_tickets where is_demo = true);
delete from ai_analyses where ticket_id in (select id from support_tickets where is_demo = true);
delete from agent_runs where ticket_id in (select id from support_tickets where is_demo = true);
delete from emails where ticket_id in (select id from support_tickets where is_demo = true);
delete from support_tickets where is_demo = true;
delete from customers where email like '%@demo.resolveai.dev';

-- customers
insert into customers (id, email, full_name, company, plan) values
  ('d1000000-0000-0000-0000-000000000001', 'priya.sharma@demo.resolveai.dev', 'Priya Sharma', 'Northwind Retail', 'growth'),
  ('d1000000-0000-0000-0000-000000000002', 'alex.chen@demo.resolveai.dev', 'Alex Chen', 'Fenwick Labs', 'pro'),
  ('d1000000-0000-0000-0000-000000000003', 'maria.gomez@demo.resolveai.dev', 'Maria Gomez', 'Solstice Apps', 'starter'),
  ('d1000000-0000-0000-0000-000000000004', 'rahul.verma@demo.resolveai.dev', 'Rahul Verma', 'Verma & Co', 'growth'),
  ('d1000000-0000-0000-0000-000000000005', 'liu.wei@demo.resolveai.dev', 'Liu Wei', 'Orbital Freight', 'pro')
on conflict (id) do nothing;

-- ticket 1 — payment failed but money deducted (NEEDS_ENGINEERING, urgent)
insert into support_tickets (id, ticket_number, customer_id, subject, category, priority, status, sentiment, is_demo, created_at)
values ('e1000000-0000-0000-0000-000000000001', 'RES-1001', 'd1000000-0000-0000-0000-000000000001',
  'Payment failed but money was deducted from my account', 'billing', 'urgent', 'escalated', 'frustrated', true, now() - interval '3 hours');

insert into emails (ticket_id, direction, from_address, to_address, subject, body_text, received_at) values
  ('e1000000-0000-0000-0000-000000000001', 'inbound', 'priya.sharma@demo.resolveai.dev', 'support@resolveai.dev',
   'Payment failed but money was deducted from my account',
   'Hi, I tried to upgrade to the Growth plan and the checkout showed "payment failed", but ₹4,999 was deducted from my card immediately. This is the second time this has happened. I need this refunded or the upgrade completed today — my card statement shows the charge from 20 minutes ago. Order reference is missing entirely on my end. Please help urgently.',
   now() - interval '3 hours');

-- ticket 2 — password reset not working (RESOLVED, medium)
insert into support_tickets (id, ticket_number, customer_id, subject, category, priority, status, sentiment, is_demo, resolved_at, first_response_at, created_at)
values ('e1000000-0000-0000-0000-000000000002', 'RES-1002', 'd1000000-0000-0000-0000-000000000002',
  'Password reset link not working', 'account', 'medium', 'resolved', 'negative', true, now() - interval '20 hours', now() - interval '23 hours', now() - interval '1 day');

insert into emails (ticket_id, direction, from_address, to_address, subject, body_text, received_at) values
  ('e1000000-0000-0000-0000-000000000002', 'inbound', 'alex.chen@demo.resolveai.dev', 'support@resolveai.dev',
   'Password reset link not working',
   'I requested a password reset three times now and the link in the email just goes to a blank page. I''m locked out of my account and can''t access my dashboard. Using Chrome on Mac. Can you help?',
   now() - interval '1 day');

-- ticket 3 — API returning 500 (NEEDS_ENGINEERING, high)
insert into support_tickets (id, ticket_number, customer_id, subject, category, priority, status, sentiment, is_demo, created_at)
values ('e1000000-0000-0000-0000-000000000003', 'RES-1003', 'd1000000-0000-0000-0000-000000000003',
  'API returning 500 on /v1/contacts since this morning', 'technical', 'high', 'in_progress', 'negative', true, now() - interval '5 hours');

insert into emails (ticket_id, direction, from_address, to_address, subject, body_text, received_at) values
  ('e1000000-0000-0000-0000-000000000003', 'inbound', 'maria.gomez@demo.resolveai.dev', 'support@resolveai.dev',
   'API returning 500 on /v1/contacts since this morning',
   'Every call to POST /v1/contacts has returned a 500 Internal Server Error since around 9am UTC today. GET requests still work fine. This is blocking our onboarding flow in production. Can someone check the API status? Happy to share request IDs if useful.',
   now() - interval '5 hours');

-- ticket 4 — subscription not updated (RESOLVED, medium)
insert into support_tickets (id, ticket_number, customer_id, subject, category, priority, status, sentiment, is_demo, resolved_at, first_response_at, created_at)
values ('e1000000-0000-0000-0000-000000000004', 'RES-1004', 'd1000000-0000-0000-0000-000000000004',
  'Upgraded my plan but still seeing old limits', 'billing', 'medium', 'resolved', 'neutral', true, now() - interval '2 hours', now() - interval '7 hours', now() - interval '8 hours');

insert into emails (ticket_id, direction, from_address, to_address, subject, body_text, received_at) values
  ('e1000000-0000-0000-0000-000000000004', 'inbound', 'rahul.verma@demo.resolveai.dev', 'support@resolveai.dev',
   'Upgraded my plan but still seeing old limits',
   'I upgraded from Starter to Growth yesterday and the payment went through, but my dashboard still shows the Starter plan limits (500 contacts). Can you refresh this on your end?',
   now() - interval '8 hours');

-- ticket 5 — data export failed (NEEDS_HUMAN_REVIEW, medium)
insert into support_tickets (id, ticket_number, customer_id, subject, category, priority, status, sentiment, is_demo, created_at)
values ('e1000000-0000-0000-0000-000000000005', 'RES-1005', 'd1000000-0000-0000-0000-000000000005',
  'CSV export keeps failing at 80%', 'technical', 'medium', 'open', 'neutral', true, now() - interval '1 hour');

insert into emails (ticket_id, direction, from_address, to_address, subject, body_text, received_at) values
  ('e1000000-0000-0000-0000-000000000005', 'inbound', 'liu.wei@demo.resolveai.dev', 'support@resolveai.dev',
   'CSV export keeps failing at 80%',
   'I''m trying to export our full contact list (around 42,000 rows) to CSV and the export progress bar gets to about 80% and then just shows "Export failed". I''ve tried 4 times over the last hour, including a smaller filtered export of 2,000 rows which also failed once. Not sure if this is a size issue.',
   now() - interval '1 hour');

-- Note: agent_runs / agent_actions / ai_analyses / responses for these demo
-- tickets are generated at request time by the backend's demo orchestrator
-- (see backend/app/services/demo_data.py) so the timeline always reflects
-- the current agent logic. This keeps seed.sql focused on the stable
-- ticket/customer/email fixtures. Run the backend once against this
-- Supabase project with DEMO_MODE=true and POST /api/demo/seed-runs to
-- materialize a full agent_runs/agent_actions trail for these 5 tickets.
