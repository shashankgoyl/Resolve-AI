-- ============================================================================
-- Resolve AI — Support Knowledge Agent
-- Supabase / Postgres schema
-- Run this in the Supabase SQL editor, or:  supabase db push
-- ============================================================================

create extension if not exists "uuid-ossp";
create extension if not exists "pgcrypto";

-- ----------------------------------------------------------------------------
-- ENUM TYPES
-- ----------------------------------------------------------------------------
do $$ begin
  create type ticket_priority as enum ('low', 'medium', 'high', 'urgent');
exception when duplicate_object then null; end $$;

do $$ begin
  create type ticket_status as enum ('open', 'in_progress', 'resolved', 'escalated', 'closed');
exception when duplicate_object then null; end $$;

do $$ begin
  create type sentiment_type as enum ('positive', 'neutral', 'negative', 'frustrated');
exception when duplicate_object then null; end $$;

do $$ begin
  create type ai_decision as enum ('RESOLVED', 'NEEDS_ENGINEERING', 'NEEDS_HUMAN_REVIEW', 'INSUFFICIENT_INFORMATION');
exception when duplicate_object then null; end $$;

do $$ begin
  create type response_status as enum ('draft', 'pending_approval', 'approved', 'sent', 'rejected');
exception when duplicate_object then null; end $$;

do $$ begin
  create type agent_run_status as enum ('running', 'completed', 'failed', 'awaiting_approval');
exception when duplicate_object then null; end $$;

do $$ begin
  create type integration_provider as enum ('gmail', 'notion', 'jira', 'github', 'resend', 'swytchcode');
exception when duplicate_object then null; end $$;

do $$ begin
  create type integration_health as enum ('connected', 'degraded', 'disconnected', 'demo');
exception when duplicate_object then null; end $$;

-- ----------------------------------------------------------------------------
-- users  (internal support agents / reviewers)
-- ----------------------------------------------------------------------------
create table if not exists users (
  id uuid primary key default gen_random_uuid(),
  auth_user_id uuid references auth.users(id) on delete set null,
  full_name text not null,
  email text not null unique,
  role text not null default 'agent' check (role in ('admin', 'agent', 'engineer', 'viewer')),
  avatar_url text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- ----------------------------------------------------------------------------
-- customers
-- ----------------------------------------------------------------------------
create table if not exists customers (
  id uuid primary key default gen_random_uuid(),
  email text not null unique,
  full_name text,
  company text,
  plan text default 'free',
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- ----------------------------------------------------------------------------
-- support_tickets
-- ----------------------------------------------------------------------------
create table if not exists support_tickets (
  id uuid primary key default gen_random_uuid(),
  ticket_number text not null unique,
  customer_id uuid not null references customers(id) on delete cascade,
  subject text not null,
  category text,
  priority ticket_priority not null default 'medium',
  status ticket_status not null default 'open',
  sentiment sentiment_type,
  assigned_to uuid references users(id) on delete set null,
  is_demo boolean not null default false,
  resolved_at timestamptz,
  first_response_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_tickets_status on support_tickets(status);
create index if not exists idx_tickets_priority on support_tickets(priority);
create index if not exists idx_tickets_customer on support_tickets(customer_id);
create index if not exists idx_tickets_created on support_tickets(created_at desc);

-- ----------------------------------------------------------------------------
-- emails  (raw inbound/outbound email content, sourced via Gmail through Swytchcode)
-- ----------------------------------------------------------------------------
create table if not exists emails (
  id uuid primary key default gen_random_uuid(),
  ticket_id uuid not null references support_tickets(id) on delete cascade,
  gmail_message_id text,
  gmail_thread_id text,
  direction text not null check (direction in ('inbound', 'outbound')),
  from_address text not null,
  to_address text not null,
  subject text,
  body_text text not null,
  body_html text,
  received_at timestamptz not null default now(),
  created_at timestamptz not null default now()
);

create index if not exists idx_emails_ticket on emails(ticket_id);

-- ----------------------------------------------------------------------------
-- ai_analyses  (Gemini classification output per ticket/email)
-- ----------------------------------------------------------------------------
create table if not exists ai_analyses (
  id uuid primary key default gen_random_uuid(),
  ticket_id uuid not null references support_tickets(id) on delete cascade,
  agent_run_id uuid,
  category text not null,
  priority ticket_priority not null,
  sentiment sentiment_type not null,
  summary text not null,
  key_entities jsonb not null default '[]'::jsonb,
  intent text,
  confidence_score numeric(4,3) not null default 0 check (confidence_score >= 0 and confidence_score <= 1),
  raw_model_output jsonb,
  model text not null default 'gemini-2.0-flash',
  created_at timestamptz not null default now()
);

create index if not exists idx_analyses_ticket on ai_analyses(ticket_id);

-- ----------------------------------------------------------------------------
-- knowledge_sources  (Notion pages retrieved as evidence)
-- ----------------------------------------------------------------------------
create table if not exists knowledge_sources (
  id uuid primary key default gen_random_uuid(),
  ticket_id uuid not null references support_tickets(id) on delete cascade,
  agent_run_id uuid,
  source_type text not null default 'notion',
  notion_page_id text,
  title text not null,
  excerpt text,
  url text,
  relevance_score numeric(4,3) default 0,
  created_at timestamptz not null default now()
);

create index if not exists idx_knowledge_ticket on knowledge_sources(ticket_id);

-- ----------------------------------------------------------------------------
-- engineering_issues  (Jira tickets / GitHub issues, found or created)
-- ----------------------------------------------------------------------------
create table if not exists engineering_issues (
  id uuid primary key default gen_random_uuid(),
  ticket_id uuid not null references support_tickets(id) on delete cascade,
  agent_run_id uuid,
  provider text not null check (provider in ('jira', 'github')),
  external_id text,
  external_key text,
  url text,
  title text not null,
  status text,
  relation text not null default 'related' check (relation in ('related', 'created')),
  relevance_score numeric(4,3) default 0,
  created_at timestamptz not null default now()
);

create index if not exists idx_eng_issues_ticket on engineering_issues(ticket_id);

-- ----------------------------------------------------------------------------
-- responses  (generated customer replies + approval workflow)
-- ----------------------------------------------------------------------------
create table if not exists responses (
  id uuid primary key default gen_random_uuid(),
  ticket_id uuid not null references support_tickets(id) on delete cascade,
  agent_run_id uuid,
  body_text text not null,
  body_html text,
  status response_status not null default 'draft',
  confidence_score numeric(4,3) not null default 0,
  decision ai_decision not null default 'NEEDS_HUMAN_REVIEW',
  reviewed_by uuid references users(id) on delete set null,
  reviewed_at timestamptz,
  sent_via_resend_id text,
  sent_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_responses_ticket on responses(ticket_id);
create index if not exists idx_responses_status on responses(status);

-- ----------------------------------------------------------------------------
-- agent_runs  (one row per end-to-end orchestration run of the agent)
-- ----------------------------------------------------------------------------
create table if not exists agent_runs (
  id uuid primary key default gen_random_uuid(),
  ticket_id uuid not null references support_tickets(id) on delete cascade,
  status agent_run_status not null default 'running',
  decision ai_decision,
  confidence_score numeric(4,3),
  started_at timestamptz not null default now(),
  completed_at timestamptz,
  error_message text,
  is_demo boolean not null default false
);

create index if not exists idx_runs_ticket on agent_runs(ticket_id);

-- ----------------------------------------------------------------------------
-- agent_actions  (every discrete step/tool call the agent made — powers the timeline)
-- ----------------------------------------------------------------------------
create table if not exists agent_actions (
  id uuid primary key default gen_random_uuid(),
  agent_run_id uuid not null references agent_runs(id) on delete cascade,
  ticket_id uuid not null references support_tickets(id) on delete cascade,
  step_order int not null,
  action_type text not null,              -- e.g. 'gmail.fetch', 'ai.classify', 'notion.search', 'jira.search', 'github.search', 'ai.decide', 'jira.create', 'resend.send'
  integration integration_provider,
  swytchcode_canonical_id text,           -- e.g. 'notion.search-pages'
  status text not null default 'success' check (status in ('success', 'error', 'skipped', 'pending')),
  summary text,
  input_payload jsonb,
  output_payload jsonb,
  duration_ms int,
  created_at timestamptz not null default now()
);

create index if not exists idx_actions_run on agent_actions(agent_run_id);
create index if not exists idx_actions_ticket on agent_actions(ticket_id);

-- ----------------------------------------------------------------------------
-- audit_logs  (append-only trail of every human + agent action in the system)
-- ----------------------------------------------------------------------------
create table if not exists audit_logs (
  id uuid primary key default gen_random_uuid(),
  ticket_id uuid references support_tickets(id) on delete set null,
  agent_run_id uuid references agent_runs(id) on delete set null,
  actor_type text not null check (actor_type in ('ai_agent', 'human', 'system')),
  actor_id uuid,
  actor_label text,
  event_type text not null,               -- e.g. 'ticket.created', 'response.approved', 'response.sent', 'ticket.escalated'
  description text not null,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_audit_ticket on audit_logs(ticket_id);
create index if not exists idx_audit_created on audit_logs(created_at desc);

-- ----------------------------------------------------------------------------
-- integration_status  (live health/connection state shown on the Integrations page)
-- ----------------------------------------------------------------------------
create table if not exists integration_status (
  id uuid primary key default gen_random_uuid(),
  provider integration_provider not null unique,
  health integration_health not null default 'demo',
  swytchcode_canonical_prefix text,
  last_checked_at timestamptz,
  last_success_at timestamptz,
  last_error text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- ----------------------------------------------------------------------------
-- updated_at trigger helper
-- ----------------------------------------------------------------------------
create or replace function set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

drop trigger if exists trg_users_updated on users;
create trigger trg_users_updated before update on users
  for each row execute function set_updated_at();

drop trigger if exists trg_customers_updated on customers;
create trigger trg_customers_updated before update on customers
  for each row execute function set_updated_at();

drop trigger if exists trg_tickets_updated on support_tickets;
create trigger trg_tickets_updated before update on support_tickets
  for each row execute function set_updated_at();

drop trigger if exists trg_responses_updated on responses;
create trigger trg_responses_updated before update on responses
  for each row execute function set_updated_at();

drop trigger if exists trg_integration_status_updated on integration_status;
create trigger trg_integration_status_updated before update on integration_status
  for each row execute function set_updated_at();

-- ----------------------------------------------------------------------------
-- Row Level Security — service role bypasses RLS; these policies cover
-- authenticated dashboard users if you wire up Supabase Auth on the frontend.
-- ----------------------------------------------------------------------------
alter table users enable row level security;
alter table customers enable row level security;
alter table support_tickets enable row level security;
alter table emails enable row level security;
alter table ai_analyses enable row level security;
alter table knowledge_sources enable row level security;
alter table engineering_issues enable row level security;
alter table responses enable row level security;
alter table agent_runs enable row level security;
alter table agent_actions enable row level security;
alter table audit_logs enable row level security;
alter table integration_status enable row level security;

do $$ begin
  create policy "authenticated read all" on support_tickets for select using (auth.role() = 'authenticated');
exception when duplicate_object then null; end $$;

do $$ begin
  create policy "authenticated read all" on emails for select using (auth.role() = 'authenticated');
exception when duplicate_object then null; end $$;

do $$ begin
  create policy "authenticated read all" on ai_analyses for select using (auth.role() = 'authenticated');
exception when duplicate_object then null; end $$;

do $$ begin
  create policy "authenticated read all" on knowledge_sources for select using (auth.role() = 'authenticated');
exception when duplicate_object then null; end $$;

do $$ begin
  create policy "authenticated read all" on engineering_issues for select using (auth.role() = 'authenticated');
exception when duplicate_object then null; end $$;

do $$ begin
  create policy "authenticated read all" on responses for select using (auth.role() = 'authenticated');
exception when duplicate_object then null; end $$;

do $$ begin
  create policy "authenticated read all" on agent_runs for select using (auth.role() = 'authenticated');
exception when duplicate_object then null; end $$;

do $$ begin
  create policy "authenticated read all" on agent_actions for select using (auth.role() = 'authenticated');
exception when duplicate_object then null; end $$;

do $$ begin
  create policy "authenticated read all" on audit_logs for select using (auth.role() = 'authenticated');
exception when duplicate_object then null; end $$;

do $$ begin
  create policy "authenticated read all" on integration_status for select using (auth.role() = 'authenticated');
exception when duplicate_object then null; end $$;

do $$ begin
  create policy "authenticated read all" on customers for select using (auth.role() = 'authenticated');
exception when duplicate_object then null; end $$;

do $$ begin
  create policy "authenticated read all" on users for select using (auth.role() = 'authenticated');
exception when duplicate_object then null; end $$;

-- All writes go through the backend using the service-role key, which
-- bypasses RLS by design — the frontend never talks to Supabase directly
-- for writes.

-- ----------------------------------------------------------------------------
-- Seed: integration_status starting rows (all begin in demo mode)
-- ----------------------------------------------------------------------------
insert into integration_status (provider, health, swytchcode_canonical_prefix)
values
  ('gmail', 'demo', 'gmail'),
  ('notion', 'demo', 'notion'),
  ('jira', 'demo', 'jira'),
  ('github', 'demo', 'github'),
  ('resend', 'demo', 'resend'),
  ('swytchcode', 'demo', null)
on conflict (provider) do nothing;
