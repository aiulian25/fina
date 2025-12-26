-- Migration: Add Budget Alert Support
-- Created: 2024
-- Description: Adds budget tracking and email alert functionality to categories and users

-- Add budget fields to Category table
ALTER TABLE category ADD COLUMN IF NOT EXISTS monthly_budget REAL;
ALTER TABLE category ADD COLUMN IF NOT EXISTS budget_alert_sent BOOLEAN DEFAULT FALSE;
ALTER TABLE category ADD COLUMN IF NOT EXISTS budget_alert_threshold INTEGER DEFAULT 100;
ALTER TABLE category ADD COLUMN IF NOT EXISTS last_budget_check DATE;

-- Add budget alert preferences to User table
ALTER TABLE user ADD COLUMN IF NOT EXISTS budget_alerts_enabled BOOLEAN DEFAULT TRUE;
ALTER TABLE user ADD COLUMN IF NOT EXISTS alert_email VARCHAR(120);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_category_budget_check ON category(monthly_budget, budget_alert_sent);
CREATE INDEX IF NOT EXISTS idx_user_budget_alerts ON user(budget_alerts_enabled);

-- Add comments
COMMENT ON COLUMN category.monthly_budget IS 'Monthly spending limit for this category in default currency';
COMMENT ON COLUMN category.budget_alert_sent IS 'Flag to track if alert was sent this month (resets monthly)';
COMMENT ON COLUMN category.budget_alert_threshold IS 'Percentage (50-200) at which to send alert';
COMMENT ON COLUMN category.last_budget_check IS 'Last date budget was checked (for monthly reset)';
COMMENT ON COLUMN user.budget_alerts_enabled IS 'Global toggle for receiving budget alert emails';
COMMENT ON COLUMN user.alert_email IS 'Optional separate email for budget alerts (defaults to user email)';
