#!/usr/bin/env python3
"""
Test script for campaign categories
"""
import sys
from app.models.campaign import CampaignCategory
from app.schemas.campaign import CampaignCategory as SchemaCampaignCategory

def test_campaign_categories():
    """Test that campaign categories match in model and schema"""
    
    # Print all categories from the model
    print("Model campaign categories:")
    for category in CampaignCategory:
        print(f" - {category.name}: {category.value}")
    
    # Print all categories from the schema
    print("\nSchema campaign categories:")
    for category in SchemaCampaignCategory:
        print(f" - {category.name}: {category.value}")
    
    # Verify that all categories match
    model_categories = {cat.name: cat.value for cat in CampaignCategory}
    schema_categories = {cat.name: cat.value for cat in SchemaCampaignCategory}
    
    if model_categories == schema_categories:
        print("\n✅ Model and schema categories match!")
    else:
        print("\n❌ Model and schema categories do not match!")
        print(f"Model: {model_categories}")
        print(f"Schema: {schema_categories}")
        sys.exit(1)
    
    # Test using the category values
    print("\nCategory values test:")
    print(f"咖啡優惠: {CampaignCategory.COFFEE}")
    print(f"美食優惠: {CampaignCategory.FOOD}")
    print(f"共乘: {CampaignCategory.RIDE_SHARING}")
    print(f"購物優惠: {CampaignCategory.SHOPPING}")
    print(f"娛樂: {CampaignCategory.ENTERTAINMENT}")
    print(f"其他: {CampaignCategory.OTHER}")

if __name__ == "__main__":
    test_campaign_categories() 