-- First, create the enum type
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'campaigncategory') THEN
        CREATE TYPE campaigncategory AS ENUM (
            '咖啡優惠', 
            '美食優惠', 
            '共乘', 
            '購物優惠', 
            '娛樂', 
            '其他'
        );
    END IF;
END $$;

-- Then, add the category column with a default value
ALTER TABLE campaigns
ADD COLUMN IF NOT EXISTS category campaigncategory NOT NULL DEFAULT '其他';

-- Display the updated table structure
\d campaigns;

-- Query to check the new column
SELECT id, title, category FROM campaigns LIMIT 10; 