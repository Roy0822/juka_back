-- Update existing campaigns with appropriate categories based on keywords in title or description

-- Update coffee-related campaigns
UPDATE campaigns 
SET category = '咖啡優惠'
WHERE 
  (LOWER(title) LIKE '%咖啡%' OR 
   LOWER(description) LIKE '%咖啡%' OR 
   LOWER(title) LIKE '%coffee%' OR 
   LOWER(description) LIKE '%coffee%') AND 
  category = '其他';

-- Update food-related campaigns
UPDATE campaigns 
SET category = '美食優惠'
WHERE 
  (LOWER(title) LIKE '%美食%' OR 
   LOWER(description) LIKE '%美食%' OR 
   LOWER(title) LIKE '%餐廳%' OR 
   LOWER(description) LIKE '%餐廳%' OR 
   LOWER(title) LIKE '%吃%' OR 
   LOWER(description) LIKE '%吃%' OR 
   LOWER(title) LIKE '%food%' OR 
   LOWER(description) LIKE '%food%' OR 
   LOWER(title) LIKE '%restaurant%' OR 
   LOWER(description) LIKE '%restaurant%') AND 
  category = '其他';

-- Update ride-sharing campaigns
UPDATE campaigns 
SET category = '共乘'
WHERE 
  (LOWER(title) LIKE '%共乘%' OR 
   LOWER(description) LIKE '%共乘%' OR 
   LOWER(title) LIKE '%搭車%' OR 
   LOWER(description) LIKE '%搭車%' OR 
   LOWER(title) LIKE '%ride%' OR 
   LOWER(description) LIKE '%ride%' OR 
   LOWER(title) LIKE '%carpool%' OR 
   LOWER(description) LIKE '%carpool%') AND 
  category = '其他';

-- Update shopping campaigns
UPDATE campaigns 
SET category = '購物優惠'
WHERE 
  (LOWER(title) LIKE '%購物%' OR 
   LOWER(description) LIKE '%購物%' OR 
   LOWER(title) LIKE '%商場%' OR 
   LOWER(description) LIKE '%商場%' OR 
   LOWER(title) LIKE '%打折%' OR 
   LOWER(description) LIKE '%打折%' OR 
   LOWER(title) LIKE '%discount%' OR 
   LOWER(description) LIKE '%discount%' OR 
   LOWER(title) LIKE '%shopping%' OR 
   LOWER(description) LIKE '%shopping%') AND 
  category = '其他';

-- Update entertainment campaigns
UPDATE campaigns 
SET category = '娛樂'
WHERE 
  (LOWER(title) LIKE '%娛樂%' OR 
   LOWER(description) LIKE '%娛樂%' OR 
   LOWER(title) LIKE '%電影%' OR 
   LOWER(description) LIKE '%電影%' OR 
   LOWER(title) LIKE '%電競%' OR 
   LOWER(description) LIKE '%電競%' OR 
   LOWER(title) LIKE '%遊戲%' OR 
   LOWER(description) LIKE '%遊戲%' OR 
   LOWER(title) LIKE '%movie%' OR 
   LOWER(description) LIKE '%movie%' OR 
   LOWER(title) LIKE '%game%' OR 
   LOWER(description) LIKE '%game%' OR 
   LOWER(title) LIKE '%entertainment%' OR 
   LOWER(description) LIKE '%entertainment%') AND 
  category = '其他';

-- Count the updated campaigns in each category
SELECT category, COUNT(*) FROM campaigns GROUP BY category; 