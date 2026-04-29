-- Run this once in Supabase SQL editor

create table if not exists listings (
  id           text primary key,          -- sha256 hash of car identity
  make         text not null,
  model        text not null,
  variant      text,
  year         int,
  kms          int,
  fuel         text,
  transmission text,
  color        text,
  location     text,
  price        int,                        -- lowest price seen across sources (INR)
  image_url    text,
  sources      jsonb default '{}',         -- {"cars24": {"url":"...", "price": 4200000}, ...}
  first_seen   date default current_date,
  is_active    boolean default true
);

-- Index for fast UI queries
create index if not exists idx_listings_active on listings(is_active, first_seen desc);
